import os
from pathlib import Path
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files import File
from django.urls import reverse


def regenerate_qr_codes_for_pickup():
    """Перегенерация всех QR-кодов для заявок на забор (только ссылка на PDF)"""
    from pickup.models import PickupOrder

    orders = PickupOrder.objects.all()
    regenerated = 0

    for order in orders:
        try:
            # Удаляем старый QR-код если есть
            if order.qr_code:
                try:
                    if os.path.exists(order.qr_code.path):
                        os.remove(order.qr_code.path)
                except:
                    pass
                order.qr_code.delete(save=False)
                order.qr_code = None

            # Генерируем новый QR-код только с ссылкой (без текста)
            pdf_url = f"{settings.SITE_URL}{reverse('pickup_order_pdf', kwargs={'pk': order.pk})}"
            qr_data = pdf_url  # Только ссылка, без текста

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            qr_dir = Path(settings.MEDIA_ROOT) / "qr_codes" / "pickup"
            qr_dir.mkdir(parents=True, exist_ok=True)

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            filename = f'pickup_qr_{order.tracking_number.replace("/", "_")}.png'
            order.qr_code.save(filename, File(buffer), save=False)
            buffer.close()

            order.save(update_fields=["qr_code"])
            regenerated += 1
            print(f"✅ Перегенерирован QR-код для заявки #{order.id} (чистая ссылка)")

        except Exception as e:
            print(f"❌ Ошибка для заявки #{order.id}: {e}")

    return regenerated


def regenerate_qr_codes_for_delivery():
    """Перегенерация всех QR-кодов для заявок на доставку (только ссылка на PDF)"""
    from logistic.models import DeliveryOrder

    orders = DeliveryOrder.objects.all()
    regenerated = 0

    for order in orders:
        try:
            # Удаляем старый QR-код если есть
            if order.qr_code:
                try:
                    if os.path.exists(order.qr_code.path):
                        os.remove(order.qr_code.path)
                except:
                    pass
                order.qr_code.delete(save=False)
                order.qr_code = None

            # Генерируем новый QR-код только с ссылкой (без текста)
            pdf_url = f"{settings.SITE_URL}{reverse('delivery_order_pdf', kwargs={'pk': order.pk})}"
            qr_data = pdf_url  # Только ссылка, без текста

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            qr_dir = Path(settings.MEDIA_ROOT) / "qr_codes" / "delivery"
            qr_dir.mkdir(parents=True, exist_ok=True)

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            filename = f'delivery_qr_{order.tracking_number.replace("/", "_")}.png'
            order.qr_code.save(filename, File(buffer), save=False)
            buffer.close()

            order.save(update_fields=["qr_code"])
            regenerated += 1
            print(f"✅ Перегенерирован QR-код для доставки #{order.id} (чистая ссылка)")

        except Exception as e:
            print(f"❌ Ошибка для доставки #{order.id}: {e}")

    return regenerated


def regenerate_all_qr_codes():
    """Перегенерация всех QR-кодов в системе"""
    pickup_count = regenerate_qr_codes_for_pickup()
    delivery_count = regenerate_qr_codes_for_delivery()

    print("\n" + "=" * 50)
    print(f"✅ Перегенерация завершена!")
    print(f"   Перегенерировано заявок на забор: {pickup_count}")
    print(f"   Перегенерировано заявок на доставку: {delivery_count}")
    print(f"   Всего: {pickup_count + delivery_count}")
    print("=" * 50)

    return pickup_count + delivery_count
