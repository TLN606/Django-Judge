#!/bin/sh
set -e

echo "Applying migrations..."
python manage.py migrate --noinput

if [ "${SEED_DEMO:-0}" = "1" ]; then
    echo "Seeding demo data..."
    python manage.py seed_demo
fi

exec "$@"
