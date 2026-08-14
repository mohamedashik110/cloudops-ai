FROM python:3.14-slim

WORKDIR /app

# System dependencies for psycopg2 and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Collect static files (for admin panel CSS/JS)
RUN python manage.py collectstatic --noinput || true

# Create a non-root user and switch to it (security best practice)
RUN useradd --create-home appuser
USER appuser

EXPOSE 8080

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080"]
