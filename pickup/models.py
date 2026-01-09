from pathlib import Path
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from logistic.models import DeliveryOrder
from warehouses.models import Warehouse, City
import qrcode
import os
from io import BytesIO
from django.core.files import File


class PickupOrder(models.Model):
    """
    Заявка на забор груза от клиента
    """

    # Выбор маркетплейсов
    MARKETPLACE_CHOICES = [
        ("Wildberries", "Wildberries"),
        ("Ozon", "Ozon"),
        ("Яндекс.Маркет", "Яндекс.Маркет"),
        ("SberMarket", "SberMarket"),
        ("Собственный сайт", "Собственный сайт"),
        ("Другое", "Другое"),
    ]

    STATUS_CHOICES = [
        ("ready", "Готов к выдаче"),
        ("payment", "На оплате"),
    ]

    # Основные данные из ТЗ
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

    # Контактное лицо для выдачи груза
    contact_person = models.CharField(
        max_length=200,
        verbose_name="Контактное лицо для выдачи груза",
        blank=True,
        null=True,
        help_text="ФИО лица, которое будет выдавать груз",
    )

    # Информация о клиенте
    client_name = models.CharField(
        max_length=200,
        verbose_name="Контактное лицо",
        help_text="ФИО контактного лица",
        default="Не указано",
    )
    client_company = models.CharField(
        max_length=200,
        verbose_name="Наименование компании",
        help_text="Полное наименование компании/ИП",
        default="Не указано",
    )
    client_phone = models.CharField(
        max_length=20,
        verbose_name="Телефон клиента",
        help_text="Телефон для связи",
        default="Не указан",
    )
    client_email = models.EmailField(
        verbose_name="Email клиента",
        help_text="Email для отправки подтверждения",
        default="noemail@example.com",
    )

    # Данные о заказе
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

    # Номер накладной
    invoice_number = models.CharField(
        max_length=100,
        verbose_name="Номер накладной",
        blank=True,
        null=True,
        help_text="Номер транспортной накладной",
    )

    # Оператор приемки и склад
    receiving_operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Оператор приемки",
        related_name="receiving_orders",
    )

    # Обновлено: ForeignKey вместо CharField
    receiving_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Склад приемки",
        related_name="pickup_orders",
        help_text="Склад, куда будет доставлен груз",
    )

    # Новое поле: город доставки
    delivery_city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Город доставки",
        related_name="pickup_orders",
        help_text="Город назначения доставки",
    )

    # Характеристики груза
    quantity = models.IntegerField(verbose_name="Количество мест", default=0)
    weight = models.FloatField(verbose_name="Вес (кг)", default=0.0)
    volume = models.FloatField(verbose_name="Объем (м³)", default=0.0)

    # Дополнительная информация
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
    notes = models.TextField(
        verbose_name="Внутренние заметки", blank=True, null=True, default=""
    )

    # Новые поля для этапа 3
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
            return f"{self.tracking_number} - {self.client_company} на {self.desired_delivery_date}"
        return f"Забор от {self.client_company} на {self.desired_delivery_date}"

    def get_absolute_url(self):
        """Возвращает URL для просмотра деталей заявки"""
        return reverse("pickup_order_detail", kwargs={"pk": self.pk})

    def get_status_color(self):
        """Возвращает цвет статуса для отображения"""
        colors = {
            "ready": "info",  # синий
            "payment": "warning",  # желтый
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

        # Генерируем уникальный номер
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()

        # Определяем, новая ли это запись
        is_new = self.pk is None

        # Сохраняем объект
        super().save(*args, **kwargs)

        # Если запись новая, генерируем QR-код
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
        """Генерирует QR-код с ссылкой на PDF файл доставки"""

        # Если QR-код уже существует и файл есть - ничего не делаем
        if self.qr_code:
            try:
                if os.path.exists(self.qr_code.path):
                    return
            except (ValueError, FileNotFoundError, AttributeError):
                pass

        # Генерируем URL для скачивания PDF
        pdf_url = f"{settings.SITE_URL}{reverse('delivery_order_pdf', kwargs={'pk': self.pk})}"

        # Создаем QR-код только с ссылкой (без текста)
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
            print(f"❌ Ошибка при создании QR-кода для заявки #{self.id}: {e}")
            import traceback

            traceback.print_exc()

    def regenerate_qr_code(self):
        """Принудительно пересоздает QR-код"""
        try:
            # Удаляем старый QR-код если есть
            if self.qr_code:
                try:
                    if os.path.exists(self.qr_code.path):
                        os.remove(self.qr_code.path)
                except:
                    pass
                self.qr_code.delete(save=False)
                self.qr_code = None

            # Генерируем новый QR-код
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

        # Сначала пытаемся использовать receiving_operator из заявки на забор
        if self.receiving_operator and hasattr(self.receiving_operator, "profile"):
            if self.receiving_operator.profile.role == "operator":
                fulfillment_user = self.receiving_operator

        # Если не нашли, проверяем текущего пользователя
        if not fulfillment_user and hasattr(user, "profile"):
            if user.profile.role == "operator":
                fulfillment_user = user

        # Если до сих пор не нашли, ищем любого пользователя с ролью оператора
        if not fulfillment_user:
            from django.contrib.auth.models import User

            try:
                # Ищем первого пользователя с ролью оператора
                fulfillment_user = User.objects.filter(profile__role="operator").first()
            except:
                fulfillment_user = None

        # Если все еще не нашли, используем текущего пользователя
        if not fulfillment_user:
            fulfillment_user = user

        # Создаём заявку на доставку с актуальными полями
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

        # Связываем заявки
        self.delivery_order = delivery
        self.save()

        return delivery

    def _extract_city_from_delivery_address(self):
        """Извлекает город из адреса доставки"""
        if self.delivery_city:
            return self.delivery_city

        parts = self.delivery_address.split(",")
        return parts[0].strip() if parts else "Не указан"
