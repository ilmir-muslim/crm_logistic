# [file name]: test_order_form.py
from datetime import timedelta
import os
import django
from django.test import TestCase
from django.urls import reverse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_logistic.settings")
django.setup()

from order_form.forms import ClientOrderForm
from django.utils import timezone


# Тест формы
print("Тестирование формы...")
data = {
    "desired_delivery_date": (timezone.now().date() + timedelta(days=2)).strftime(
        "%Y-%m-%d"
    ),
    "pickup_address": "Москва, ул. Ленина, 1",
    "delivery_address": "Казань, ул. Пушкина, 10",
    "marketplace": "Wildberries",
    "client_company": 'ООО "Тестовая компания"',
    "client_name": "Иванов Иван",
    "client_phone": "+79161234567",
    "client_email": "test@example.com",
    "quantity": 5,
    "volume": 2.5,
    "weight": 150.5,
    "order_1c_number": "123456",
    "cargo_description": "Тестовый заказ",
    "privacy_policy": True,
}

form = ClientOrderForm(data=data)
if form.is_valid():
    print("✓ Форма валидна")
    order = form.save()
    print(f"✓ Заявка создана: {order.tracking_number}")
else:
    print("✗ Ошибки формы:", form.errors)
