### BEGIN: create_test_pickup_data.py
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

# Проверяем наличие пользователей
users = User.objects.all()
if users.count() == 0:
    print("Создаем тестовых пользователей...")

    # Создаем оператора для забора
    operator_user = User.objects.create_user(
        username="pickup_operator",
        email="pickup@example.com",
        password="pickup123",
        first_name="Алексей",
        last_name="Заборщиков",
    )
    from users.models import UserProfile

    if hasattr(operator_user, "profile"):
        operator_user.profile.role = "operator"
        operator_user.profile.save()

    users = User.objects.all()

print(f"Найдено {users.count()} пользователей")

# Тестовые данные
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
    "Санкт-Петербург, Невский пр., 100, вход со двора",
    "Тула, ул. Металлургов, 33, цех 2",
    "Екатеринбург, ул. Мамина-Сибиряка, 145",
    "Москва, Ленинградский пр., 72, корпус А",
    "Новосибирск, ул. Кирова, 25, помещение 10",
    "Краснодар, ул. Красная, 150, офис 305",
]

cargo_descriptions = [
    "Оборудование для склада",
    "Канцелярские товары",
    "Электронные компоненты",
    "Хрупкое стекло",
    "Промышленная химия",
    "Бытовая техника",
    "Строительные материалы",
    "Текстильная продукция",
]

special_requirements = [
    "Хрупкий груз",
    "Температурный режим +5...+8°C",
    "Срочная доставка",
    "Требуется грузчики",
    "Забор после 18:00",
    "Подъем на этаж",
    "Негабаритный груз",
    "",
    "",
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
        special_requirements=(
            special_requirements[i % len(special_requirements)] if i % 2 == 0 else ""
        ),
        status=["new", "confirmed", "picked_up", "cancelled"][i % 4],
        operator=operator,
        notes=f"Тестовая заявка #{i+1}. Создана для тестирования системы.\nДополнительные заметки для оператора.",
    )

    print(f"Создана заявка #{order.id}: {order.tracking_number} - {order.client_name}")

print(f"\n✅ Создано {PickupOrder.objects.count()} заявок на забор")

# Покажем распределение
print("\n📊 РАСПРЕДЕЛЕНИЕ ПО СТАТУСАМ:")
for status_code, status_name in PickupOrder.STATUS_CHOICES:
    count = PickupOrder.objects.filter(status=status_code).count()
    print(f"  {status_name}: {count} заявок")

# Покажем сквозные номера
print("\n📊 СКВОЗНЫЕ НОМЕРА (первые 5):")
for order in PickupOrder.objects.order_by("tracking_number")[:5]:
    print(f"  {order.tracking_number}: {order.client_name} на {order.pickup_date}")

# Проверим наличие QR-кодов
qr_count = PickupOrder.objects.filter(qr_code__isnull=False).count()
print(
    f"\n📱 QR-коды сгенерированы для {qr_count} из {PickupOrder.objects.count()} заявок"
)

# Покажем заявки, готовые к преобразованию в доставку
convertible_count = PickupOrder.objects.filter(
    status__in=["confirmed", "picked_up"], delivery_order__isnull=True
).count()
print(f"\n🔄 Готовы к преобразованию в доставку: {convertible_count} заявок")

### END: create_test_pickup_data.py
