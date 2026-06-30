"""
Management command: bitta video faylni HLS formatga (360p/720p/1080p) aylantiradi.

Ishlatish:
    python manage.py transcode_movie <movie_slug> <input_video_path> [--language=uz]

Misol:
    python manage.py transcode_movie avatar-1 /app/media/videos/film2.mp4 --language=uz
"""
import os
import subprocess
import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from movies.models import Movie, MovieFile, Language

logger = logging.getLogger(__name__)


# Sifat darajalari: (nomi, kenglik, balandlik, video bitrate, audio bitrate)
QUALITY_PRESETS = [
    ("360p",  640,  360,  "800k",  "96k"),
    ("720p",  1280, 720,  "2800k", "128k"),
    ("1080p", 1920, 1080, "5000k", "192k"),
]


class Command(BaseCommand):
    help = "Video faylni HLS formatga (ko'p sifatli) aylantiradi"

    def add_arguments(self, parser):
        parser.add_argument("movie_slug", type=str, help="Film slug (masalan: avatar-1)")
        parser.add_argument("input_path", type=str, help="Original video fayl yo'li")
        parser.add_argument("--language", type=str, default="uz", help="Til kodi (uz, ru, en)")
        parser.add_argument(
            "--qualities", type=str, default="360p,720p,1080p",
            help="Vergul bilan ajratilgan sifatlar (masalan: 360p,720p)"
        )

    def handle(self, *args, **options):
        movie_slug = options["movie_slug"]
        input_path = options["input_path"]
        lang_code = options["language"]
        requested_qualities = options["qualities"].split(",")

        # Filmni topish
        try:
            movie = Movie.objects.get(slug=movie_slug)
        except Movie.DoesNotExist:
            raise CommandError(f"Film topilmadi: {movie_slug}")

        # Tilni topish
        try:
            language = Language.objects.get(code=lang_code)
        except Language.DoesNotExist:
            raise CommandError(f"Til topilmadi: {lang_code}. Avval Language qo'shing.")

        # Input fayl mavjudligini tekshirish
        if not os.path.exists(input_path):
            raise CommandError(f"Fayl topilmadi: {input_path}")

        self.stdout.write(self.style.NOTICE(f"Boshlanmoqda: {movie.title} ({lang_code})"))

        # Chiqish papkasi: media/hls/<slug>/<lang>/
        output_base = Path(settings.MEDIA_ROOT) / "hls" / movie_slug / lang_code
        output_base.mkdir(parents=True, exist_ok=True)

        variant_playlists = []

        for quality_name, width, height, v_bitrate, a_bitrate in QUALITY_PRESETS:
            if quality_name not in requested_qualities:
                continue

            self.stdout.write(f"  → {quality_name} transcoding...")

            quality_dir = output_base / quality_name
            quality_dir.mkdir(exist_ok=True)

            playlist_path = quality_dir / "playlist.m3u8"
            segment_pattern = quality_dir / "segment_%03d.ts"

            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-vf", f"scale=w={width}:h={height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-b:v", v_bitrate,
                "-maxrate", v_bitrate,
                "-bufsize", str(int(v_bitrate.replace("k", "")) * 2) + "k",
                "-c:a", "aac",
                "-b:a", a_bitrate,
                "-hls_time", "6",
                "-hls_playlist_type", "vod",
                "-hls_segment_filename", str(segment_pattern),
                str(playlist_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                self.stdout.write(self.style.ERROR(f"  ✗ {quality_name} xato:"))
                self.stdout.write(result.stderr[-2000:])
                continue

            self.stdout.write(self.style.SUCCESS(f"  ✓ {quality_name} tayyor"))

            # Fayl o'lchami
            file_size = sum(f.stat().st_size for f in quality_dir.glob("*") if f.is_file())

            # MovieFile yaratish/yangilash
            relative_playlist = f"hls/{movie_slug}/{lang_code}/{quality_name}/playlist.m3u8"

            movie_file, created = MovieFile.objects.update_or_create(
                movie=movie,
                quality=quality_name,
                language=language,
                defaults={
                    "file_key": relative_playlist,
                    "hls_playlist_key": relative_playlist,
                    "status": MovieFile.Status.READY,
                    "file_size_bytes": file_size,
                },
            )

            bandwidth = int(v_bitrate.replace("k", "")) * 1000 + int(a_bitrate.replace("k", "")) * 1000
            variant_playlists.append({
                "quality": quality_name,
                "width": width,
                "height": height,
                "bandwidth": bandwidth,
                "path": f"{quality_name}/playlist.m3u8",
            })

        # Master playlist yaratish (barcha sifatlarni birlashtiruvchi)
        if variant_playlists:
            master_path = output_base / "master.m3u8"
            with open(master_path, "w") as f:
                f.write("#EXTM3U\n#EXT-X-VERSION:3\n")
                for v in variant_playlists:
                    f.write(
                        f'#EXT-X-STREAM-INF:BANDWIDTH={v["bandwidth"]},RESOLUTION={v["width"]}x{v["height"]}\n'
                    )
                    f.write(f'{v["path"]}\n')

            self.stdout.write(self.style.SUCCESS(f"\nMaster playlist yaratildi: {master_path}"))
            self.stdout.write(self.style.SUCCESS(
                f"Jami {len(variant_playlists)} ta sifat darajasi tayyor: "
                f"{', '.join(v['quality'] for v in variant_playlists)}"
            ))
        else:
            self.stdout.write(self.style.ERROR("Hech qanday sifat transcoding qilinmadi!"))