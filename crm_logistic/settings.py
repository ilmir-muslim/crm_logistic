"""
Django settings for crm_logistic project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG")

ALLOWED_HOSTS = ["crm.gulnar8f.beget.tech", 'www.crm.gulnar8f.beget.tech',"localhost", "127.0.0.1"]


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "logistic.apps.LogisticConfig",
    "users.apps.UsersConfig",
    "pickup.apps.PickupConfig",
    "order_form.apps.OrderFormConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "crm_logistic.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Добавляем контекстный процессор для MEDIA_URL
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = "crm_logistic.wsgi.application"


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DATABASE", "crm_logistic"),
        "USER": os.getenv("MYSQL_USER", "crm_logistic_user"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
        "HOST": os.getenv("MYSQL_HOST", "localhost"),
        "PORT": os.getenv("MYSQL_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# Password validation
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
LANGUAGE_CODE = "ru-ru"  # Меняем на русский

TIME_ZONE = "Europe/Moscow"  # Меняем на московское время

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = []

if not os.path.exists(os.path.join(BASE_DIR, "static")):
    os.makedirs(os.path.join(BASE_DIR, "static"))

STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URL сайта для QR-кодов

SITE_URL = os.getenv("SITE_URL")

# Настройки безопасности для продакшена
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = False  # Beget сам перенаправляет HTTPS
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [
    "https://crm.gulnar8f.beget.tech",
    "https://www.crm.gulnar8f.beget.tech",
]
CSRF_COOKIE_DOMAIN = ".gulnar8f.beget.tech"
SESSION_COOKIE_DOMAIN = ".gulnar8f.beget.tech"

X_FRAME_OPTIONS = "DENY"


# Настройки email (для Beget)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "localhost"  # Beget использует локальный sendmail
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
DEFAULT_FROM_EMAIL = "noreply@crm.gulnar8f.beget.tech"
