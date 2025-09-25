#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando build de Dataset Analyzer Backend..."

echo "🔧 Instalando dependencias..."
pip install -r requirements.txt

echo "📁 Creando directorios necesarios..."
mkdir -p staticfiles
mkdir -p media

echo "🧪 Verificando configuración Django..."
python manage.py check

echo "🔄 Ejecutando migraciones..."
python manage.py migrate

echo "🗂️ Recolectando archivos estáticos..."
python manage.py collectstatic --no-input --clear

echo "✅ Build completado exitosamente!"