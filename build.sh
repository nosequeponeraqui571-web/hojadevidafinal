#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# --- COMANDO CRÍTICO PARA ESTILOS DEL ADMIN ---
python manage.py collectstatic --no-input

python manage.py migrate