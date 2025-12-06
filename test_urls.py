# Создай файл test_urls.py в корне проекта:

import os
import django
from django.urls import reverse, resolve

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_logistic.settings")
django.setup()

print("Тестирование URL...")
print("=" * 50)

try:
    url = reverse("delivery_order_list")
    print(f"✅ URL 'delivery_order_list' найден: {url}")
except Exception as e:
    print(f"❌ Ошибка: {e}")

try:
    from logistic.urls import urlpatterns

    print(f"✅ URL паттерны загружены: {len(urlpatterns)} шт")
    for pattern in urlpatterns:
        print(f"  - {pattern.pattern}: {pattern.name}")
except Exception as e:
    print(f"❌ Ошибка при загрузке URL паттернов: {e}")

print("=" * 50)
