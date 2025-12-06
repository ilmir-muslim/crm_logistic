import os
import django
from datetime import date, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_logistic.settings")
django.setup()

from django.contrib.auth.models import User
from pickup.models import PickupOrder

print("СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ МОДУЛЯ ЗАБОРА")
print("=" * 50)

# Удаляем старые данные
PickupOrder.objects.all().delete()
print("Старые заявки на забор удалены")

# Получаем пользователей
users = User.objects.all()
print(f"Найдено {users.count()} пользователей")

# Тестовые данные
clients = [
    "ООО 'Ромашка'",
    "ИП Иванов",
    "АО 'СтройМаш'",
    "ЗАО 'ТехноПром'",
    "ООО 'ЛогистикГрупп'",
]

addresses = [
    "Москва, ул. Ленина, 15, офис 203",
    "Казань, пр. Победы, 42, склад 5",
    "Санкт-Петербург, Невский пр., 100, вход со двора",
    "Тула, ул. Металлургов, 33, цех 2",
    "Екатеринбург, ул. Мамина-Сибиряка, 145",
]

cargo_descriptions = [
    "Оборудование для склада",
    "Канцелярские товары",
    "Электронные компоненты",
    "Хрупкое стекло",
    "Промышленная химия",
]

# Создаем заявки
for i in range(30):
    # Выбираем оператора
    operator = users[i % len(users)]

    order = PickupOrder.objects.create(
        pickup_date=date.today() + timedelta(days=i % 10),
        pickup_address=addresses[i % len(addresses)],
        client_name=f"{clients[i % len(clients)]} #{i+1}",
        client_phone=f"+7916{3000000 + i*1000}",
        client_email=f"client{i}@example.com",
        quantity=(i % 8) + 1,
        weight=(i % 200) + 50.0 if i % 3 != 0 else None,
        volume=(i % 5) + 0.5 if i % 4 != 0 else None,
        cargo_description=cargo_descriptions[i % len(cargo_descriptions)],
        special_requirements="Хрупкий груз" if i % 4 == 0 else "",
        status=["new", "confirmed", "picked_up", "cancelled"][i % 4],
        operator=operator,
        notes=f"Тестовая заявка #{i+1}. Создана для тестирования системы.",
    )

    print(f"Создана заявка #{order.id}: {order.client_name}")

print(f"\n✅ Создано {PickupOrder.objects.count()} заявок на забор")

# Покажем распределение
print("\n📊 РАСПРЕДЕЛЕНИЕ ПО СТАТУСАМ:")
for status_code, status_name in PickupOrder.STATUS_CHOICES:
    count = PickupOrder.objects.filter(status=status_code).count()
    print(f"  {status_name}: {count} заявок")
