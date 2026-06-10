import boto3
import sys
from botocore.config import Config

def upload_video(file_path: str, movie_id: str, quality: str = "720p"):
    """
    Video faylni MinIO ga yuklash.
    
    Ishlatish:
    python scripts/upload_video.py video.mp4 movie-uuid-here 720p
    """
    client = boto3.client(
        "s3",
        endpoint_url="http://161.33.30.28:9000",
        aws_access_key_id="minio",
        aws_secret_access_key="minio123",
        config=Config(signature_version="s3v4"),
        verify=False,
    )

    bucket = "cinema"
    file_key = f"videos/{movie_id}/original_{quality}.mp4"

    print(f"Yuklanmoqda: {file_path} → {bucket}/{file_key}")

    with open(file_path, "rb") as f:
        client.upload_fileobj(
            f,
            bucket,
            file_key,
            ExtraArgs={"ContentType": "video/mp4"},
            Callback=lambda bytes_transferred: print(
                f"\r{bytes_transferred / 1024 / 1024:.1f} MB yuklandi",
                end="",
            ),
        )

    print(f"\n✅ Yuklandi: {file_key}")
    return file_key

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Ishlatish: python scripts/upload_video.py <video_fayl> <movie_id> [quality]")
        sys.exit(1)

    file_path = sys.argv[1]
    movie_id  = sys.argv[2]
    quality   = sys.argv[3] if len(sys.argv) > 3 else "720p"

    upload_video(file_path, movie_id, quality)