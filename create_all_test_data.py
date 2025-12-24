#!/usr/bin/env python
"""
Безопасный скрипт для создания тестовых данных
Обходит проблемы с генерацией QR-кодов
"""

import os
import sys
import django
from datetime import date, datetime, timedelta, time

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_logistic.settings")
django.setup()

print("=" * 60)
print("БЕЗОПАСНОЕ СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ")
print("=" * 60)

# Импортируем модели
from django.contrib.auth.models import User
from users.models import UserProfile
from warehouses.models import City, Warehouse
from logistic.models import DeliveryOrder
from pickup.models import PickupOrder
from django.db import transaction

# Временно отключаем генерацию QR-кодов для DeliveryOrder
print("\n1. ВРЕМЕННОЕ ОТКЛЮЧЕНИЕ ГЕНЕРАЦИИ QR-КОДОВ...")

# Сохраняем оригинальный метод save
original_save = DeliveryOrder.save


# Создаем новый метод save без генерации QR-кодов
def new_save(self, *args, **kwargs):
    """Сохраняет DeliveryOrder без генерации QR-кода"""
    # Генерация tracking_number если его нет
    if not self.tracking_number:
        year = datetime.now().year
        last_order = (
            DeliveryOrder.objects.filter(tracking_number__startswith=f"FFC-{year}-")
            .order_by("-tracking_number")
            .first()
        )

        if last_order and last_order.tracking_number:
            try:
                last_num = int(last_order.tracking_number.split("-")[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1

        self.tracking_number = f"FFC-{year}-{new_num:05d}"

    # Сохраняем БЕЗ вызова оригинального save (чтобы избежать генерации QR)
    super(DeliveryOrder, self).save(*args, **kwargs)


# Временно заменяем метод save
DeliveryOrder.save = new_save

print("\n2. СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ...")

# Создаем пользователей
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
]

for user_data in users_data:
    with transaction.atomic():
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

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = user_data["role"]
            if "fulfillment" in user_data:
                profile.fulfillment = user_data["fulfillment"]
            profile.save()
            print(f"  ✅ Создан пользователь: {user.username}")

print(f"\n   Всего пользователей: {User.objects.count()}")

print("\n3. СОЗДАНИЕ ТЕСТОВЫХ ГОРОДОВ И СКЛАДОВ...")

# Создаем 2 города
cities = []
for city_name in ["Москва", "Казань"]:
    city, created = City.objects.get_or_create(
        name=city_name, defaults={"region": f"{city_name}ская область"}
    )
    if created:
        print(f"  ✅ Создан город: {city.name}")
    cities.append(city)

# Создаем 2 склада
admin_user = User.objects.get(username="admin")
warehouses = []
for i, (city, name) in enumerate(
    zip(cities, ["Склад Электросталь", "Основной склад Казань"])
):
    warehouse, created = Warehouse.objects.get_or_create(
        name=name,
        defaults={
            "city": city,
            "code": f"WH-{i+1:03d}",
            "address": f"{city.name}, ул. Промышленная, {i+1}",
            "phone": f"+7 (495) 111-{i+1:02d}{i+1:02d}",
            "email": f"warehouse{i+1}@example.com",
            "manager": admin_user,
            "total_area": 5000,
            "available_area": 3000,
            "opening_time": time(9, 0),
            "closing_time": time(18, 0),
            "work_days": "пн-пт",
        },
    )
    if created:
        print(f"  ✅ Создан склад: {warehouse.name}")
    warehouses.append(warehouse)

print("\n4. СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ ДОСТАВКИ...")

# Удаляем старые данные если есть
DeliveryOrder.objects.all().delete()

# Получаем оператора
operator = User.objects.get(username="operator1")

# Создаем 10 тестовых заявок на доставку
for i in range(10):
    with transaction.atomic():
        # Используем новый метод save
        order = DeliveryOrder(
            date=date.today() + timedelta(days=i % 7),
            pickup_address=f"Москва, ул. Примерная, д. {i+1}",
            delivery_address=f"Казань, ул. Тестовая, д. {i+1}, кв. {i+1}",
            fulfillment=operator,
            quantity=(i % 5) + 1,
            weight=(i * 10) + 50.0,
            volume=(i % 3) + 0.5,
            status="submitted",
            operator=operator,
        )

        # Устанавливаем tracking_number вручную
        order.tracking_number = f"FFC-2025-{i+1:05d}"

        # Сохраняем через новый метод save
        order.save()

        # Для некоторых заявок добавляем данные водителя
        if i % 3 == 0:
            order.driver_name = f"Водитель {i+1}"
            order.driver_phone = f"+7916{1000000 + i}"
            order.vehicle = f"ГАЗель А{100+i}АА"
            order.status = "driver_assigned"
            order.save()

        print(f"  ✅ Создана заявка на доставку: {order.tracking_number}")

print(f"  Всего заявок на доставку: {DeliveryOrder.objects.count()}")

print("\n5. СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ ЗАБОРА...")

# Удаляем старые данные если есть
PickupOrder.objects.all().delete()

# Создаем 5 тестовых заявок на забор
for i in range(5):
    with transaction.atomic():
        order = PickupOrder(
            pickup_date=date.today() + timedelta(days=i % 5),
            pickup_time=time(10 + i % 4, 0),
            pickup_address=f"Москва, ул. Заборная, д. {i+1}",
            contact_person=f"Контакт {i+1}",
            client_name=f"Клиент {i+1}",
            client_company=f"Компания {i+1}",
            client_phone=f"+7916{2000000 + i}",
            client_email=f"client{i+1}@example.com",
            marketplace="Wildberries" if i % 2 == 0 else "Ozon",
            desired_delivery_date=date.today() + timedelta(days=3 + i),
            delivery_address=f"Казань, ул. Доставки, д. {i+1}",
            invoice_number=f"INV-{1000+i}",
            receiving_operator=operator,
            receiving_warehouse=warehouses[i % len(warehouses)],
            delivery_city=cities[i % len(cities)],
            quantity=(i % 4) + 1,
            weight=(i * 20) + 30.0,
            volume=(i % 2) + 0.3,
            cargo_description=f"Тестовый груз #{i+1}",
            status="ready",
            operator=operator,
            notes=f"Тестовая заявка #{i+1}",
        )

        # Устанавливаем tracking_number вручную
        order.tracking_number = f"PUP-2025-{i+1:05d}"

        # Сохраняем (для PickupOrder используем оригинальный save)
        order.save()

        print(f"  ✅ Создана заявка на забор: {order.tracking_number}")

print(f"  Всего заявок на забор: {PickupOrder.objects.count()}")

# Восстанавливаем оригинальный метод save
print("\n6. ВОССТАНОВЛЕНИЕ ОРИГИНАЛЬНЫХ МЕТОДОВ...")
DeliveryOrder.save = original_save

print("\n" + "=" * 60)
print("📊 ИТОГОВАЯ СТАТИСТИКА:")
print("=" * 60)
print(f"👥 Пользователей: {User.objects.count()}")
print(f"🏙️  Городов: {City.objects.count()}")
print(f"🏢 Складов: {Warehouse.objects.count()}")
print(f"🚚 Заявок на доставку: {DeliveryOrder.objects.count()}")
print(f"📦 Заявок на забор: {PickupOrder.objects.count()}")

print("\n🔑 ДАННЫЕ ДЛЯ ВХОДА:")
print("  Администратор: admin / admin123")
print("  Логист: logistic / logistic123")
print("  Оператор: operator1 / operator123")

print("\n✅ Тестовые данные успешно созданы!")
print("=" * 60)

print("\n⚠️  ДЛЯ ГЕНЕРАЦИИ QR-КОДОВ ВЫПОЛНИТЕ:")
print("   python manage.py check_and_fix_qr_codes")
