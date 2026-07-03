#!/bin/bash

echo "⏳ Migrations apply qilinimoqda..."
python manage.py migrate --noinput

echo "⏳ Static files collecting..."
python manage.py collectstatic --noinput

echo "🚀 Server start qilinimoqda..."
gunicorn cinema.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
