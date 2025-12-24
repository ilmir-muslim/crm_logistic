from pathlib import Path
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
import qrcode
import os
from io import BytesIO
from django.core.files import File


class DeliveryOrder(models.Model):
    STATUS_CHOICES = [
        ("submitted", "Заявка подана"),
        ("driver_assigned", "Назначен водитель"),
        ("shipped", "Отправлено"),
    ]

    date = models.DateField(verbose_name="Дата доставки")

    # Адрес отправки
    pickup_address = models.TextField(
        verbose_name="Адрес отправки",
        blank=True,
        null=True,
    )

    # Адрес доставки (приемки)
    delivery_address = models.TextField(
        verbose_name="Адрес доставки",
        blank=True,
        null=True,
    )

    # Остальные поля остаются без изменений
    fulfillment = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Фулфилмент оператор",
        related_name="delivery_orders",
        limit_choices_to={"profile__role": "operator"},
    )
    quantity = models.IntegerField(verbose_name="Количество мест")
    weight = models.FloatField(verbose_name="Вес (кг)")
    volume = models.FloatField(verbose_name="Объем (м³)")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="submitted"
    )
    driver_name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="ФИО водителя"
    )
    driver_phone = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Телефон водителя"
    )
    vehicle = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Марка и номер ТС"
    )
    driver_pass_info = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Данные пропуска",
        help_text="Номер пропуска, серия, срок действия и т.д.",
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ответственный оператор",
        related_name="created_delivery_orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    tracking_number = models.CharField(
        max_length=50, unique=True, blank=True, verbose_name="Сквозной номер заказа"
    )
    qr_code = models.ImageField(
        upload_to="qr_codes/delivery/", blank=True, null=True, verbose_name="QR-код"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заявка на доставку"
        verbose_name_plural = "Заявки на доставку"

    def __str__(self):
        if self.tracking_number:
            return f"{self.tracking_number} - {self.pickup_address} → {self.delivery_address}"
        return f"Доставка #{self.id} от {self.date}"

    def get_absolute_url(self):
        return reverse("delivery_order_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()

        # Генерируем QR-код при сохранении
        super().save(*args, **kwargs)
        self.check_and_generate_qr_code()

    def check_and_generate_qr_code(self):
        """Проверяет существование QR-кода и создает при необходимости"""
        if not self.qr_code or not os.path.exists(self.qr_code.path):
            self.generate_qr_code()

    def generate_tracking_number(self):
        """Генерирует уникальный сквозной номер заказа"""
        year = timezone.now().year
        last_order = (
            DeliveryOrder.objects.filter(tracking_number__startswith=f"FFC-{year}-")
            .order_by("tracking_number")
            .last()
        )

        if last_order and last_order.tracking_number:
            try:
                last_num = int(last_order.tracking_number.split("-")[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1

        return f"FFC-{year}-{new_num:05d}"


def generate_qr_code(self):
    """Генерирует QR-код для заявки"""
    from django.conf import settings

    # Проверяем, существует ли уже QR-код
    if self.qr_code:
        try:
            if os.path.exists(self.qr_code.path):
                return
        except (ValueError, FileNotFoundError, AttributeError):
            pass

    # Формируем данные для QR-кода (БЕЗ устаревших полей)
    qr_data = f"""
Доставка #{self.id}
Сквозной номер: {self.tracking_number}
Адрес отправки: {self.pickup_address or 'Не указан'}
Адрес доставки: {self.delivery_address or 'Не указан'}
Дата: {self.date}
Места: {self.quantity}
Вес: {self.weight} кг
Объем: {self.volume} м³
Статус: {self.get_status_display()}
Фулфилмент: {self.get_fulfillment_display()}
Водитель: {self.driver_name or 'Не назначен'}
Телефон: {self.driver_phone or 'Не указан'}
ТС: {self.vehicle or 'Не указано'}
Пропуск: {self.driver_pass_info or 'Не требуется'}
Ссылка: {settings.SITE_URL}{self.get_absolute_url()}
    """.strip()

    try:
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

        filename = f'delivery_qr_{self.tracking_number.replace("/", "_")}_{self.id}.png'
        self.qr_code.save(filename, File(buffer), save=False)
        buffer.close()

        super().save(update_fields=["qr_code"])

    except Exception as e:
        print(f"❌ Ошибка при создании QR-кода для заявки #{self.id}: {e}")
        import traceback

        traceback.print_exc()
