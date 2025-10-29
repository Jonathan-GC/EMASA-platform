#!/bin/bash

# Script para cargar fixtures iniciales de desarrollo
# Útil para probar permisos y roles manualmente

set -e  # Salir si hay algún error

echo "🔄 Limpiando base de datos..."
python manage.py flush --no-input

echo ""
echo "📦 Aplicando migraciones (shared apps primero)..."
python manage.py migrate_schemas --shared

echo ""
echo "📥 Cargando fixtures de SHARED APPS..."

echo "  ├─ Suscripciones..."
python manage.py loaddata fixtures/002_subscription.json

echo "  ├─ Tenants..."
python manage.py loaddata fixtures/003_tenant.json

echo "  ├─ Dominios..."
python manage.py loaddata fixtures/003_domains.json

echo ""
echo "📦 Aplicando migraciones a schemas de tenants..."
python manage.py migrate_schemas

echo ""
echo "📥 Continuando con fixtures compartidas..."

echo "  ├─ Grupos..."
python manage.py loaddata fixtures/000_groups.json

echo "  ├─ Superusuario..."
python manage.py loaddata fixtures/001_superuser.json

echo "  ├─ Workspaces..."
python manage.py loaddata fixtures/004_workspace.json

echo "  ├─ Roles..."
python manage.py loaddata fixtures/005_role.json

echo "  └─ Usuarios y Memberships..."
python manage.py loaddata fixtures/006_users.json

echo ""
echo "✅ Fixtures iniciales cargadas exitosamente!"
echo ""
echo "📊 Resumen de datos cargados:"
echo "  • Superusuario: weedo (password: estrellita123)"
echo "  • Tenants: EMASA (super_tenant), Tecnobot"
echo "  • Usuarios EMASA: emasa_admin, emasa_employee"
echo "  • Usuarios Tecnobot: tec_admin, tec_employee"
echo ""
echo "🔑 Para iniciar sesión:"
echo "  Username: weedo (superuser)"
echo "  Username: emasa_admin (admin EMASA)"
echo "  Username: tec_admin (admin Tecnobot)"
echo "  Password: estrellita123 (para todos)"
echo ""
echo "🚀 Servidor listo para pruebas. Ejecuta:"
echo "   python manage.py runserver"
