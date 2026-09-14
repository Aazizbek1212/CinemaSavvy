#!/usr/bin/env python3
import secrets
import os
from pathlib import Path

out_dir = Path(__file__).parent.parent / 'secrets'
out_dir.mkdir(parents=True, exist_ok=True)
outfile = out_dir / '.env.generated'

def gen_secret(n=50):
    return secrets.token_urlsafe(n)[:n]

content = f"""
# GENERATED ENV - DO NOT COMMIT
SECRET_KEY={gen_secret(50)}
POSTGRES_PASSWORD={gen_secret(24)}
MINIO_ROOT_USER={gen_secret(16)}
MINIO_ROOT_PASSWORD={gen_secret(24)}
EMAIL_HOST_PASSWORD={gen_secret(24)}
""".lstrip()

outfile.write_text(content)
print(f"Wrote generated env to: {outfile}")
print("Please copy these values into your hosting dashboards and update your local .env (do NOT commit .env)")
