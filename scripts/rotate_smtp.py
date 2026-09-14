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

if 'EMAIL_HOST_PASSWORD' not in data:
    print('EMAIL_HOST_PASSWORD not found in secrets/.env.generated')
    raise SystemExit(1)

out = root / '.env.smtp'
out.write_text(f"EMAIL_HOST_PASSWORD={data['EMAIL_HOST_PASSWORD']}\n")
print('Wrote .env.smtp — use this to update CI/deployment secrets (do NOT commit).')
print('\nNext steps:')
print('1) Update your production/CI secret EMAIL_HOST_PASSWORD with the value in .env.smtp')
print('2) Restart web app service to pick up new email credentials:')
print('   docker-compose restart web')
print('3) Send a test email from the app or Django shell:')
print("   python manage.py shell -c \"from django.core.mail import send_mail; send_mail('Test','Body','from@example.com',['to@example.com'],fail_silently=False)\"")
print('4) Revoke old SMTP credentials at provider panel if possible.')
