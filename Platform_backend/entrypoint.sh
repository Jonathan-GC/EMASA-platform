#!/bin/bash
set -e

echo "🚀 Ejecutando migraciones..."
python manage.py migrate

echo "📦 Cargando fixtures..."
for fixture in $(ls fixtures/*.json | sort); do
  echo "   -> $fixture"
  python manage.py loaddata "$fixture"
done

echo "✅ Fixtures cargadas correctamente."

# Ejecuta el comando final (por defecto el runserver)
exec "$@"
