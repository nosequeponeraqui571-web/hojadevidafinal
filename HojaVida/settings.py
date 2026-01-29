import os
import dj_database_url
from pathlib import Path

# Directorio Base
BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-ww9j7_=ac%06&-rvo27ci!8f)0^2)+o-m8@1+i^bxys)=%l0@2')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Render Hostnames
ALLOWED_HOSTS = ['*']
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Aplicaciones - El orden de cloudinary_storage es importante
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', 
    'django.contrib.staticfiles',
    'cloudinary_storage',
    'cloudinary',
    'Perfil',
]

# Middlewares
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'HojaVida.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'HojaVida.wsgi.application'

# BASE DE DATOS
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}

# CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# --- CONFIGURACIÓN DE CLOUDINARY ---
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

# Verificamos si las variables existen para activar el almacenamiento en la nube
if CLOUDINARY_STORAGE['CLOUD_NAME'] and CLOUDINARY_STORAGE['API_KEY'] and CLOUDINARY_STORAGE['API_SECRET']:
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = '/media/'
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# Configuración de Storages para Django 4.2+
STORAGES = {
    "default": {
        "BACKEND": DEFAULT_FILE_STORAGE if 'DEFAULT_FILE_STORAGE' in locals() else "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Idioma y Hora
LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil' 
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Permite cargar PDFs en iframes
X_FRAME_OPTIONS = 'SAMEORIGIN'