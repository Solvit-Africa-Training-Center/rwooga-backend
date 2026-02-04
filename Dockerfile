FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create staticfiles directory
RUN mkdir -p staticfiles

EXPOSE 8000

# Run collectstatic at startup, then start gunicorn
CMD python manage.py collectstatic --noinput && \
    gunicorn --bind 0.0.0.0:$PORT --workers=2 --threads=2 --timeout=60 --access-logfile - --error-logfile - rwoogaBackend.wsgi:application