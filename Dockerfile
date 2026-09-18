FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Tizim bog'liqliklari (ffmpeg video qayta ishlash uchun, psycopg2 uchun)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    gcc \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Tailwind CSS ni build qilib, static/css/main.css ni to'ldiramiz
RUN cd frontend && npm install && npm run build
EXPOSE 8000
ENTRYPOINT ["sh", "scripts/entrypoint.sh"]
