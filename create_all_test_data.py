#!/usr/bin/env python
"""
Скрипт для создания всех тестовых данных одним вызовом
Обновлено под текущую версию проекта с актуальными моделями DeliveryOrder и PickupOrder
"""

import os
import sys
import django
from datetime import date, datetime, timedelta, time
import random

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

# Адреса для доставок
pickup_addresses = [
    "Москва, ул. Тверская, д. 10, офис 25",
    "Москва, пр-т Мира, д. 15, склад 3",
    "Казань, ул. Баумана, д. 45, помещение 12",
    "Санкт-Петербург, Невский пр., д. 100, офис 305",
    "Екатеринбург, ул. Малышева, д. 50",
    "Новосибирск, ул. Ленина, д. 30, склад 5",
    "Краснодар, ул. Красная, д. 150, офис 10",
    "Тула, пр-т Ленина, д. 80, помещение 4",
]

delivery_addresses = [
    "Москва, ул. Пушкина, д. 20, кв. 45",
    "Москва, ул. Лермонтова, д. 15, офис 12",
    "Казань, ул. Габдуллы Тукая, д. 60, кв. 33",
    "Санкт-Петербург, ул. Садовая, д. 25, офис 8",
    "Екатеринбург, ул. 8 Марта, д. 70, склад 2",
    "Новосибирск, ул. Кирова, д. 40, помещение 15",
    "Краснодар, ул. Северная, д. 300, офис 5",
    "Тула, ул. Советская, д. 90, кв. 12",
]

driver_names = [
    "Иванов Иван Иванович",
    "Петров Петр Петрович",
    "Сидоров Алексей Владимирович",
    "Кузнецов Дмитрий Сергеевич",
    "Смирнова Анна Михайловна",
    "Попов Андрей Николаевич",
    "Лебедев Сергей Алексеевич",
    "Козлова Екатерина Дмитриевна",
]

vehicles = [
    "ГАЗель NEXT А123АА777",
    "Форд Транзит В234ВВ777",
    "Мерседес Спринтер С345СС777",
    "Фольксваген Крафтер D456DD777",
    "Исузу Эльф Е567ЕЕ777",
    "Пежо Боксер F678FF777",
    "Рено Мастер G789GG777",
    "Фиат Дукато H890HH777",
]

for i in range(40):
    operator = operator_list[i % len(operator_list)]
    pickup_addr = pickup_addresses[i % len(pickup_addresses)]
    delivery_addr = delivery_addresses[i % len(delivery_addresses)]

    # Определяем статус
    status_options = ["submitted", "driver_assigned", "shipped"]
    if i % 3 == 0:
        status = "driver_assigned"
    elif i % 5 == 0:
        status = "shipped"
    else:
        status = "submitted"

    # Создаем заявку на доставку
    order = DeliveryOrder.objects.create(
        date=date.today() + timedelta(days=i % 14),
        pickup_address=pickup_addr,
        delivery_address=delivery_addr,
        fulfillment=operator,
        quantity=(i % 10) + 1,
        weight=(i % 100) + 50.5,
        volume=(i % 3) + 0.5,
        status=status,
        operator=operator,
    )

    # Назначаем водителя для некоторых заявок
    if status == "driver_assigned" or status == "shipped":
        order.driver_name = driver_names[i % len(driver_names)]
        order.driver_phone = f"+7916{1000000 + i*1000}"
        order.vehicle = vehicles[i % len(vehicles)]
        order.save()

    if i % 20 == 0:
        order.driver_pass_info = (
            f"Пропуск №{1000+i}, действует до {date.today() + timedelta(days=365)}"
        )
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

pickup_addresses_pickup = [
    "Москва, ул. Ленина, 15, офис 203",
    "Казань, пр. Победы, 42, склад 5",
    "Санкт-Петербург, Невский пр., 100",
    "Екатеринбург, ул. Мамина-Сибиряка, 145",
    "Новосибирск, ул. Кирова, 25",
    "Краснодар, ул. Красная, 150",
    "Тула, пр-т Ленина, 80, помещение 4",
    "Владивосток, ул. Светланская, 50",
]

marketplaces = ["Wildberries", "Ozon", "Яндекс.Маркет", "Собственный сайт", "Другое"]

# Получаем список складов для привязки
warehouse_list = list(Warehouse.objects.all())
city_list = list(City.objects.all())

for i in range(25):
    operator = operator_list[i % len(operator_list)]
    delivery_city = city_list[i % len(city_list)]
    receiving_warehouse = (
        warehouse_list[i % len(warehouse_list)] if warehouse_list else None
    )

    # Определяем статус
    status_pickup = "ready" if i % 2 == 0 else "payment"

    # Время забора
    pickup_time_obj = time(9 + i % 8, 0)  # С 9 до 17

    order = PickupOrder.objects.create(
        pickup_date=date.today() + timedelta(days=i % 10),
        pickup_time=pickup_time_obj,
        pickup_address=pickup_addresses_pickup[i % len(pickup_addresses_pickup)],
        contact_person=f"Контактное лицо {i+1}",
        client_name=f"Клиент {i+1}",
        client_company=clients[i % len(clients)],
        client_phone=f"+7916{3000000 + i*1000}",
        client_email=f"client{i}@example.com",
        marketplace=marketplaces[i % len(marketplaces)],
        desired_delivery_date=date.today() + timedelta(days=(i % 7) + 2),
        delivery_address=f"ул. Доставки, д.{i+1}, кв.{i%10+1}",
        invoice_number=f"INV-{1000+i}" if i % 3 == 0 else None,
        receiving_operator=operator,
        receiving_warehouse=receiving_warehouse,
        delivery_city=delivery_city,
        quantity=(i % 8) + 1,
        weight=(i % 200) + 50.0,
        volume=(i % 5) + 0.5,
        cargo_description=f"Тестовый груз #{i+1}. "
        + ("Хрупкий груз" if i % 4 == 0 else "Обычный груз"),
        special_requirements="Требуется бережная перевозка" if i % 4 == 0 else "",
        status=status_pickup,
        operator=operator,
        notes=f"Тестовая заявка #{i+1}. Создана автоматически.",
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
        # Используем данные из заявки на забор для создания доставки
        delivery = DeliveryOrder.objects.create(
            date=pickup.desired_delivery_date,
            pickup_address=pickup.pickup_address,
            delivery_address=pickup.delivery_address,
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

# Вывод распределения по статусам
print("\n📊 СТАТУСЫ ЗАЯВОК:")
print(f"  Доставки:")
for status_code, status_name in DeliveryOrder.STATUS_CHOICES:
    count = DeliveryOrder.objects.filter(status=status_code).count()
    print(f"    {status_name}: {count}")

print(f"  Заборы:")
for status_code, status_name in PickupOrder.STATUS_CHOICES:
    count = PickupOrder.objects.filter(status=status_code).count()
    print(f"    {status_name}: {count}")

print("\n🔑 ДАННЫЕ ДЛЯ ВХОДА:")
print("  Администратор: admin / admin123")
print("  Логист: logistic / logistic123")
print("  Операторы: operator1, operator2, operator3 / operator123")

print("\n🌐 Адреса:")
print("  Главная страница: http://localhost:8000/")
print("  Админка: http://localhost:8000/admin/")
print("  Форма забора: http://localhost:8000/order/pickup/")
print("  Форма доставки: http://localhost:8000/order/delivery/")
print("  Список заявок на доставку: http://localhost:8000/delivery/")
print("  Список заявок на забор: http://localhost:8000/pickup/")

print("\n✅ Все тестовые данные успешно созданы!")
print("=" * 60)
