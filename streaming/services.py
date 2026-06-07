import os
import logging
import tempfile
from pathlib import Path
from django.utils import timezone

from movies.models import MovieFile
from .models import VideoProcessingJob, WatchHistory
from .storage import minio_storage
from .ffmpeg import ffmpeg_processor

logger = logging.getLogger(__name__)


class VideoStreamingService:
    """
    Handles presigned URL generation for secure video streaming.
    """

    # Presigned URL expires in 2 hours
    STREAM_URL_EXPIRY = 7200

    @staticmethod
    def get_stream_url(movie_file: MovieFile) -> str | None:
        """
        Generate presigned HLS playlist URL.
        Frontend uses this URL with Video.js HLS plugin.
        """
        if movie_file.status != MovieFile.Status.READY:
            logger.warning(
                "Stream URL requested for non-ready file: %s", movie_file.id
            )
            return None

        key = movie_file.hls_playlist_key or movie_file.file_key
        return minio_storage.generate_presigned_url(
            file_key=key,
            expires_in=VideoStreamingService.STREAM_URL_EXPIRY,
        )

    @staticmethod
    def get_best_quality_file(movie, preferred_quality: str | None = None) -> MovieFile | None:
        """
        Returns best available quality file.
        Priority: preferred → 1080p → 720p → 360p
        """
        ready_files = movie.video_files.filter(
            status=MovieFile.Status.READY
        ).order_by("-quality")

        if not ready_files.exists():
            return None

        if preferred_quality:
            file = ready_files.filter(quality=preferred_quality).first()
            if file:
                return file

        # Quality priority fallback
        priority = ["1080p", "720p", "360p", "4k"]
        for quality in priority:
            file = ready_files.filter(quality=quality).first()
            if file:
                return file

        return ready_files.first()


class WatchHistoryService:
    """
    Manages watch progress tracking.
    """

    # Mark as completed if watched >= 90%
    COMPLETION_THRESHOLD = 0.90

    @staticmethod
    def update_progress(
        user,
        movie,
        position_seconds: int,
        duration_seconds: int | None = None,
    ) -> WatchHistory:
        """Update or create watch progress record."""
        history, _ = WatchHistory.objects.update_or_create(
            user=user,
            movie=movie,
            defaults={
                "position_seconds": position_seconds,
                "duration_seconds": duration_seconds,
                "completed": (
                    position_seconds >= duration_seconds * WatchHistoryService.COMPLETION_THRESHOLD
                    if duration_seconds
                    else False
                ),
            },
        )
        return history

    @staticmethod
    def get_resume_position(user, movie) -> int:
        """Returns last watched position in seconds."""
        try:
            history = WatchHistory.objects.get(user=user, movie=movie)
            if history.completed:
                return 0  # Completed — start from beginning
            return history.position_seconds
        except WatchHistory.DoesNotExist:
            return 0


class VideoProcessingService:
    """
    Handles FFmpeg video processing pipeline.
    Upload → Convert → Upload segments → Update status
    """

    @staticmethod
    def process_video(movie_file_id: str) -> bool:
        """
        Full pipeline:
        1. Download original from MinIO
        2. Convert to HLS with FFmpeg
        3. Upload segments back to MinIO
        4. Update MovieFile status
        """
        try:
            movie_file = MovieFile.objects.select_related("movie").get(id=movie_file_id)
        except MovieFile.DoesNotExist:
            logger.error("MovieFile not found: %s", movie_file_id)
            return False

        # Update job status
        job, _ = VideoProcessingJob.objects.get_or_create(movie_file=movie_file)
        job.status = VideoProcessingJob.Status.PROCESSING
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at"])

        movie_file.status = MovieFile.Status.PROCESSING
        movie_file.save(update_fields=["status"])

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input_video")
            output_dir = os.path.join(tmp_dir, "hls_output")

            # Download original video
            logger.info("Downloading original video: %s", movie_file.file_key)
            try:
                minio_storage.client.download_file(
                    Bucket=movie_file.movie.title,
                    Key=movie_file.file_key,
                    Filename=input_path,
                )
            except Exception as exc:
                return VideoProcessingService._fail(job, movie_file, str(exc))

            # Convert to HLS
            result = ffmpeg_processor.convert_to_hls(
                input_path=input_path,
                output_dir=output_dir,
                quality=movie_file.quality,
            )

            if not result.success:
                return VideoProcessingService._fail(job, movie_file, result.error)

            # Upload HLS segments to MinIO
            base_key = f"videos/{movie_file.movie.id}/{movie_file.quality}"
            playlist_key = f"{base_key}/playlist.m3u8"

            for file_path in Path(output_dir).iterdir():
                file_key = f"{base_key}/{file_path.name}"
                content_type = (
                    "application/x-mpegURL"
                    if file_path.suffix == ".m3u8"
                    else "video/mp2t"
                )
                success = minio_storage.upload_file(
                    str(file_path), file_key, content_type
                )
                if not success:
                    return VideoProcessingService._fail(
                        job, movie_file, f"Upload failed: {file_path.name}"
                    )

            # Update MovieFile
            movie_file.hls_playlist_key = playlist_key
            movie_file.status = MovieFile.Status.READY
            movie_file.duration_seconds = result.duration_seconds
            movie_file.save(update_fields=[
                "hls_playlist_key", "status", "duration_seconds"
            ])

            job.status = VideoProcessingJob.Status.COMPLETED
            job.progress_percent = 100
            job.completed_at = timezone.now()
            job.save(update_fields=["status", "progress_percent", "completed_at"])

            logger.info("Video processing completed: %s", movie_file.id)
            return True

    @staticmethod
    def _fail(job: VideoProcessingJob, movie_file: MovieFile, error: str) -> bool:
        logger.error("Video processing failed: %s — %s", movie_file.id, error)
        job.status = VideoProcessingJob.Status.FAILED
        job.error_message = error
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at"])

        movie_file.status = MovieFile.Status.FAILED
        movie_file.processing_error = error
        movie_file.save(update_fields=["status", "processing_error"])
        return False