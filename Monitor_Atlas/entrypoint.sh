#!/bin/bash
set -e

# Ensure PYTHONPATH is set
export PYTHONPATH=/app:$PYTHONPATH

echo "🚀 Running migrations..."
python manage.py migrate --noinput

# Execute the final command (by default runserver)
exec "$@"
