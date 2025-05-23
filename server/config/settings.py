"""
Django settings for mia project.

Generated by 'django-admin startproject' using Django 5.0.1.

"""

import os
import configparser
from datetime import timedelta
from django.core.management.utils import get_random_secret_key
from corsheaders.defaults import default_headers

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Reading and populating secrets and instance specific information
secrets = configparser.ConfigParser()

# Try reading `.secrets`, fallback to environment variables
secrets_file_path = os.path.join(BASE_DIR, ".secrets")
if os.path.exists(secrets_file_path):
    secrets.read(secrets_file_path)

# Handle missing SECRET_KEY in CI (GitHub Actions)
SECRET_KEY = (
    secrets.get("DJANGO_KEYS", "SECRET_KEY", fallback=None)
    or os.getenv("SECRET_KEY")
    or get_random_secret_key()  # Fallback to a random key in CI
)

# Handle missing SERVER settings gracefully
DEBUG = secrets.getboolean("SERVER", "DEBUG", fallback=True)
ALLOWED_HOSTS = secrets.get("SERVER", "ALLOWED_HOSTS", fallback="*").split(",")
VERSION = secrets.get("SERVER", "SERVER_VERSION", fallback="BETA")
PUBLIC_HOSTNAME = secrets.get("SERVER", "DASHBOARD_URL", fallback="http://localhost:3000/")

# DATABASE settings
ENGINE=secrets.get("DATABASE", "ENGINE", fallback="django.db.backends.postgresql")
NAME=secrets.get("DATABASE", "NAME", fallback="mia_app_prod")
USER=secrets.get("DATABASE", "USER", fallback="miauser")
PASSWORD=secrets.get("DATABASE", "PASSWORD", fallback="miauser")
HOST=secrets.get("DATABASE", "HOST", fallback="localhost") # Or your PostgreSQL server
PORT=secrets.get("DATABASE", "PORT", fallback="5432") # Default PostgreSQL port

# Static files (CSS, JavaScript, Images)
STATIC_URL = secrets.get("STATIC", "STATIC_URL", fallback="/django-static/")
STATIC_ROOT=secrets.get("STATIC", "STATIC_ROOT", fallback=f"{BASE_DIR}/static")
MEDIA_URL = secrets.get("STATIC", "MEDIA_URL", fallback="/media/")
MEDIA_ROOT=secrets.get("STATIC", "MEDIA_ROOT", fallback=f"{BASE_DIR}/media")


DATABASES = {
    'default': {
        'ENGINE': ENGINE,
        'NAME': NAME,
        'USER': USER,
        'PASSWORD': PASSWORD,
        'HOST': HOST,
        'PORT': PORT
    }
}

allowed_hosts_raw = secrets.get("SERVER", "ALLOWED_HOSTS", fallback="*")
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_raw.split(",")]

cors_origins = secrets.get("SERVER", "CORS_ALLOWED_ORIGINS", fallback=None)
if cors_origins:
    CORS_ALLOWED_ORIGINS = cors_origins.split(",")
    CSRF_TRUSTED_ORIGINS = cors_origins.split(",")
else:
    CORS_ALLOWED_ORIGINS = [
        "https://localhost:3000",
        "https://127.0.0.1:3000"
    ]
    CSRF_TRUSTED_ORIGINS = [
        "https://localhost:3000",
        "https://127.0.0.1:3000"
    ]

CORS_ALLOW_CREDENTIALS = True  # Needed for CSRF with cookies

CORS_ALLOW_HEADERS = list(default_headers) + [
    'X-CSRFToken',
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",  # ✅ Crucial for preflight checks
    "PATCH",
    "POST",
    "PUT",
]

AUTH_USER_MODEL = 'authentication.User'

# Application definition
INSTALLED_APPS = [
    'authentication',
    'consentbot',
    "corsheaders",
    'drf_yasg',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_json_widget",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
]
# DRF settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'USER_ID_FIELD': 'user_id',  # Change default from 'id' to 'user_id'
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
