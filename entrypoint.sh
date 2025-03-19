#!/bin/bash

# Start Nginx
echo "Starting Nginx..."
nginx -c /etc/nginx/nginx.conf

# Create database directory if it doesn't exist
echo "Setting up database..."
mkdir -p /app/db
sudo chown -R appuser:appuser /app/db
chmod -R 777 /app/db

# Check if database file exists
if [ ! -f /app/db/db.sqlite3 ]; then
    echo "Creating database file..."
    touch /app/db/db.sqlite3
    sudo chown appuser:appuser /app/db/db.sqlite3
    chmod 666 /app/db/db.sqlite3
fi

echo "Database directory permissions:"
ls -la /app/db

# Make and apply migrations
echo "Creating migrations..."
python manage.py makemigrations

echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static..."
python manage.py collectstatic --no-input

echo "Static files directory contents:"
ls -la /app/staticfiles
ls -la /app/staticfiles/img

echo "Setting proper permissions for static files..."
sudo chown -R appuser:appuser /app/staticfiles
chmod -R 755 /app/staticfiles

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py create_superuser || true

# Start Gunicorn
echo "Starting Gunicorn server..."
gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 wsgi:application
