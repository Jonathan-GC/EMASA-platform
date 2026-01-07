FROM python:3.12-slim

# Environment variables
ENV PYTHONWRITEBYTECODE=1 \
    PYTHONBUFFERED=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DJANGO_SETTINGS_MODULE=platform_backend.settings

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Make scripts executable
RUN chmod +x /app/entrypoint.sh /app/initial_setup.sh

# Verify platform_backend module exists
RUN python -c "import sys; sys.path.insert(0, '/app'); import platform_backend; print('✓ platform_backend module found')"

# Expose port
EXPOSE 8000

# Set entrypoint and default command
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
