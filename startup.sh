#!/bin/bash

echo "=========================================="
echo "Iniciando Bingo Multicanal"
echo "=========================================="

# Asegurarse de que tenemos los permisos correctos
chmod +x startup.sh

# Colectar archivos estáticos SIN --clear para evitar borrar archivos
echo "🎨 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Ejecutar migraciones
echo "🗄️  Ejecutando migraciones..."
python manage.py migrate --noinput

# Crear superusuario si no existe
echo "👤 Verificando superusuario..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@bingo.com', 'Admin2025!Bingo')
        print('✅ Superusuario creado')
    else:
        print('✅ Superusuario ya existe')
except Exception as e:
    print(f'⚠️  Error con superusuario: {e}')
EOF

echo "=========================================="
echo "🚀 Iniciando Daphne..."
echo "=========================================="

# Iniciar Daphne
exec daphne -b 0.0.0.0 -p 8000 proyecto.asgi:application