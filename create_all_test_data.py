#!/usr/bin/env python
"""
Скрипт для создания всех тестовых данных одним вызовом
Обновлено для новых моделей городов и складов
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
import random

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_logistic.settings")
django.setup()

print("=" * 60)
print("СОЗДАНИЕ ВСЕХ ТЕСТОВЫХ ДАННЫХ CRM ЛОГИСТИКА")
print("(с поддержкой городов, складов и новой структуры)")
print("=" * 60)

# Сначала создадим пользователей
from django.contrib.auth.models import User
from users.models import UserProfile

print("\n1. СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ...")

# Удаляем старых тестовых пользователей (кроме суперпользователя)
test_users = User.objects.filter(is_superuser=False)
if test_users.exists():
    print(f"  Удаляем {test_users.count()} старых тестовых пользователей...")
    test_users.delete()
    print("  ✅ Старые тестовые пользователи удалены")

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

created_users = []
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

        created_users.append(user.username)
        print(f"  ✅ Создан пользователь: {user.username} ({user_data['role']})")
    else:
        print(f"  ⚠️  Пользователь уже существовал, обновляем: {user.username}")
        # Обновляем существующего пользователя
        user.email = user_data["email"]
        user.first_name = user_data["first_name"]
        user.last_name = user_data["last_name"]
        user.set_password(user_data["password"])
        user.save()

        # Обновляем профиль
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = user_data["role"]
        if "fulfillment" in user_data:
            profile.fulfillment = user_data["fulfillment"]
        profile.save()
        print(f"  ✅ Обновлен пользователь: {user.username}")

print(f"\n   Всего пользователей: {User.objects.count()}")

# Создаем города
print("\n2. СОЗДАНИЕ ТЕСТОВЫХ ГОРОДОВ...")
from warehouses.models import City

# Удаляем старые тестовые города
old_cities = City.objects.all()
if old_cities.exists():
    print(f"  Удаляем {old_cities.count()} старых городов...")
    old_cities.delete()

cities_data = [
    {"name": "Москва", "region": "Московская область"},
    {"name": "Санкт-Петербург", "region": "Ленинградская область"},
    {"name": "Новосибирск", "region": "Новосибирская область"},
    {"name": "Екатеринбург", "region": "Свердловская область"},
    {"name": "Казань", "region": "Республика Татарстан"},
    {"name": "Нижний Новгород", "region": "Нижегородская область"},
    {"name": "Челябинск", "region": "Челябинская область"},
    {"name": "Самара", "region": "Самарская область"},
    {"name": "Омск", "region": "Омская область"},
    {"name": "Ростов-на-Дону", "region": "Ростовская область"},
    {"name": "Краснодар", "region": "Краснодарский край"},
    {"name": "Тула", "region": "Тульская область"},
    {"name": "Владивосток", "region": "Приморский край"},
]

created_cities = {}
for city_data in cities_data:
    city, created = City.objects.get_or_create(
        name=city_data["name"], defaults=city_data
    )
    created_cities[city.name] = city
    if created:
        print(f"  ✅ Создан город: {city.name}")

print(f"   Всего городов: {City.objects.count()}")

# Создаем склады
print("\n3. СОЗДАНИЕ ТЕСТОВЫХ СКЛАДОВ...")
from warehouses.models import Warehouse
from datetime import time

# Удаляем старые тестовые склады
old_warehouses = Warehouse.objects.all()
if old_warehouses.exists():
    print(f"  Удаляем {old_warehouses.count()} старых складов...")
    old_warehouses.delete()

# Получаем администратора для назначения менеджером
admin_user = User.objects.filter(username="admin").first()

warehouses_data = [
    {
        "city": created_cities["Москва"],
        "name": "Склад Царицыно",
        "code": "MSK-TSAR",
        "address": "г. Москва, ул. Луганская, д. 5, склад №1",
        "phone": "+7 (495) 123-45-67",
        "email": "tsaritsyno@fmc-tzaritsyna.ru",
        "total_area": 5000,
        "available_area": 3500,
        "opening_time": time(9, 0),
        "closing_time": time(18, 0),
        "work_days": "пн-пт",
        "manager": admin_user,
    },
    {
        "city": created_cities["Москва"],
        "name": "Склад Люберцы",
        "code": "MSK-LUB",
        "address": "Московская область, г. Люберцы, ул. Красная, д. 10",
        "phone": "+7 (495) 234-56-78",
        "email": "lubertsy@fmc-tzaritsyna.ru",
        "total_area": 3000,
        "available_area": 2000,
        "opening_time": time(8, 0),
        "closing_time": time(20, 0),
        "work_days": "пн-сб",
        "manager": admin_user,
    },
    {
        "city": created_cities["Санкт-Петербург"],
        "name": "Склад Пулково",
        "code": "SPB-PUL",
        "address": "г. Санкт-Петербург, Пулковское шоссе, д. 25",
        "phone": "+7 (812) 345-67-89",
        "email": "pulkovo@fmc-tzaritsyna.ru",
        "total_area": 4000,
        "available_area": 2500,
        "opening_time": time(9, 0),
        "closing_time": time(19, 0),
        "work_days": "пн-пт",
        "manager": admin_user,
    },
    {
        "city": created_cities["Екатеринбург"],
        "name": "Склад Урал",
        "code": "EKB-URAL",
        "address": "г. Екатеринбург, ул. Машиностроителей, д. 15",
        "phone": "+7 (343) 456-78-90",
        "email": "ural@fmc-tzaritsyna.ru",
        "total_area": 2500,
        "available_area": 1500,
        "opening_time": time(8, 30),
        "closing_time": time(17, 30),
        "work_days": "пн-пт",
        "manager": admin_user,
    },
    {
        "city": created_cities["Казань"],
        "name": "Склад Татарстан",
        "code": "KAZ-TAT",
        "address": "г. Казань, ул. Пушкина, д. 42",
        "phone": "+7 (843) 567-89-01",
        "email": "kazan@fmc-tzaritsyna.ru",
        "total_area": 2000,
        "available_area": 1200,
        "opening_time": time(9, 0),
        "closing_time": time(18, 0),
        "work_days": "пн-пт",
        "manager": admin_user,
    },
]

created_warehouses = {}
for wh_data in warehouses_data:
    warehouse, created = Warehouse.objects.get_or_create(
        code=wh_data["code"], defaults=wh_data
    )
    created_warehouses[warehouse.name] = warehouse
    if created:
        print(f"  ✅ Создан склад: {warehouse.name} ({warehouse.city.name})")

# Назначаем операторов на склады
operator_users = User.objects.filter(
    username__in=["operator1", "operator2", "operator3"]
)
for warehouse in Warehouse.objects.all():
    for operator in operator_users:
        warehouse.operators.add(operator)
    print(f"  ✅ Назначены операторы на склад: {warehouse.name}")

print(f"   Всего складов: {Warehouse.objects.count()}")

# Создаем типы тары
print("\n4. СОЗДАНИЕ ТИПОВ ТАРЫ...")
from warehouses.models import ContainerType, WarehouseContainer

# Удаляем старые данные о таре
WarehouseContainer.objects.all().delete()
ContainerType.objects.all().delete()

container_types_data = [
    {
        "name": "Коробка S",
        "code": "BOX-S",
        "category": "box",
        "length": 40,
        "width": 30,
        "height": 40,
        "weight_capacity": 15,
        "is_reusable": False,
        "purchase_price": 50.00,
    },
    {
        "name": "Коробка M",
        "code": "BOX-M",
        "category": "box",
        "length": 60,
        "width": 40,
        "height": 40,
        "weight_capacity": 30,
        "is_reusable": False,
        "purchase_price": 80.00,
    },
    {
        "name": "Коробка L",
        "code": "BOX-L",
        "category": "box",
        "length": 60,
        "width": 80,
        "height": 50,
        "weight_capacity": 50,
        "is_reusable": False,
        "purchase_price": 120.00,
    },
    {
        "name": "Коробка XL",
        "code": "BOX-XL",
        "category": "box",
        "length": 120,
        "width": 80,
        "height": 180,
        "weight_capacity": 1200,
        "is_reusable": True,
        "purchase_price": 1500.00,
    },
    {
        "name": "Еврокуб 1000л",
        "code": "EURO-1000",
        "category": "container",
        "length": 120,
        "width": 100,
        "height": 116,
        "weight_capacity": 1200,
        "is_reusable": True,
        "purchase_price": 8000.00,
        "rental_price_per_day": 100.00,
    },
    {
        "name": "Паллет 80x120",
        "code": "PAL-80x120",
        "category": "pallet",
        "length": 120,
        "width": 80,
        "height": 15,
        "weight_capacity": 2000,
        "is_reusable": True,
        "purchase_price": 1500.00,
        "rental_price_per_day": 50.00,
    },
]

for ct_data in container_types_data:
    ct, created = ContainerType.objects.get_or_create(
        code=ct_data["code"], defaults=ct_data
    )
    if created:
        print(f"  ✅ Создан тип тары: {ct.name} ({ct.code})")

print(f"   Всего типов тары: {ContainerType.objects.count()}")

# Создаем запасы тары на складах
print("\n5. СОЗДАНИЕ ЗАПАСОВ ТАРЫ НА СКЛАДАХ...")

for warehouse in Warehouse.objects.all():
    for container_type in ContainerType.objects.filter(category="box"):
        wc, created = WarehouseContainer.objects.get_or_create(
            warehouse=warehouse,
            container_type=container_type,
            defaults={
                "total_quantity": random.randint(50, 200),
                "available_quantity": random.randint(30, 150),
                "reserved_quantity": random.randint(0, 20),
                "min_stock_level": 20,
                "storage_location": f"Секция {chr(65 + random.randint(0, 3))}, стеллажи 1-5",
                "last_restock_date": date.today()
                - timedelta(days=random.randint(0, 30)),
            },
        )
        if created:
            print(f"  ✅ Создан запас {container_type.name} на складе {warehouse.name}")

print(f"   Всего записей о запасах: {WarehouseContainer.objects.count()}")

# Теперь создаем данные для доставки
print("\n6. СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ ДОСТАВКИ...")
from logistic.models import DeliveryOrder

# Удаляем старые тестовые данные доставки
old_deliveries = DeliveryOrder.objects.all()
if old_deliveries.exists():
    print(f"  Удаляем {old_deliveries.count()} старых заявок на доставку...")
    old_deliveries.delete()
    print("  ✅ Старые заявки на доставку удалены")

warehouse_names = ["Склад А", "Склад Б", "Склад В", "Сборный груз"]
fulfillments = ["Фулфилмент Царицыно", "Фулфилмент Люберцы", "Фулфилмент Химки"]

created_deliveries = 0
for i in range(40):
    operator = (
        User.objects.filter(username__startswith="operator").order_by("?").first()
        or User.objects.first()
    )

    # Используем города из созданных
    random_city = random.choice(list(created_cities.values()))

    order = DeliveryOrder.objects.create(
        date=date.today() + timedelta(days=i % 14),
        city=random_city.name,
        warehouse=random.choice(warehouse_names),
        fulfillment=random.choice(fulfillments),
        quantity=(i % 10) + 1,
        weight=(i % 100) + 50.5,
        volume=(i % 3) + 0.5,
        status="submitted",
        operator=operator,
    )
    created_deliveries += 1

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

print(f"  ✅ Создано {created_deliveries} заявок на доставку")

# Создаем данные для забора с новыми статусами и использованием складов
print("\n7. СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ ЗАБОРА (с городами и складами)...")
from pickup.models import PickupOrder

# Удаляем старые тестовые данные забора
old_pickups = PickupOrder.objects.all()
if old_pickups.exists():
    print(f"  Удаляем {old_pickups.count()} старых заявок на забор...")
    old_pickups.delete()
    print("  ✅ Старые заявки на забор удалены")

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

marketplaces = [
    "Wildberries",
    "Ozon",
    "Яндекс.Маркет",
    "SberMarket",
    "Собственный сайт",
    "Другое",
]

contact_persons = [
    "Иванов Иван Иванович",
    "Петров Петр Петрович",
    "Сидорова Анна Сергеевна",
    "Кузнецов Алексей Владимирович",
    "Морозова Екатерина Дмитриевна",
    "Соколов Денис Андреевич",
]

created_pickups = 0
for i in range(25):
    operator = (
        User.objects.filter(username__startswith="operator").order_by("?").first()
        or User.objects.first()
    )

    # Определяем статус (чередуем ready и payment)
    status = "ready" if i % 2 == 0 else "payment"

    # Вес и объем
    weight_value = (i % 200) + 50.0
    volume_value = (i % 5) + 0.5

    # Выбираем случайный склад и город
    random_warehouse = random.choice(list(created_warehouses.values()))
    random_city = random.choice(list(created_cities.values()))

    # Создаем заявку на забор с новыми ForeignKey полями
    order = PickupOrder.objects.create(
        pickup_date=date.today() + timedelta(days=i % 10),
        pickup_time=(
            (datetime.now() + timedelta(hours=9, minutes=30)).time()
            if i % 3 == 0
            else None
        ),
        pickup_address=addresses[i % len(addresses)],
        contact_person=contact_persons[i % len(contact_persons)],
        delivery_city=random_city,
        delivery_address=f"Ул. Примерная, д. {i+1}, кв. {(i%20)+1}",
        client_name=f"Контактное лицо {i+1}",
        client_company=clients[i % len(clients)],
        client_phone=f"+7916{3000000 + i*1000}",
        client_email=f"client{i}@example.com",
        marketplace=marketplaces[i % len(marketplaces)],
        order_1c_number=f"1C-2024-{1000+i:04d}" if i % 3 == 0 else "",
        desired_delivery_date=date.today() + timedelta(days=(i % 10) + 2),
        invoice_number=f"ТН-2024-{5000+i:05d}" if i % 2 == 0 else "",
        receiving_operator=operator if i % 3 == 0 else None,
        receiving_warehouse=random_warehouse,
        quantity=(i % 8) + 1,
        weight=weight_value,
        volume=volume_value,
        cargo_description=f"Тестовый груз #{i+1}. Состоит из {((i % 8) + 1)} мест, вес {weight_value} кг.",
        special_requirements="Хрупкий груз" if i % 4 == 0 else "Без особых требований",
        status=status,
        operator=operator,
        notes=f"Тестовая заявка #{i+1}. Статус: {status}. Склад: {random_warehouse.name}",
    )
    created_pickups += 1

print(
    f"  ✅ Создано {created_pickups} заявок на забор с использованием складов и городов"
)

# Создаем несколько связанных заявок (забор -> доставка)
print("\n8. СОЗДАНИЕ СВЯЗАННЫХ ЗАЯВОК...")
from django.db import transaction

# Берем несколько заявок на забор со статусом "ready", готовых к преобразованию
pickup_orders = PickupOrder.objects.filter(status="ready", delivery_order__isnull=True)[
    :5
]

created_links = 0
for pickup in pickup_orders:
    with transaction.atomic():
        try:
            delivery = DeliveryOrder.objects.create(
                date=pickup.pickup_date if pickup.pickup_date else date.today(),
                city=(
                    pickup.delivery_city.name
                    if pickup.delivery_city
                    else pickup.pickup_address.split(",")[0].strip()
                ),
                warehouse=(
                    pickup.receiving_warehouse.name
                    if pickup.receiving_warehouse
                    else "Сборный груз"
                ),
                fulfillment="Фулфилмент Царицыно",
                quantity=pickup.quantity,
                weight=pickup.weight or 0,
                volume=pickup.volume or 0,
                status="submitted",
                operator=pickup.operator,
            )

            pickup.delivery_order = delivery
            pickup.save()

            created_links += 1
            print(
                f"  🔄 Создана связанная доставка: {pickup.tracking_number} -> {delivery.tracking_number}"
            )
        except Exception as e:
            print(f"  ❌ Ошибка при создании связанной доставки: {e}")

# Статистика
print("\n" + "=" * 60)
print("📊 ИТОГОВАЯ СТАТИСТИКА:")
print("=" * 60)
print(f"👥 Пользователей: {User.objects.count()}")
print(f"🏙️  Городов: {City.objects.count()}")
print(f"🏭 Складов: {Warehouse.objects.count()}")
print(f"📦 Типов тары: {ContainerType.objects.count()}")
print(f"📊 Запасов на складах: {WarehouseContainer.objects.count()}")
print(f"🚚 Заявок на доставку: {DeliveryOrder.objects.count()}")
print(f"📦 Заявок на забор: {PickupOrder.objects.count()}")
print(f"  - Готов к выдаче: {PickupOrder.objects.filter(status='ready').count()}")
print(f"  - На оплате: {PickupOrder.objects.filter(status='payment').count()}")
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

print("\n🏙️  СОЗДАННЫЕ ГОРОДА:")
for city in City.objects.all().order_by("name"):
    print(f"  - {city.name} ({city.region or 'без региона'})")

print("\n🏭 СОЗДАННЫЕ СКЛАДЫ:")
for warehouse in Warehouse.objects.all().order_by("city__name", "name"):
    print(f"  - {warehouse.name} в {warehouse.city.name}")

print("\n✅ Все тестовые данные успешно созданы!")
print("=" * 60)
