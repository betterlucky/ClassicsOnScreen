#!/bin/bash

# Start Nginx
echo "Starting Nginx..."
nginx -c /etc/nginx/nginx.conf

# Create database directory if it doesn't exist
echo "Setting up database..."
sudo mkdir -p /app/db
sudo chown -R appuser:appuser /app/db
sudo chmod -R 777 /app/db

# Function to check if required tables exist
check_tables() {
    echo "Checking if required tables exist..."
    python << END
import sqlite3
try:
    conn = sqlite3.connect('/app/db/db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blog_siteuser'")
    exists = cursor.fetchone() is not None
    conn.close()
    exit(0 if exists else 1)
except:
    exit(1)
END
}

# Reset database if it doesn't exist, if RESET_DB is true, or if required tables are missing
if [ ! -f /app/db/db.sqlite3 ] || [ "$RESET_DB" = "true" ] || ! check_tables; then
    echo "Creating fresh database..."
    if [ -f /app/db/db.sqlite3 ]; then
        echo "Removing existing database..."
        sudo rm /app/db/db.sqlite3
    fi
    
    echo "Creating new database file..."
    sudo touch /app/db/db.sqlite3
    sudo chown appuser:appuser /app/db/db.sqlite3
    sudo chmod 666 /app/db/db.sqlite3

    # Create migrations directory if it doesn't exist
    echo "Setting up migrations directory..."
    sudo mkdir -p blog/migrations
    sudo chown -R appuser:appuser blog/migrations
    sudo chmod -R 777 blog/migrations

    # Remove any existing migrations
    echo "Cleaning up old migrations..."
    sudo rm -f blog/migrations/0*.py
    sudo rm -f blog/migrations/*.pyc

    # Make and apply migrations in correct order
    echo "Creating migrations..."
    python manage.py makemigrations blog

    # Temporarily disable the post_migrate signal
    echo "Applying migrations with post_migrate signal disabled..."
    DJANGO_DISABLE_POST_MIGRATE=true python manage.py migrate contenttypes
    DJANGO_DISABLE_POST_MIGRATE=true python manage.py migrate auth
    DJANGO_DISABLE_POST_MIGRATE=true python manage.py migrate blog
    DJANGO_DISABLE_POST_MIGRATE=true python manage.py migrate admin
    DJANGO_DISABLE_POST_MIGRATE=true python manage.py migrate sessions
    DJANGO_DISABLE_POST_MIGRATE=true python manage.py migrate sites

    # Now create the superuser after all tables exist
    echo "Creating superuser..."
    python manage.py create_superuser || true

    # Create test data
    echo "Creating test data..."
    python manage.py setup_test_data || true
else
    echo "Using existing database..."
    # Just run migrations in case there are any pending
    python manage.py migrate
fi

echo "Database directory permissions:"
ls -la /app/db

# Collect static files
echo "Collecting static..."
python manage.py collectstatic --no-input

echo "Static files directory contents:"
ls -la /app/staticfiles
ls -la /app/staticfiles/img

echo "Setting proper permissions for static files..."
sudo chown -R appuser:appuser /app/staticfiles
chmod -R 755 /app/staticfiles

# Start Gunicorn
echo "Starting Gunicorn server..."
gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 wsgi:application
