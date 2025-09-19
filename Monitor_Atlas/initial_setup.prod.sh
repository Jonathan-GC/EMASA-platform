#!/bin/bash
set -e

echo "🚀 Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "📦 Loading fixtures..."
for fixture in $(ls fixtures.prod/*.json | sort); do
    echo "   -> $fixture"
    python manage.py loaddata "$fixture"
done

echo "✅ Fixtures loaded successfully."

echo "🔑 Loading initial model keys..."

python manage.py regenerate_permissionkeys

echo "✅ Initial model keys loaded successfully."

echo "🔄 Synchronizing data with ChirpStack..."

python manage.py sync_chirpstack

# Execute the final command (by default runserver)
exec "$@"