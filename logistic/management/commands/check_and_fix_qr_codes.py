# logistic/management/commands/check_and_fix_qr_codes.py
from django.core.management.base import BaseCommand
from logistic.models import DeliveryOrder
from pickup.models import PickupOrder
import os


class Command(BaseCommand):
    help = "Проверяет и восстанавливает отсутствующие QR-коды"

    def handle(self, *args, **options):
        self.stdout.write("🔍 Начинаем проверку QR-кодов...")

        # Проверяем QR-коды для доставок
        delivery_orders = DeliveryOrder.objects.all()
        delivery_fixed = 0

        self.stdout.write(
            f"\n📦 Проверяем доставки ({delivery_orders.count()} записей):"
        )

        for order in delivery_orders:
            # Всегда проверяем наличие файла для каждой записи с QR-кодом в БД
            needs_fix = False

            if order.qr_code:
                # Проверяем существование файла
                try:
                    if not os.path.exists(order.qr_code.path):
                        self.stdout.write(
                            f"  ✗ Доставка #{order.id} ({order.tracking_number}): запись в БД есть, но файла нет"
                        )
                        needs_fix = True
                except (ValueError, FileNotFoundError, AttributeError):
                    self.stdout.write(
                        f"  ✗ Доставка #{order.id} ({order.tracking_number}): ошибка доступа к файлу"
                    )
                    needs_fix = True
            else:
                # Нет записи в БД
                self.stdout.write(
                    f"  ✗ Доставка #{order.id} ({order.tracking_number}): нет записи о QR-коде в БД"
                )
                needs_fix = True

            if needs_fix:
                # Создаем QR-код заново
                try:
                    # Очищаем старое поле если есть
                    if order.qr_code:
                        order.qr_code.delete(save=False)

                    # Генерируем новый QR-код
                    order.generate_qr_code()
                    delivery_fixed += 1
                    self.stdout.write(f"  ✓ Доставка #{order.id}: QR-код создан")
                except Exception as e:
                    self.stdout.write(
                        f"  ✗ Доставка #{order.id}: ошибка при создании QR-кода: {e}"
                    )

        # Проверяем QR-коды для заборов
        pickup_orders = PickupOrder.objects.all()
        pickup_fixed = 0

        self.stdout.write(f"\n📦 Проверяем заборы ({pickup_orders.count()} записей):")

        for order in pickup_orders:
            # Всегда проверяем наличие файла для каждой записи с QR-кодом в БД
            needs_fix = False

            if order.qr_code:
                # Проверяем существование файла
                try:
                    if not os.path.exists(order.qr_code.path):
                        self.stdout.write(
                            f"  ✗ Забор #{order.id} ({order.tracking_number}): запись в БД есть, но файла нет"
                        )
                        needs_fix = True
                except (ValueError, FileNotFoundError, AttributeError):
                    self.stdout.write(
                        f"  ✗ Забор #{order.id} ({order.tracking_number}): ошибка доступа к файлу"
                    )
                    needs_fix = True
            else:
                # Нет записи в БД
                self.stdout.write(
                    f"  ✗ Забор #{order.id} ({order.tracking_number}): нет записи о QR-коде в БД"
                )
                needs_fix = True

            if needs_fix:
                # Создаем QR-код заново
                try:
                    # Очищаем старое поле если есть
                    if order.qr_code:
                        order.qr_code.delete(save=False)

                    # Генерируем новый QR-код
                    order.generate_qr_code()
                    pickup_fixed += 1
                    self.stdout.write(f"  ✓ Забор #{order.id}: QR-код создан")
                except Exception as e:
                    self.stdout.write(
                        f"  ✗ Забор #{order.id}: ошибка при создании QR-кода: {e}"
                    )

        # Сводка
        self.stdout.write("\n" + "=" * 50)
        if delivery_fixed > 0 or pickup_fixed > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Проверка завершена!\n"
                    f"   Восстановлено доставок: {delivery_fixed}\n"
                    f"   Восстановлено заборов: {pickup_fixed}\n"
                    f"   Всего восстановлено: {delivery_fixed + pickup_fixed} QR-кодов"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("✅ Все QR-коды в порядке!"))
        self.stdout.write("=" * 50)
