#!/bin/sh

echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.5
done
echo "Database is up."

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"
