#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# --- LIMPIEZA DE LOGS ACTIVADA ---
#echo "Limpiando logs de administración..."
#echo "from django.contrib.admin.models import LogEntry; \
#LogEntry.objects.all().delete();" \
#| python manage.py shell

# Crear/Asegurar superusuario
echo "Asegurando superusuario..."
echo "from django.contrib.auth import get_user_model; \
User = get_user_model(); \
User.objects.filter(username='rafa').exists() or \
User.objects.create_superuser('rafa', 'alexrafazam06@gmail.com', 'rafa123')" \
| python manage.py shell