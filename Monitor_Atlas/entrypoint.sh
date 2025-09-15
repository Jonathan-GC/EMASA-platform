#!/bin/bash
set -e

echo "🚀 Running migrations..."
python manage.py migrate

echo "🔄 Syncing data with ChirpStack..."
python manage.py sync_chirpstack

# Execute the final command (by default runserver)
exec "$@"
