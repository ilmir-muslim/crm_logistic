"""
Django settings for crm_logistic project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv("SECRET_KEY")


def str_to_bool(value):
    """Преобразует строку в булево значение"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.lower().strip()
        return value in ("true", "1", "yes", "on", "y", "t")
    return False


IS_PRODUCTION = str_to_bool(os.getenv("DJANGO_PRODUCTION", "False"))

if IS_PRODUCTION:
    DEBUG = False
    ALLOWED_HOSTS = [
        "crm.gulnar8f.beget.tech",
        "www.crm.gulnar8f.beget.tech",
        "fftzar-crm.ru",
        "www.fftzar-crm.ru",
    ]
    print("⚙️  Загружены ПРОДАКШЕН настройки")
else:
    DEBUG = True
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]
    print("🔧 Загружены РАЗРАБОТОЧНЫЕ настройки")


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
    "warehouses.apps.WarehousesConfig",
    "counterparties.apps.CounterpartiesConfig",
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
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = "crm_logistic.wsgi.application"


if IS_PRODUCTION:
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
    print(f"📊 База данных: MySQL ({os.getenv('MYSQL_DATABASE')})")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    print(f"📊 База данных: SQLite ({BASE_DIR / 'db.sqlite3'})")


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


LANGUAGE_CODE = "ru-ru"  

TIME_ZONE = "Europe/Moscow" 

USE_I18N = True

USE_TZ = True


STATIC_URL = "/static/"
STATICFILES_DIRS = []

if not os.path.exists(os.path.join(BASE_DIR, "static")):
    os.makedirs(os.path.join(BASE_DIR, "static"))

STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if IS_PRODUCTION:
    SITE_URL = "https://fftzar-crm.ru"
else:
    SITE_URL = "http://localhost:8000"

print(f"🌐 SITE_URL: {SITE_URL}")

if IS_PRODUCTION:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "localhost" 
    EMAIL_PORT = 25
    EMAIL_USE_TLS = False
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = ""
    EMAIL_HOST_PASSWORD = ""
    DEFAULT_FROM_EMAIL = "noreply@fftzar-crm.ru"
    print("📧 Email: SMTP (продакшен)")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    print("📧 Email: Console (разработка)")

if IS_PRODUCTION:
    required_vars = ["SECRET_KEY", "MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"⚠️  ВНИМАНИЕ: Отсутствуют переменные окружения: {missing}")


LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

