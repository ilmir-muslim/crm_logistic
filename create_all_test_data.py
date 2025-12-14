### BEGIN: create_all_test_data.py
#!/usr/bin/env python
"""
Скрипт для создания всех тестовых данных одним вызовом
"""

import os
import sys
import django

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_logistic.settings")
django.setup()

print("=" * 60)
print("СОЗДАНИЕ ВСЕХ ТЕСТОВЫХ ДАННЫХ CRM ЛОГИСТИКА")
print("=" * 60)

# Сначала создадим пользователей
from django.contrib.auth.models import User
from users.models import UserProfile

print("\n1. СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ...")

# Удаляем старых тестовых пользователей (кроме суперпользователя)
User.objects.filter(is_superuser=False).delete()

# Создаем тестовых пользователей с разными ролями
users_data = [
    {
        "username": "admin",
        "password": "admin123",
        "email": "admin@example.com",
        "first_name": "Администратор",
        "last_name": "Системы",
        "role": "admin",
    },
    {
        "username": "logistic",
        "password": "logistic123",
        "email": "logistic@example.com",
        "first_name": "Иван",
        "last_name": "Логистов",
        "role": "logistic",
    },
    {
        "username": "operator1",
        "password": "operator123",
        "email": "operator1@example.com",
        "first_name": "Мария",
        "last_name": "Операторова",
        "role": "operator",
        "fulfillment": "Фулфилмент Царицыно",
    },
    {
        "username": "operator2",
        "password": "operator123",
        "email": "operator2@example.com",
        "first_name": "Петр",
        "last_name": "Заборщиков",
        "role": "operator",
        "fulfillment": "Фулфилмент Люберцы",
    },
    {
        "username": "operator3",
        "password": "operator123",
        "email": "operator3@example.com",
        "first_name": "Анна",
        "last_name": "Диспетчер",
        "role": "operator",
        "fulfillment": "Фулфилмент Химки",
    },
]

