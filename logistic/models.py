from pathlib import Path
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
import qrcode
import os
from io import BytesIO
from django.core.files import File
from warehouses.models import Warehouse, City  # Добавить импорт


class DeliveryOrder(models.Model):
    STATUS_CHOICES = [
        ("submitted", "Заявка подана"),
        ("driver_assigned", "Назначен водитель"),
        ("shipped", "Отправлено"),
    ]

    date = models.DateField(verbose_name="Дата доставки")

    sender = models.ForeignKey(
        "counterparties.Counterparty",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_deliveries",
        verbose_name="Отправитель",
        help_text="Контрагент, который отправляет груз",
    )
    pickup_address = models.TextField(
        verbose_name="Адрес отправки",
        blank=True,
        null=True,
        help_text="Можно указать вручную, если отправитель не выбран",
    )
    # Добавить поле для склада отправки (аналогично PickupOrder.receiving_warehouse)
    pickup_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pickup_delivery_orders",
        verbose_name="Склад отправки",
        help_text="Склад, откуда отправляется груз",
    )

    recipient = models.ForeignKey(
        "counterparties.Counterparty",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_deliveries",
        verbose_name="Получатель",
        help_text="Контрагент, который получает груз",
    )
    delivery_address = models.TextField(
        verbose_name="Адрес доставки",
        blank=True,
        null=True,
        help_text="Можно указать вручную, если получатель не выбран",
    )
    # Добавить поле для склада доставки
    delivery_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="delivery_delivery_orders",
        verbose_name="Склад доставки",
        help_text="Склад, куда доставляется груз",
    )
    # Добавить поле для города доставки (аналогично PickupOrder.delivery_city)
    delivery_city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="delivery_orders",
        verbose_name="Город доставки",
        help_text="Город назначения доставки",
    )

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
            return f"{self.tracking_number} - {self.get_sender_display()} → {self.get_recipient_display()}"
        return f"Доставка #{self.id} от {self.date}"

    def get_absolute_url(self):
        return reverse("delivery_order_detail", kwargs={"pk": self.pk})


    def get_sender_display(self):
        """Возвращает отображаемое имя отправителя"""
        if self.sender:
            return self.sender.name
        elif self.pickup_warehouse:
            return f"{self.pickup_warehouse.name} ({self.pickup_warehouse.address})"
        elif self.pickup_address:
            return (
                self.pickup_address[:50] + "..."
                if len(self.pickup_address) > 50
                else self.pickup_address
            )
        return "Не указан"


    def get_recipient_display(self):
        """Возвращает отображаемое имя получателя"""
        if self.recipient:
            return self.recipient.name
        elif self.delivery_warehouse:
            return f"{self.delivery_warehouse.name} ({self.delivery_warehouse.address})"
        elif self.delivery_address:
            return (
                self.delivery_address[:50] + "..."
                if len(self.delivery_address) > 50
                else self.delivery_address
            )
        return "Не указан"

    def get_full_sender_info(self):
        """Возвращает полную информацию об отправителе"""
        if self.sender:
            return self.sender.get_full_info()
        elif self.pickup_address:
            return f"Адрес отправки:\n{self.pickup_address}"
        return "Отправитель не указан"

    def get_full_recipient_info(self):
        """Возвращает полную информацию о получателе"""
        if self.recipient:
            return self.recipient.get_full_info()
        elif self.delivery_address:
            return f"Адрес доставки:\n{self.delivery_address}"
        return "Получатель не указан"

    def save(self, *args, **kwargs):
        """Сохраняет заявку и генерирует QR-код при создании"""
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:
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
        """Генерирует QR-код с ссылкой на PDF файл заявки"""
        from django.conf import settings

        if self.qr_code:
            try:
                if os.path.exists(self.qr_code.path):
                    return
            except (ValueError, FileNotFoundError, AttributeError):
                pass

        pdf_url = f"{settings.SITE_URL}{reverse('delivery_order_pdf', kwargs={'pk': self.pk})}"

        qr_data = pdf_url

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

            filename = f'delivery_qr_{self.tracking_number.replace("/", "_")}.png'
            self.qr_code.save(filename, File(buffer), save=False)

            buffer.close()

            super().save(update_fields=["qr_code"])
            print(f"✅ QR-код создан для заявки на доставку #{self.id}")

        except Exception as e:
            print(
                f"❌ Ошибка при создании QR-кода для заявки на доставку #{self.id}: {e}"
            )
            import traceback

            traceback.print_exc()

    def regenerate_qr_code(self):
        """Принудительно пересоздает QR-код"""
        try:
            if self.qr_code:
                try:
                    if os.path.exists(self.qr_code.path):
                        os.remove(self.qr_code.path)
                except:
                    pass
                self.qr_code.delete(save=False)
                self.qr_code = None

            self.generate_qr_code()
            return True
        except Exception as e:
            print(f"❌ Ошибка при пересоздании QR-кода для доставки #{self.id}: {e}")
            return False
