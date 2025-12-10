from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from logistic.models import DeliveryOrder
import qrcode
import os
from io import BytesIO
from django.core.files import File


class PickupOrder(models.Model):
    """
    Заявка на забор груза от клиента
    """

    STATUS_CHOICES = [
        ("new", "Новая"),
        ("confirmed", "Подтверждена"),
        ("picked_up", "Забран"),
        ("cancelled", "Отменена"),
    ]

    # Основные данные из ТЗ
    pickup_date = models.DateField(verbose_name="Дата забора")
    pickup_address = models.CharField(
        max_length=500,
        verbose_name="Адрес забора",
        help_text="Город, улица, дом, помещение",
    )
    client_name = models.CharField(max_length=200, verbose_name="Клиент/Компания")
    client_phone = models.CharField(
        max_length=20, verbose_name="Телефон клиента", blank=True, null=True
    )
    client_email = models.EmailField(
        verbose_name="Email клиента", blank=True, null=True
    )

    # Характеристики груза
    quantity = models.IntegerField(verbose_name="Количество мест")
    weight = models.FloatField(verbose_name="Вес (кг)", blank=True, null=True)
    volume = models.FloatField(verbose_name="Объем (м³)", blank=True, null=True)

    # Дополнительная информация
    cargo_description = models.TextField(
        verbose_name="Описание груза", blank=True, null=True
    )
    special_requirements = models.TextField(
        verbose_name="Особые требования",
        blank=True,
        null=True,
        help_text="Хрупкий груз, температура, сроки и т.д.",
    )

    # Статус и ответственные
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
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

    # Связь с заявкой на доставку (если создана)
    delivery_order = models.OneToOneField(
        DeliveryOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Связанная заявка на доставку",
        related_name="pickup_source",
    )

    # Системные поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    notes = models.TextField(verbose_name="Внутренние заметки", blank=True, null=True)

    # Новые поля для этапа 3
    tracking_number = models.CharField(
        max_length=50, unique=True, blank=True, verbose_name="Сквозной номер заказа"
    )
    qr_code = models.ImageField(
        upload_to="qr_codes/pickup/", blank=True, null=True, verbose_name="QR-код"
    )

    class Meta:
        verbose_name = "Заявка на забор груза"
        verbose_name_plural = "Заявки на забор груза"
        ordering = ["-pickup_date", "-created_at"]

    def __str__(self):
        if self.tracking_number:
            return f"{self.tracking_number} - {self.client_name} на {self.pickup_date}"
        return f"Забор от {self.client_name} на {self.pickup_date}"

    def get_absolute_url(self):
        """Возвращает URL для просмотра деталей заявки"""
        return reverse("pickup_order_detail", kwargs={"pk": self.pk})

    @property
    def is_convertible_to_delivery(self):
        """Можно ли преобразовать в заявку на доставку"""
        return self.status in ["confirmed", "picked_up"] and not self.delivery_order

    def save(self, *args, **kwargs):
        """
        Автоматически управляет QR-кодами:
        1. Генерирует tracking_number при создании
        2. Генерирует QR-код при создании
        3. Автоматически пересоздает QR при изменении важных данных
        """

        # Генерируем уникальный номер
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()

        # Если объект уже существует, проверяем изменения
        if self.pk:
            try:
                old = PickupOrder.objects.get(pk=self.pk)
                # Проверяем, изменились ли данные, которые влияют на QR
                if any(
                    [
                        old.pickup_date != self.pickup_date,
                        old.client_name != self.client_name,
                        old.pickup_address != self.pickup_address,
                        old.quantity != self.quantity,
                        old.weight != self.weight,
                        old.volume != self.volume,
                        old.status != self.status,
                    ]
                ):
                    # Удаляем старый QR-код
                    if self.qr_code and os.path.exists(self.qr_code.path):
                        os.remove(self.qr_code.path)
                    self.qr_code = None
            except PickupOrder.DoesNotExist:
                pass

        # Сохраняем объект
        super().save(*args, **kwargs)

        # Генерируем QR-код если его нет
        if not self.qr_code:
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
        """Генерирует QR-код для заявки на забор"""
        from django.conf import settings

        # Если QR-код уже существует и файл есть - ничего не делаем
        if self.qr_code:
            if os.path.exists(self.qr_code.path):
                return

        # Данные для QR-кода
        qr_data = f"""
Забор груза #{self.id}
Сквозной номер: {self.tracking_number}
Клиент: {self.client_name}
Дата забора: {self.pickup_date}
Адрес: {self.pickup_address}
Места: {self.quantity}
Вес: {self.weight or 'Не указан'} кг
Объем: {self.volume or 'Не указан'} м³
Статус: {self.get_status_display()}
Ссылка: {settings.SITE_URL}{self.get_absolute_url()}
        """.strip()

        try:
            # Создаем QR-код
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            # Создаем изображение
            img = qr.make_image(fill_color="black", back_color="white")

            # Создаем папку, если её нет
            qr_dir = settings.MEDIA_ROOT / "qr_codes" / "pickup"
            qr_dir.mkdir(parents=True, exist_ok=True)

            # Сохраняем в BytesIO
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            # Сохраняем в поле модели
            filename = f'pickup_qr_{self.tracking_number.replace("/", "_")}.png'
            self.qr_code.save(filename, File(buffer), save=False)

            # Закрываем буфер
            buffer.close()

            # Сохраняем модель с QR-кодом
            super().save(update_fields=["qr_code"])

        except Exception as e:
            print(f"Ошибка при создании QR-кода для заявки на забор #{self.id}: {e}")

    def create_delivery_order(self, user):
        """
        Создаёт заявку на доставку на основе заявки на забор
        """
        if not self.is_convertible_to_delivery:
            return None

        # Создаём заявку на доставку
        delivery = DeliveryOrder.objects.create(
            date=self.pickup_date,
            city=self._extract_city_from_address(),
            warehouse="Сборный груз",
            fulfillment="Фулфилмент Царицыно",
            quantity=self.quantity,
            weight=self.weight or 0,
            volume=self.volume or 0,
            status="submitted",
            operator=user,
        )

        # Связываем заявки
        self.delivery_order = delivery
        self.save()

        return delivery

    def _extract_city_from_address(self):
        """Извлекает город из адреса (простая логика)"""
        parts = self.pickup_address.split(",")
        return parts[0].strip() if parts else "Не указан"


