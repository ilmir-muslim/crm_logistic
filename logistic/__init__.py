import json
from pathlib import Path
import os
from django.conf import settings


def load_email_settings():
    """Загружает настройки email из файла"""
    try:
        # Для продакшена используем .env или настройки Django
        if os.getenv("DJANGO_PRODUCTION", False):
            # В продакшене настройки из переменных окружения
            settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
            settings.EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
            settings.EMAIL_PORT = int(os.getenv("EMAIL_PORT", 25))
            settings.EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False") == "True"
            settings.EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
            settings.EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
            settings.DEFAULT_FROM_EMAIL = os.getenv(
                "DEFAULT_FROM_EMAIL", "noreply@fftzar-crm.ru"
            )
            settings.OPERATOR_EMAIL = os.getenv(
                "OPERATOR_EMAIL", "operator@fftzar-crm.ru"
            )
        else:
            # Для разработки из файла
            settings_file = Path(settings.BASE_DIR) / "email_settings.json"
            if settings_file.exists():
                with open(settings_file, "r", encoding="utf-8") as f:
                    email_settings = json.load(f)
                    settings.EMAIL_BACKEND = email_settings.get(
                        "email_backend", "django.core.mail.backends.smtp.EmailBackend"
                    )
                    settings.EMAIL_HOST = email_settings.get("email_host", "")
                    settings.EMAIL_PORT = email_settings.get("email_port", 587)
                    settings.EMAIL_USE_TLS = email_settings.get("email_use_tls", True)
                    settings.EMAIL_HOST_USER = email_settings.get("email_host_user", "")
                    settings.EMAIL_HOST_PASSWORD = email_settings.get(
                        "email_host_password", ""
                    )
                    settings.DEFAULT_FROM_EMAIL = email_settings.get(
                        "default_from_email", ""
                    )
                    settings.OPERATOR_EMAIL = email_settings.get("operator_email", "")

    except Exception as e:
        print(f"⚠️ Не удалось загрузить настройки email: {e}")


# Загружаем настройки только если не в продакшене
if not os.getenv("DJANGO_PRODUCTION", False):
    load_email_settings()

