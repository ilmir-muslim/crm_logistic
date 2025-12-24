#!/usr/bin/env python
"""
Скрипт для создания всех тестовых данных одним вызовом
Обновлено под текущую версию проекта с моделями Warehouse и City
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

# Теперь Django будет использовать правильную базу данных из settings.py

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

# Создаем тестовые города и склады
print("\n2. СОЗДАНИЕ ТЕСТОВЫХ ГОРОДОВ И СКЛАДОВ...")
from warehouses.models import City, Warehouse, WarehouseSchedule

# Создаем города
cities_data = [
    {"name": "Москва", "region": "Московская область"},
    {"name": "Казань", "region": "Республика Татарстан"},
    {"name": "Санкт-Петербург", "region": "Ленинградская область"},
    {"name": "Новосибирск", "region": "Новосибирская область"},
    {"name": "Екатеринбург", "region": "Свердловская область"},
    {"name": "Краснодар", "region": "Краснодарский край"},
    {"name": "Тула", "region": "Тульская область"},
    {"name": "Владивосток", "region": "Приморский край"},
]

cities = {}
for city_data in cities_data:
    city, created = City.objects.get_or_create(
        name=city_data["name"], defaults={"region": city_data["region"]}
    )
    cities[city.name] = city
    if created:
        print(f"  ✅ Создан город: {city.name}")

# Создаем склады
admin_user = User.objects.get(username="admin")
warehouses_data = [
    {
        "name": "Склад Электросталь",
        "code": "MSK-EL",
        "city": cities["Москва"],
        "address": "Московская область, г. Электросталь, ул. Промышленная, 1",
        "phone": "+7 (495) 111-11-11",
        "email": "electrostal@example.com",
        "total_area": 5000,
        "available_area": 3500,
        "opening_time": time(8, 0),
        "closing_time": time(20, 0),
        "work_days": "пн-пт, сб",
        "is_24h": False,
    },
    {
        "name": "Склад Подольск",
        "code": "MSK-POD",
        "city": cities["Москва"],
        "address": "Московская область, г. Подольск, ул. Заводская, 15",
        "phone": "+7 (495) 222-22-22",
        "email": "podolsk@example.com",
        "total_area": 3000,
        "available_area": 2000,
        "opening_time": time(9, 0),
        "closing_time": time(19, 0),
        "work_days": "пн-пт",
        "is_24h": False,
    },
    {
        "name": "Склад Коледино",
        "code": "MSK-KOL",
        "city": cities["Москва"],
        "address": "Московская область, г. Домодедово, промзона Коледино",
        "phone": "+7 (495) 333-33-33",
        "email": "koledino@example.com",
        "total_area": 8000,
        "available_area": 6000,
        "opening_time": time(7, 0),
        "closing_time": time(23, 0),
        "work_days": "пн-вс",
        "is_24h": True,
    },
    {
        "name": "Основной склад Казань",
        "code": "KZN-MAIN",
        "city": cities["Казань"],
        "address": "г. Казань, ул. Промышленная, 10",
        "phone": "+7 (843) 333-33-33",
        "email": "kazan@example.com",
        "total_area": 4000,
        "available_area": 2500,
        "opening_time": time(9, 0),
        "closing_time": time(18, 0),
        "work_days": "пн-пт, сб",
        "is_24h": False,
    },
    {
        "name": "Склад Санкт-Петербург",
        "code": "SPB-MAIN",
        "city": cities["Санкт-Петербург"],
        "address": "г. Санкт-Петербург, ул. Индустриальная, 5",
        "phone": "+7 (812) 444-44-44",
        "email": "spb@example.com",
        "total_area": 3500,
        "available_area": 2000,
        "opening_time": time(8, 0),
        "closing_time": time(20, 0),
        "work_days": "пн-пт",
        "is_24h": False,
    },
]

warehouses = {}
for wh_data in warehouses_data:
    warehouse, created = Warehouse.objects.get_or_create(
        code=wh_data["code"],
        defaults={
            "city": wh_data["city"],
            "manager": admin_user,
            "name": wh_data["name"],
            "address": wh_data["address"],
            "phone": wh_data["phone"],
            "email": wh_data["email"],
            "total_area": wh_data["total_area"],
            "available_area": wh_data["available_area"],
            "opening_time": wh_data["opening_time"],
            "closing_time": wh_data["closing_time"],
            "work_days": wh_data["work_days"],
            "is_24h": wh_data["is_24h"],
        },
    )
    warehouses[warehouse.code] = warehouse
    if created:
        print(f"  ✅ Создан склад: {warehouse.name} ({warehouse.city.name})")

        # Создаем расписание для склада
        for day_num in range(1, 8):  # 1-7 дни недели
            is_working = day_num <= 5  # пн-пт рабочие
            if warehouse.is_24h:
                opening = time(0, 0)
                closing = time(23, 59)
            else:
                opening = warehouse.opening_time
                closing = warehouse.closing_time

            WarehouseSchedule.objects.create(
                warehouse=warehouse,
                day_of_week=day_num,
                is_working=is_working,
                opening_time=opening,
                closing_time=closing,
                pickup_cutoff_time=time(16, 0),
                delivery_cutoff_time=time(17, 0),
                max_daily_pickups=20,
                max_daily_deliveries=30,
            )

print(f"  Всего складов: {Warehouse.objects.count()}")

# Теперь создаем данные для доставки
print("\n3. СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ ДОСТАВКИ...")
from logistic.models import DeliveryOrder

DeliveryOrder.objects.all().delete()

# Получаем операторов
operators = User.objects.filter(profile__role="operator")
operator_list = list(operators)

# Города для доставки (используем реальные объекты City)
delivery_cities = list(City.objects.all())
delivery_warehouses = list(Warehouse.objects.all())

for i in range(40):
    operator = operator_list[i % len(operator_list)]
    city = delivery_cities[i % len(delivery_cities)]
    warehouse = delivery_warehouses[i % len(delivery_warehouses)]

    order = DeliveryOrder.objects.create(
        date=date.today() + timedelta(days=i % 14),
        city=city,
        warehouse=warehouse,
        fulfillment=operator,
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
print("\n4. СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ ЗАБОРА...")
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

pickup_cities = list(City.objects.all())
pickup_warehouses = list(Warehouse.objects.all())

for i in range(25):
    operator = operator_list[i % len(operator_list)]
    delivery_city = pickup_cities[i % len(pickup_cities)]
    receiving_warehouse = pickup_warehouses[i % len(pickup_warehouses)]

    order = PickupOrder.objects.create(
        pickup_date=date.today() + timedelta(days=i % 10),
        pickup_address=addresses[i % len(addresses)],
        contact_person=f"Контактное лицо {i+1}",
        client_name=f"Клиент {i+1}",
        client_company=clients[i % len(clients)],
        client_phone=f"+7916{3000000 + i*1000}",
        client_email=f"client{i}@example.com",
        marketplace=["Wildberries", "Ozon", "Яндекс.Маркет", "Собственный сайт"][i % 4],
        desired_delivery_date=date.today() + timedelta(days=(i % 7) + 2),
        delivery_address=f"ул. Доставки, д.{i+1}, кв.{i%10+1}",
        invoice_number=f"INV-{1000+i}",
        receiving_operator=operator,
        receiving_warehouse=receiving_warehouse,
        delivery_city=delivery_city,
        quantity=(i % 8) + 1,
        weight=(i % 200) + 50.0,
        volume=(i % 5) + 0.5,
        cargo_description=f"Тестовый груз #{i+1}",
        special_requirements="Хрупкий груз" if i % 4 == 0 else "",
        status=["ready", "payment"][i % 2],
        operator=operator,
        notes=f"Тестовая заявка #{i+1}",
    )

print(f"  ✅ Создано {PickupOrder.objects.count()} заявок на забор")

# Создаем несколько связанных заявок (забор -> доставка)
print("\n5. СОЗДАНИЕ СВЯЗАННЫХ ЗАЯВОК...")
from django.db import transaction

# Берем несколько заявок на забор, готовых к преобразованию
pickup_orders = PickupOrder.objects.filter(status="ready", delivery_order__isnull=True)[
    :5
]

for pickup in pickup_orders:
    with transaction.atomic():
        delivery = DeliveryOrder.objects.create(
            date=pickup.desired_delivery_date,
            city=pickup.delivery_city,
            warehouse=pickup.receiving_warehouse,
            fulfillment=pickup.operator,
            quantity=pickup.quantity,
            weight=pickup.weight,
            volume=pickup.volume,
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
print(f"🏙️  Городов: {City.objects.count()}")
print(f"🏢 Складов: {Warehouse.objects.count()}")
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

print("\n🌐 Адреса:")
print("  Главная страница: http://localhost:8000/")
print("  Админка: http://localhost:8000/admin/")
print("  Форма забора: http://localhost:8000/order/pickup/")
print("  Форма доставки: http://localhost:8000/order/delivery/")

print("\n✅ Все тестовые данные успешно созданы!")
print("=" * 60)
