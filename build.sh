#!/usr/bin/env bash
set -o errexit

echo "🔧 Instalando dependencias de Python..."
pip install -r requirements.txt

echo "🗂️ Recolectando archivos estáticos..."
python manage.py collectstatic --no-input

echo "🔄 Ejecutando migraciones..."
python manage.py migrate

echo "✅ Build completado!"