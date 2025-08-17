#!/bin/bash
set -e

# Wait for database
echo "Waiting for PostgreSQL..."
until pg_isready -h db -p 5432 -U postgres; do
  echo "Waiting for postgres..."
  sleep 2
done
echo "PostgreSQL started"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Create directories if they don't exist
mkdir -p /app/staticfiles
mkdir -p /app/mediafiles
mkdir -p /app/logs

# Collect static files in production
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.prod" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

# Create superuser if specified
if [ "$DJANGO_CREATE_SUPERUSER" = "true" ]; then
    echo "Creating superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
fi

# Load fixtures if specified
if [ "$DJANGO_LOAD_FIXTURES" = "true" ]; then
    echo "Loading fixtures..."
    python manage.py loaddata fixtures/dev_data.json || echo "No fixtures found or error loading"
fi

# Execute the container's main process
exec "$@"