for user_data in users_data:
    user, created = User.objects.get_or_create(
        username=user_data["username"],
        defaults={
            "email": user_data["email"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
        },
    )
    if created:
        user.set_password(user_data["password"])
        user.save()

        # Создаем профиль
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = user_data["role"]
        if "fulfillment" in user_data:
            profile.fulfillment = user_data["fulfillment"]
        profile.save()

        print(f"  ✅ Создан пользователь: {user.username} ({user_data['role']})")
    else:
        print(f"  ⚠️  Пользователь уже существует: {user.username}")

print(f"\n   Всего пользователей: {User.objects.count()}")

# Теперь создаем данные для доставки
print("\n2. СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ ДОСТАВКИ...")
from logistic.models import DeliveryOrder
from datetime import date, timedelta

DeliveryOrder.objects.all().delete()

cities = [
    "Казань",
    "Москва",
    "Санкт-Петербург",
    "Екатеринбург",
    "Новосибирск",
    "Краснодар",
    "Тула",
    "Владивосток",
]
warehouses = ["Склад А", "Склад Б", "Склад В", "Сборный груз"]
fulfillments = ["Фулфилмент Царицыно", "Фулфилмент Люберцы", "Фулфилмент Химки"]

for i in range(40):
    operator = (
        User.objects.filter(username__startswith="operator").order_by("?").first()
        or User.objects.first()
    )

    order = DeliveryOrder.objects.create(
        date=date.today() + timedelta(days=i % 14),
        city=cities[i % len(cities)],
        warehouse=warehouses[i % len(warehouses)],
        fulfillment=fulfillments[i % len(fulfillments)],
        quantity=(i % 10) + 1,
        weight=(i % 100) + 50.5,
        volume=(i % 3) + 0.5,
        status="submitted",
        operator=operator,
    )

    # Назначаем водителя для некоторых заявок
    if i % 3 == 0:
        order.driver_name = f"Водитель {i+1}"
        order.driver_phone = f"+7916{1000000 + i*1000}"
        order.vehicle = f"ГАЗель А{100+i%50}АА"
        order.status = "driver_assigned"
        order.save()

    if i % 5 == 0:
        order.driver_name = f"Водитель {i+5}"
        order.driver_phone = f"+7916{2000000 + i*1000}"
        order.vehicle = f"Камаз Б{200+i%50}ББ"
        order.status = "shipped"
        order.save()

print(f"  ✅ Создано {DeliveryOrder.objects.count()} заявок на доставку")

# Создаем данные для забора
print("\n3. СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ ЗАБОРА...")
from pickup.models import PickupOrder

PickupOrder.objects.all().delete()

clients = [
    "ООО 'Ромашка'",
    "ИП Иванов",
    "АО 'СтройМаш'",
    "ЗАО 'ТехноПром'",
    "ООО 'ЛогистикГрупп'",
    "ИП Петров",
    "АО 'МеталлТрейд'",
    "ЗАО 'СтройГрад'",
]

addresses = [
    "Москва, ул. Ленина, 15, офис 203",
    "Казань, пр. Победы, 42, склад 5",
    "Санкт-Петербург, Невский пр., 100",
    "Екатеринбург, ул. Мамина-Сибиряка, 145",
    "Новосибирск, ул. Кирова, 25",
    "Краснодар, ул. Красная, 150",
]

for i in range(25):
    operator = (
        User.objects.filter(username__startswith="operator").order_by("?").first()
        or User.objects.first()
    )

    order = PickupOrder.objects.create(
        pickup_date=date.today() + timedelta(days=i % 10),
        pickup_address=addresses[i % len(addresses)],
        client_name=f"{clients[i % len(clients)]} #{i+1}",
        client_phone=f"+7916{3000000 + i*1000}",
        client_email=f"client{i}@example.com",
        quantity=(i % 8) + 1,
        weight=(i % 200) + 50.0 if i % 3 != 0 else None,
        volume=(i % 5) + 0.5 if i % 4 != 0 else None,
        cargo_description=f"Тестовый груз #{i+1}",
        special_requirements="Хрупкий груз" if i % 4 == 0 else "",
        status=["new", "confirmed", "picked_up", "cancelled"][i % 4],
        operator=operator,
        notes=f"Тестовая заявка #{i+1}",
    )

print(f"  ✅ Создано {PickupOrder.objects.count()} заявок на забор")

# Создаем несколько связанных заявок (забор -> доставка)
print("\n4. СОЗДАНИЕ СВЯЗАННЫХ ЗАЯВОК...")
from django.db import transaction

# Берем несколько заявок на забор, готовых к преобразованию
pickup_orders = PickupOrder.objects.filter(
    status__in=["confirmed", "picked_up"], delivery_order__isnull=True
)[:5]

for pickup in pickup_orders:
    with transaction.atomic():
        delivery = DeliveryOrder.objects.create(
            date=pickup.pickup_date,
            city=pickup.pickup_address.split(",")[0].strip(),
            warehouse="Сборный груз",
            fulfillment="Фулфилмент Царицыно",
            quantity=pickup.quantity,
            weight=pickup.weight or 0,
            volume=pickup.volume or 0,
            status="submitted",
            operator=pickup.operator,
        )

        pickup.delivery_order = delivery
        pickup.save()

        print(
            f"  🔄 Создана связанная доставка: {pickup.tracking_number} -> {delivery.tracking_number}"
        )

# Статистика
print("\n" + "=" * 60)
print("📊 ИТОГОВАЯ СТАТИСТИКА:")
print("=" * 60)
print(f"👥 Пользователей: {User.objects.count()}")
print(f"🚚 Заявок на доставку: {DeliveryOrder.objects.count()}")
print(f"📦 Заявок на забор: {PickupOrder.objects.count()}")
print(
    f"🔄 Связанных заявок: {PickupOrder.objects.filter(delivery_order__isnull=False).count()}"
)
print(
    f"📱 QR-кодов доставки: {DeliveryOrder.objects.filter(qr_code__isnull=False).count()}"
)
print(
    f"📱 QR-кодов забора: {PickupOrder.objects.filter(qr_code__isnull=False).count()}"
)

print("\n🔑 ДАННЫЕ ДЛЯ ВХОДА:")
print("  Администратор: admin / admin123")
print("  Логист: logistic / logistic123")
print("  Операторы: operator1, operator2, operator3 / operator123")

print("\n✅ Все тестовые данные успешно созданы!")
print("=" * 60)

### END: create_all_test_data.py
