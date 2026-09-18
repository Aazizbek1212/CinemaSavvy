import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from movies.models import MovieFile


class Command(BaseCommand):
    help = "Upload a video file to Telegram and save its file_id to MovieFile"

    def add_arguments(self, parser):
        parser.add_argument('movie_file_id', type=str, help='MovieFile primary key (UUID)')
        parser.add_argument('file_path', type=str, help='Path to the local video file')

    def handle(self, *args, **options):
        pk = options['movie_file_id']
        file_path = options['file_path']

        try:
            movie_file = MovieFile.objects.get(pk=pk)
        except MovieFile.DoesNotExist:
            raise CommandError(f"MovieFile with id={pk} not found")

        movie_file.status = MovieFile.Status.PROCESSING
        movie_file.save(update_fields=['status'])

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendVideo"

        self.stdout.write(f"Uploading {file_path} to Telegram...")

        try:
            with open(file_path, 'rb') as f:
                response = requests.post(
                    url,
                    data={'chat_id': settings.TELEGRAM_CHANNEL_ID},
                    files={'video': f},
                    timeout=600,
                )
            data = response.json()

            if not data.get('ok'):
                movie_file.status = MovieFile.Status.FAILED
                movie_file.processing_error = str(data)
                movie_file.save(update_fields=['status', 'processing_error'])
                raise CommandError(f"Telegram API error: {data}")

            result = data['result']
            video = result.get('video') or result.get('document')

            movie_file.telegram_file_id = video['file_id']
            movie_file.telegram_message_id = result['message_id']
            movie_file.status = MovieFile.Status.READY
            movie_file.save(update_fields=[
                'telegram_file_id', 'telegram_message_id', 'status'
            ])

            self.stdout.write(self.style.SUCCESS(
                f"Muvaffaqiyatli yuklandi! file_id={video['file_id']}"
            ))

        except CommandError:
            raise
        except Exception as e:
            movie_file.status = MovieFile.Status.FAILED
            movie_file.processing_error = str(e)
            movie_file.save(update_fields=['status', 'processing_error'])
            raise CommandError(f"Yuklashda xatolik: {e}")