FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# g++ cần cho bộ chấm bài C++ (Online Judge)
RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x docker-entrypoint.sh \
    && SECRET_KEY=build-only python manage.py collectstatic --noinput

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
# Render đặt biến PORT (mặc định 10000); chạy local/Docker Compose dùng 8000
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 60"]
