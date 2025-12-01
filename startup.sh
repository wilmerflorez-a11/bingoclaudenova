#!/bin/bash

# Colectar archivos estáticos
echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py migrate --noinput

# Crear superusuario si no existe (opcional)
echo "Verificando superusuario..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'cambiar-password-123')
    print('Superusuario creado')
else:
    print('Superusuario ya existe')
EOF

# Iniciar Daphne (servidor ASGI para WebSockets)
echo "Iniciando aplicación con Daphne..."
daphne -b 0.0.0.0 -p 8000 proyecto.asgi:application