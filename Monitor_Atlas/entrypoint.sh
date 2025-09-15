#!/bin/bash
set -e

echo "🚀 Running migrations..."
python manage.py migrate --noinput

# Execute the final command (by default runserver)
exec "$@"
