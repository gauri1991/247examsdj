#!/bin/bash
set -e

echo "Starting Django application..."

# Wait for database
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis started"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', '${DJANGO_SUPERUSER_PASSWORD:-changeme}')
    print('Superuser created')
else:
    print('Superuser already exists')
"

# Create cache table
echo "Creating cache table..."
python manage.py createcachetable || true

# Start application
echo "Starting application..."
exec "$@"