import os
from pathlib import Path

# Ruta base del proyecto (/code dentro del contenedor)
BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad leída desde .env
SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-insegura-desarrollo')
DEBUG = os.environ.get('DEBUG', '1') == '1'

# Permite conexiones desde localhost y la red de Docker
ALLOWED_HOSTS = ['*']

# Aplicaciones activas en el servidor
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Librerías externas
    'corsheaders',
    'rest_framework',
    # Nuestra aplicación
    'app',
]

# Capas de procesamiento por las que pasa cada petición HTTP
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

# Archivo principal de rutas
ROOT_URLCONF = 'core.urls'

# Dónde buscar archivos HTML (templates)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,  # Busca automáticamente en app/templates/
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Conexión al contenedor 'db' de PostgreSQL usando variables de .env
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'biblioteca_db'),
        'USER': os.environ.get('POSTGRES_USER', 'biblioteca_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'biblioteca_pass'),
        'HOST': os.environ.get('DATABASE_HOST', 'db'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
}

# Configuración de Django REST Framework
# Desactivamos SessionAuthentication por defecto para evitar el error
# "CSRF Failed: CSRF token missing" en las peticiones fetch() JSON de nuestra API.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'UNAUTHENTICATED_USER': None,
    'UNAUTHENTICATED_TOKEN': None,
}

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
