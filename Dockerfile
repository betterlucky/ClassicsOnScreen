# Use an official Python runtime as a parent image
FROM python:3.9

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run database migrations and start server
CMD ["sh", "-c", "python manage.py migrate && gunicorn classicsonscreen.wsgi:application --bind 0.0.0.0:$PORT"]
