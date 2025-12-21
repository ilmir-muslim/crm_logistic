#!/usr/bin/env python
import os
import sys
import django
from datetime import time

# Добавляем проект в путь Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_logistic.settings")

django.setup()

from warehouses.models import City, Warehouse, ContainerType, WarehouseSchedule
from django.contrib.auth.models import User
from django.db import transaction


def create_test_data():
    """Создает тестовые данные для warehouses"""

    print("🔄 Создание тестовых данных для warehouses...")

    with transaction.atomic():
        # Создаем города
        cities_data = [
            {"name": "Москва", "region": "Московская область"},
            {"name": "Казань", "region": "Республика Татарстан"},
            {"name": "Санкт-Петербург", "region": "Ленинградская область"},
            {"name": "Новосибирск", "region": "Новосибирская область"},
            {"name": "Екатеринбург", "region": "Свердловская область"},
        ]

        for city_data in cities_data:
            city, created = City.objects.get_or_create(
                name=city_data["name"], defaults={"region": city_data["region"]}
            )
            if created:
                print(f"✅ Создан город: {city.name}")

        # Получаем или создаем пользователя для менеджера
        manager, created = User.objects.get_or_create(
            username="warehouse_manager",
            defaults={
                "first_name": "Иван",
                "last_name": "Складской",
                "email": "manager@example.com",
                "is_staff": True,
            },
        )
        if created:
            manager.set_password("password123")
            manager.save()
            print(f"✅ Создан менеджер: {manager.get_full_name()}")

        # Создаем склады для Москвы
        moscow = City.objects.get(name="Москва")
        moscow_warehouses = [
            {
                "name": "Склад Электросталь",
                "code": "MSK-EL",
                "address": "Московская область, г. Электросталь, ул. Промышленная, 1",
                "phone": "+7 (495) 111-11-11",
                "email": "electrostal@example.com",
                "total_area": 5000,
                "available_area": 3500,
                "opening_time": time(8, 0),
                "closing_time": time(20, 0),
                "work_days": "пн-пт, сб",
            },
            {
                "name": "Склад Подольск",
                "code": "MSK-POD",
                "address": "Московская область, г. Подольск, ул. Заводская, 15",
                "phone": "+7 (495) 222-22-22",
                "email": "podolsk@example.com",
                "total_area": 3000,
                "available_area": 2000,
                "opening_time": time(9, 0),
                "closing_time": time(19, 0),
                "work_days": "пн-пт",
            },
            {
                "name": "Склад Коледино",
                "code": "MSK-KOL",
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
        ]

        for wh_data in moscow_warehouses:
            warehouse, created = Warehouse.objects.get_or_create(
                code=wh_data["code"],
                defaults={"city": moscow, "manager": manager, **wh_data},
            )
            if created:
                print(f"✅ Создан склад: {warehouse.name}")

                # Создаем расписание для склада (рабочие дни пн-пт)
                days = [
                    (1, "Понедельник", True),
                    (2, "Вторник", True),
                    (3, "Среда", True),
                    (4, "Четверг", True),
                    (5, "Пятница", True),
                    (6, "Суббота", wh_data.get("work_days", "").find("сб") != -1),
                    (7, "Воскресенье", wh_data.get("work_days", "").find("вс") != -1),
                ]

                for day_num, day_name, is_working in days:
                    WarehouseSchedule.objects.create(
                        warehouse=warehouse,
                        day_of_week=day_num,
                        is_working=is_working,
                        opening_time=(
                            wh_data["opening_time"] if is_working else time(0, 0)
                        ),
                        closing_time=(
                            wh_data["closing_time"] if is_working else time(0, 0)
                        ),
                        pickup_cutoff_time=time(16, 0) if is_working else time(0, 0),
                        delivery_cutoff_time=time(17, 0) if is_working else time(0, 0),
                        max_daily_pickups=20,
                        max_daily_deliveries=30,
                    )
                print(f"  📅 Создано расписание для склада {warehouse.name}")

        # Создаем склады для Казани
        kazan = City.objects.get(name="Казань")
        kazan_warehouses = [
            {
                "name": "Основной склад Казань",
                "code": "KZN-MAIN",
                "address": "г. Казань, ул. Промышленная, 10",
                "phone": "+7 (843) 333-33-33",
                "email": "kazan@example.com",
                "total_area": 4000,
                "available_area": 2500,
                "opening_time": time(9, 0),
                "closing_time": time(18, 0),
                "work_days": "пн-пт, сб",
            },
            {
                "name": "Склад Иннополис",
                "code": "KZN-INN",
                "address": "Республика Татарстан, г. Иннополис, ул. Университетская, 1",
                "phone": "+7 (843) 444-44-44",
                "email": "innopolis@example.com",
                "total_area": 2000,
                "available_area": 1500,
                "opening_time": time(10, 0),
                "closing_time": time(19, 0),
                "work_days": "пн-пт",
            },
        ]

        for wh_data in kazan_warehouses:
            warehouse, created = Warehouse.objects.get_or_create(
                code=wh_data["code"],
                defaults={"city": kazan, "manager": manager, **wh_data},
            )
            if created:
                print(f"✅ Создан склад: {warehouse.name}")

                # Создаем расписание для склада
                days = [
                    (1, "Понедельник", True),
                    (2, "Вторник", True),
                    (3, "Среда", True),
                    (4, "Четверг", True),
                    (5, "Пятница", True),
                    (6, "Суббота", wh_data.get("work_days", "").find("сб") != -1),
                    (7, "Воскресенье", wh_data.get("work_days", "").find("вс") != -1),
                ]

                for day_num, day_name, is_working in days:
                    WarehouseSchedule.objects.create(
                        warehouse=warehouse,
                        day_of_week=day_num,
                        is_working=is_working,
                        opening_time=(
                            wh_data["opening_time"] if is_working else time(0, 0)
                        ),
                        closing_time=(
                            wh_data["closing_time"] if is_working else time(0, 0)
                        ),
                        pickup_cutoff_time=time(15, 0) if is_working else time(0, 0),
                        delivery_cutoff_time=time(16, 0) if is_working else time(0, 0),
                        max_daily_pickups=15,
                        max_daily_deliveries=25,
                    )
                print(f"  📅 Создано расписание для склада {warehouse.name}")

        # Создаем типы коробок
        box_types = [
            {
                "name": "Маленькая коробка",
                "code": "BOX-S",
                "category": "box",
                "length": 30,
                "width": 20,
                "height": 15,
                "weight_capacity": 5,
                "description": "Для небольших и легких товаров",
            },
            {
                "name": "Стандартная коробка",
                "code": "BOX-M",
                "category": "box",
                "length": 40,
                "width": 30,
                "height": 25,
                "weight_capacity": 10,
                "description": "Универсальная коробка для большинства товаров",
            },
            {
                "name": "Большая коробка",
                "code": "BOX-L",
                "category": "box",
                "length": 60,
                "width": 40,
                "height": 35,
                "weight_capacity": 20,
                "description": "Для крупных и тяжелых товаров",
            },
            {
                "name": "Очень большая коробка",
                "code": "BOX-XL",
                "category": "box",
                "length": 80,
                "width": 60,
                "height": 50,
                "weight_capacity": 30,
                "description": "Для объемных и тяжелых грузов",
            },
            {
                "name": "Коробка для одежды",
                "code": "BOX-CLOTH",
                "category": "box",
                "length": 50,
                "width": 40,
                "height": 30,
                "weight_capacity": 15,
                "description": "Специальная коробка для одежды",
            },
            {
                "name": "Коробка для электроники",
                "code": "BOX-ELEC",
                "category": "box",
                "length": 45,
                "width": 35,
                "height": 25,
                "weight_capacity": 8,
                "description": "Защищенная коробка для электроники",
            },
        ]

        for box_data in box_types:
            box, created = ContainerType.objects.get_or_create(
                code=box_data["code"], defaults=box_data
            )
            if created:
                print(f"✅ Создан тип коробки: {box.name}")

        print("\n" + "=" * 50)
        print("✅ Тестовые данные успешно созданы!")
        print("=" * 50)
        print(f"Городов: {City.objects.count()}")
        print(f"Складов: {Warehouse.objects.count()}")
        print(f"Типов коробок: {ContainerType.objects.count()}")
        print("=" * 50)
        print("\n🔑 Для входа в админку используйте:")
        print("   Логин: warehouse_manager")
        print("   Пароль: password123")
        print("\n🌐 Адрес админки: http://localhost:8000/admin/")


if __name__ == "__main__":
    create_test_data()
