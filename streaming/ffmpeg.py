import os
import subprocess
import logging
import tempfile
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HLSConversionResult:
    success: bool
    playlist_path: str | None = None
    segment_dir: str | None = None
    duration_seconds: int | None = None
    error: str | None = None


class FFmpegProcessor:
    """
    Converts video to HLS format with multiple quality variants.
    Requires ffmpeg installed in the system.
    """

    QUALITY_SETTINGS = {
        "360p": {
            "resolution": "640x360",
            "video_bitrate": "500k",
            "audio_bitrate": "96k",
            "crf": "28",
        },
        "720p": {
            "resolution": "1280x720",
            "video_bitrate": "2500k",
            "audio_bitrate": "128k",
            "crf": "23",
        },
        "1080p": {
            "resolution": "1920x1080",
            "video_bitrate": "5000k",
            "audio_bitrate": "192k",
            "crf": "20",
        },
        "4k": {
            "resolution": "3840x2160",
            "video_bitrate": "15000k",
            "audio_bitrate": "256k",
            "crf": "18",
        },
    }

    @staticmethod
    def get_video_duration(input_path: str) -> int | None:
        """Get video duration in seconds using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-show_entries", "format=duration",
                    "-of", "csv=p=0",
                    input_path,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return int(float(result.stdout.strip()))
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError) as exc:
            logger.error("ffprobe failed: %s", exc)
        return None

    def convert_to_hls(
        self,
        input_path: str,
        output_dir: str,
        quality: str = "720p",
        segment_duration: int = 6,
    ) -> HLSConversionResult:
        """
        Convert video to HLS with given quality.
        Returns playlist path and segment directory.
        """
        if quality not in self.QUALITY_SETTINGS:
            return HLSConversionResult(
                success=False,
                error=f"Unsupported quality: {quality}",
            )

        settings = self.QUALITY_SETTINGS[quality]
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        playlist_path = str(output_path / "playlist.m3u8")
        segment_pattern = str(output_path / "segment_%03d.ts")

        cmd = [
            "ffmpeg", "-y",  # overwrite output (global flag must come before output)
            "-i", input_path,
            "-vf", f"scale={settings['resolution']}",
            "-c:v", "libx264",
            "-crf", settings["crf"],
            "-maxrate", settings["video_bitrate"],
            "-bufsize", str(int(settings["video_bitrate"][:-1]) * 2) + "k",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", settings["audio_bitrate"],
            "-ac", "2",
            # HLS settings
            "-f", "hls",
            "-hls_time", str(segment_duration),
            "-hls_playlist_type", "vod",
            "-hls_segment_filename", segment_pattern,
            "-hls_flags", "independent_segments",
            playlist_path,
        ]

        logger.info("Starting HLS conversion: %s → %s (%s)", input_path, output_dir, quality)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 soat timeout
            )

            if result.returncode != 0:
                logger.error("FFmpeg error: %s", result.stderr[-500:])
                return HLSConversionResult(
                    success=False,
                    error=result.stderr[-500:],
                )

            duration = self.get_video_duration(input_path)
            logger.info("HLS conversion completed: %s", playlist_path)

            return HLSConversionResult(
                success=True,
                playlist_path=playlist_path,
                segment_dir=str(output_path),
                duration_seconds=duration,
            )

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout for: %s", input_path)
            return HLSConversionResult(success=False, error="FFmpeg timeout")
        except FileNotFoundError:
            logger.error("FFmpeg not found in system PATH")
            return HLSConversionResult(success=False, error="FFmpeg not installed")


ffmpeg_processor = FFmpegProcessor()