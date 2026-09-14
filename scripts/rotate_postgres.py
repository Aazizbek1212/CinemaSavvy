#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).parent.parent
secrets_file = root / 'secrets' / '.env.generated'
if not secrets_file.exists():
    print('secrets/.env.generated not found. Run scripts/generate_env.py first.')
    raise SystemExit(1)

data = {}
for line in secrets_file.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    if '=' in line:
        k, v = line.split('=', 1)
        data[k.strip()] = v.strip()

if 'POSTGRES_PASSWORD' not in data:
    print('POSTGRES_PASSWORD not found in secrets/.env.generated')
    raise SystemExit(1)

# Write a .env.postgres file containing only the DB secret for safe manual upload to CI
out = root / '.env.postgres'
out.write_text(f"POSTGRES_PASSWORD={data['POSTGRES_PASSWORD']}\n")
print('Wrote .env.postgres — use this to update CI/deployment secrets (do NOT commit).')
print('\nNext steps:')
print('1) Update your production/CI secret POSTGRES_PASSWORD with the value in .env.postgres')
print('2) Restart Postgres service or the host/DB container:')
print('   docker-compose restart db')
print('3) Verify app connectivity and run smoke migrations:')
print('   python manage.py migrate --check')
print('   python manage.py showmigrations')
print('4) Revoke old DB credentials from hosting panel if applicable.')
