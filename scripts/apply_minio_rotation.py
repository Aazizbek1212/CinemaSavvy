#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).parent.parent
secrets_file = root / 'secrets' / '.env.generated'
output_file = root / '.env'

if not secrets_file.exists():
    print('secrets/.env.generated not found. Run scripts/generate_env.py first.')
    raise SystemExit(1)

# Read generated secrets
data = {}
for line in secrets_file.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    if '=' in line:
        k, v = line.split('=', 1)
        data[k.strip()] = v.strip()

# Map keys for app and docker-compose
env_lines = []
# Keep existing important defaults if present (could be extended)
# Map MINIO root user/password to both MINIO_ROOT_* (for server) and MINIO_ACCESS_KEY/MINIO_SECRET_KEY (for app)
if 'MINIO_ROOT_USER' in data:
    env_lines.append(f"MINIO_ROOT_USER={data['MINIO_ROOT_USER']}")
    env_lines.append(f"MINIO_ACCESS_KEY={data['MINIO_ROOT_USER']}")
if 'MINIO_ROOT_PASSWORD' in data:
    env_lines.append(f"MINIO_ROOT_PASSWORD={data['MINIO_ROOT_PASSWORD']}")
    env_lines.append(f"MINIO_SECRET_KEY={data['MINIO_ROOT_PASSWORD']}")

# Postgres
if 'POSTGRES_PASSWORD' in data:
    env_lines.append(f"POSTGRES_PASSWORD={data['POSTGRES_PASSWORD']}")

# Django secret
if 'SECRET_KEY' in data:
    env_lines.append(f"SECRET_KEY={data['SECRET_KEY']}")

# Email
if 'EMAIL_HOST_PASSWORD' in data:
    env_lines.append(f"EMAIL_HOST_PASSWORD={data['EMAIL_HOST_PASSWORD']}")

# Endpoint
# Keep MINIO endpoint default to http://minio:9000 for docker-compose
env_lines.append('MINIO_ENDPOINT=http://minio:9000')

output_file.write_text('\n'.join(env_lines) + '\n')
print('Wrote .env with mapped MinIO and DB values at', output_file)
print('DO NOT COMMIT .env; it is ignored by .gitignore')
