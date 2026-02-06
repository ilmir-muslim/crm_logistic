from pathlib import Path
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from logistic.models import DeliveryOrder
from warehouses.models import Warehouse, City
from counterparties.models import Counterparty
import qrcode
import os
from io import BytesIO
from django.core.files import File


class Carrier(models.Model):
    """
    Модель перевозчика
    """

    name = models.CharField(
        max_length=200,
        verbose_name="Название перевозчика",
        help_text="Полное наименование компании перевозчика",
    )
    contact_person = models.CharField(
        max_length=200,
        verbose_name="Контактное лицо",
        blank=True,
        null=True,
        help_text="ФИО контактного лица перевозчика",
    )
    phone = models.CharField(
        max_length=50,
        verbose_name="Телефон",
        blank=True,
        null=True,
        help_text="Телефон перевозчика",
    )
    email = models.EmailField(
        verbose_name="Email", blank=True, null=True, help_text="Email перевозчика"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
        help_text="Показывать ли перевозчика в выпадающих списках",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Перевозчик"
        verbose_name_plural = "Перевозчики"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_short_info(self):
        """Краткая информация о перевозчике"""
        info = self.name
        if self.contact_person:
            info += f" ({self.contact_person})"
        return info


class PickupOrder(models.Model):
    """
    Заявка на забор груза от клиента
    """

    MARKETPLACE_CHOICES = [
        ("Wildberries", "Wildberries"),
        ("Ozon", "Ozon"),
        ("Яндекс.Маркет", "Яндекс.Маркет"),
        ("SberMarket", "SberMarket"),
        ("Собственный сайт", "Собственный сайт"),
        ("Другое", "Другое"),
    ]

    STATUS_CHOICES = [
        ("ready", "Готова к выдаче"),
        ("payment", "На оплате"),
        ("accepted", "Принята"),
    ]

    pickup_date = models.DateField(
        verbose_name="Дата забора",
        blank=True,
        null=True,
        help_text="Дата будет назначена оператором после подтверждения",
    )
    pickup_time_from = models.TimeField(
        verbose_name="Время забора от",
        blank=True,
        null=True,
        help_text="Начало интервала забора",
    )
    pickup_time_to = models.TimeField(
        verbose_name="Время забора до",
        blank=True,
        null=True,
        help_text="Конец интервала забора",
    )
    pickup_address = models.CharField(
        max_length=500,
        verbose_name="Адрес забора",
        help_text="Город, улица, дом, помещение",
        default="Не указан",
    )

    contact_person = models.CharField(
        max_length=200,
        verbose_name="Контактное лицо для выдачи груза",
        blank=True,
        null=True,
        help_text="ФИО лица, которое будет выдавать груз",
    )

    sender = models.ForeignKey(
        Counterparty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Отправитель",
        related_name="sent_pickup_orders",
        help_text="Контрагент, который отправляет груз",
    )

    recipient = models.ForeignKey(
        Counterparty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Получатель",
        related_name="received_pickup_orders",
        help_text="Контрагент, который получает груз",
    )

    marketplace = models.CharField(
        max_length=50,
        choices=MARKETPLACE_CHOICES,
        verbose_name="Маркетплейс",
        help_text="Площадка, с которой заказ",
        default="Собственный сайт",
    )
    order_1c_number = models.CharField(
        max_length=50,
        verbose_name="№ заказа в 1С",
        blank=True,
        null=True,
        help_text="Номер заказа в системе 1С",
    )
    desired_delivery_date = models.DateField(
        verbose_name="Желаемая дата поставки",
        help_text="Дата, когда клиент хочет получить заказ",
        default=timezone.now,
    )
    delivery_address = models.TextField(
        verbose_name="Адрес доставки",
        help_text="Полный адрес доставки",
        default="Не указан",
    )

    invoice_number = models.CharField(
        max_length=100,
        verbose_name="Номер накладной",
        blank=True,
        null=True,
        help_text="Номер транспортной накладной",
    )

    receiving_operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Оператор фулфилмента",
        related_name="receiving_orders",
    )

    receiving_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Склад приемки",
        related_name="pickup_orders",
        help_text="Склад, куда будет доставлен груз",
    )

    delivery_city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Город доставки",
        related_name="pickup_orders",
        help_text="Город назначения доставки",
    )

    quantity = models.IntegerField(verbose_name="Количество мест", default=0)
    weight = models.FloatField(verbose_name="Вес (кг)", default=0.0)
    volume = models.FloatField(verbose_name="Объем (м³)", default=0.0)

    cargo_description = models.TextField(
        verbose_name="Комментарий к заказу",
        blank=True,
        null=True,
        help_text="Дополнительная информация о заказе",
        default="",
    )
    special_requirements = models.TextField(
        verbose_name="Особые требования",
        blank=True,
        null=True,
        help_text="Хрупкий груз, температура, сроки и т.д.",
        default="",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ready",
        verbose_name="Статус заявки",
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ответственный оператор",
        related_name="pickup_orders",
    )

    logistic = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Логист",
        related_name="logistic_pickup_orders",
        help_text="Логист, ответственный за заявку",
        limit_choices_to={"profile__role": "logistic"},
    )

    delivery_order = models.OneToOneField(
        DeliveryOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Связанная заявка на доставку",
        related_name="pickup_source",
    )

    carrier = models.ForeignKey(
        Carrier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Перевозчик",
        related_name="pickup_orders",
        help_text="Компания перевозчик для забора груза",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    notes = models.TextField(
        verbose_name="Внутренние заметки", blank=True, null=True, default=""
    )

    tracking_number = models.CharField(
        max_length=50, unique=True, blank=True, verbose_name="Сквозной номер заказа"
    )
    qr_code = models.ImageField(
        upload_to="qr_codes/pickup/", blank=True, null=True, verbose_name="QR-код"
    )

    class Meta:
        verbose_name = "Заявки на забор груза"
        verbose_name_plural = "Заявки на забор груза"
        ordering = ["-pickup_date", "-created_at"]

    def __str__(self):
        if self.tracking_number:
            return f"{self.tracking_number} - {self.get_client_name()} на {self.desired_delivery_date}"
        return f"Забор от {self.get_client_name()} на {self.desired_delivery_date}"

    def get_client_name(self):
        """Возвращает имя клиента из отправителя"""
        if self.sender:
            return self.sender.name
        return "Не указано"

    def get_absolute_url(self):
        """Возвращает URL для просмотра деталей заявки"""
        return reverse("pickup_order_detail", kwargs={"pk": self.pk})

    def get_status_color(self):
        """Возвращает цвет статуса для отображения"""
        colors = {
            "ready": "info",
            "payment": "warning",
            "accepted": "success",
        }
        return colors.get(self.status, "secondary")

    @property
    def is_convertible_to_delivery(self):
        """Можно ли преобразовать в заявку на доставку"""
        return self.status == "ready" and not self.delivery_order

    @property
    def pickup_time_range(self):
        """Возвращает строку с диапазоном времени"""
        if self.pickup_time_from and self.pickup_time_to:
            return f"{self.pickup_time_from.strftime('%H:%M')}-{self.pickup_time_to.strftime('%H:%M')}"
        elif self.pickup_time_from:
            return f"{self.pickup_time_from.strftime('%H:%M')}"
        elif self.pickup_time_to:
            return f"{self.pickup_time_to.strftime('%H:%M')}"
        return "-"

    def save(self, *args, **kwargs):
        """
        Автоматически управляет QR-кодами:
        1. Генерирует tracking_number при создании
        2. Генерирует QR-код при создании (один раз, неизменный)
        """

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
            PickupOrder.objects.filter(tracking_number__startswith=f"PUP-{year}-")
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

        return f"PUP-{year}-{new_num:05d}"

    def generate_qr_code(self):
        """Генерирует QR-код с ссылкой на PDF файл заявки"""
        if self.qr_code:
            try:
                if os.path.exists(self.qr_code.path):
                    return
            except (ValueError, FileNotFoundError, AttributeError):
                pass

        pdf_url = (
            f"{settings.SITE_URL}{reverse('pickup_order_pdf', kwargs={'pk': self.pk})}"
        )

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

            qr_dir = Path(settings.MEDIA_ROOT) / "qr_codes" / "pickup"
            qr_dir.mkdir(parents=True, exist_ok=True)

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            filename = f'pickup_qr_{self.tracking_number.replace("/", "_")}.png'
            self.qr_code.save(filename, File(buffer), save=False)
            buffer.close()

            super().save(update_fields=["qr_code"])
            print(f"✅ QR-код создан для заявки на забор #{self.id}")

        except Exception as e:
            print(f"❌ Ошибка при создании QR-кода для заявки #{self.id}: {e}")
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
            print(f"❌ Ошибка при пересоздании QR-кода для заявки #{self.id}: {e}")
            return False

    def create_delivery_order(self, user):
        """
        Создаёт заявку на доставку на основе заявки на забор
        """
        if not self.is_convertible_to_delivery:
            return None

        fulfillment_user = None

        if self.receiving_operator and hasattr(self.receiving_operator, "profile"):
            if self.receiving_operator.profile.role == "operator":
                fulfillment_user = self.receiving_operator

        if not fulfillment_user and hasattr(user, "profile"):
            if user.profile.role == "operator":
                fulfillment_user = user

        if not fulfillment_user:
            from django.contrib.auth.models import User

            try:
                fulfillment_user = User.objects.filter(profile__role="operator").first()
            except:
                fulfillment_user = None

        if not fulfillment_user:
            fulfillment_user = user

        delivery = DeliveryOrder.objects.create(
            date=self.desired_delivery_date,
            pickup_address=self.pickup_address,
            delivery_address=self.delivery_address,
            fulfillment=fulfillment_user,
            quantity=self.quantity,
            weight=self.weight or 0,
            volume=self.volume or 0,
            status="submitted",
            operator=user,
        )

        self.delivery_order = delivery
        self.save()

        return delivery
