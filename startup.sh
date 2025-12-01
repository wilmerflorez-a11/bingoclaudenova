#!/bin/bash

echo "=========================================="
echo "Iniciando Bingo Multicanal"
echo "=========================================="

# Instalar dependencias (por si acaso)
echo "📦 Instalando dependencias..."
pip install -r requirements.txt --quiet

# Verificar estructura de carpetas estáticas
echo "📁 Verificando archivos estáticos..."
if [ -d "editor/static/imagenes" ]; then
    echo "✅ Carpeta de imágenes encontrada"
    ls -la editor/static/imagenes/ || echo "⚠️  No se puede listar el contenido"
else
    echo "❌ Carpeta editor/static/imagenes no existe"
fi

# Colectar archivos estáticos
echo "🎨 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear --verbosity 2

# Verificar que se copiaron los archivos
echo "📊 Archivos estáticos copiados:"
if [ -d "staticfiles/imagenes" ]; then
    ls -la staticfiles/imagenes/ || echo "Sin imágenes en staticfiles"
else
    echo "⚠️  No se encontró carpeta staticfiles/imagenes"
fi

# Ejecutar migraciones
echo "🗄️  Ejecutando migraciones de base de datos..."
python manage.py migrate --noinput

# Crear superusuario si no existe
echo "👤 Verificando superusuario..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@bingo.com', 'Admin2025!Bingo')
    print('✅ Superusuario creado: admin / Admin2025!Bingo')
else:
    print('✅ Superusuario ya existe')
EOF

echo "=========================================="
echo "🚀 Iniciando aplicación con Daphne..."
echo "=========================================="

# Iniciar Daphne (servidor ASGI para WebSockets)
daphne -b 0.0.0.0 -p 8000 proyecto.asgi:application