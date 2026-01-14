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

    # Контрагенты вместо текстовых адресов
    sender = models.ForeignKey(
        "counterparties.Counterparty",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_deliveries",
        verbose_name="Отправитель",
        help_text="Контрагент, который отправляет груз",
    )
    sender_address = models.TextField(
        verbose_name="Адрес отправки",
        blank=True,
        null=True,
        help_text="Можно указать вручную, если отправитель не выбран",
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
    recipient_address = models.TextField(
        verbose_name="Адрес доставки",
        blank=True,
        null=True,
        help_text="Можно указать вручную, если получатель не выбран",
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
            return f"{self.tracking_number} - {self.get_sender_display()} → {self.get_recipient_display()}"
        return f"Доставка #{self.id} от {self.date}"

    def get_absolute_url(self):
        return reverse("delivery_order_detail", kwargs={"pk": self.pk})

    def get_sender_display(self):
        """Возвращает отображаемое имя отправителя"""
        if self.sender:
            return self.sender.name
        elif self.sender_address:
            return (
                self.sender_address[:50] + "..."
                if len(self.sender_address) > 50
                else self.sender_address
            )
        return "Не указан"

    def get_recipient_display(self):
        """Возвращает отображаемое имя получателя"""
        if self.recipient:
            return self.recipient.name
        elif self.recipient_address:
            return (
                self.recipient_address[:50] + "..."
                if len(self.recipient_address) > 50
                else self.recipient_address
            )
        return "Не указан"

    def get_full_sender_info(self):
        """Возвращает полную информацию об отправителе"""
        if self.sender:
            return self.sender.get_full_info()
        elif self.sender_address:
            return f"Адрес отправки:\n{self.sender_address}"
        return "Отправитель не указан"

    def get_full_recipient_info(self):
        """Возвращает полную информацию о получателе"""
        if self.recipient:
            return self.recipient.get_full_info()
        elif self.recipient_address:
            return f"Адрес доставки:\n{self.recipient_address}"
        return "Получатель не указан"

    def save(self, *args, **kwargs):
        """Сохраняет заявку и генерирует QR-код при создании"""
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

        # Если QR-код уже существует и файл есть - ничего не делаем
        if self.qr_code:
            try:
                if os.path.exists(self.qr_code.path):
                    return
            except (ValueError, FileNotFoundError, AttributeError):
                pass  # Файл не существует, продолжаем создание

        # Генерируем URL для скачивания PDF
        pdf_url = f"{settings.SITE_URL}{reverse('delivery_order_pdf', kwargs={'pk': self.pk})}"

        # Создаем QR-код только с ссылкой (без текста)
        qr_data = pdf_url

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
            qr_dir = Path(settings.MEDIA_ROOT) / "qr_codes" / "delivery"
            qr_dir.mkdir(parents=True, exist_ok=True)

            # Сохраняем в BytesIO
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            # Сохраняем в поле модели
            filename = f'delivery_qr_{self.tracking_number.replace("/", "_")}.png'
            self.qr_code.save(filename, File(buffer), save=False)

            # Закрываем буфер
            buffer.close()

            # Сохраняем модель с QR-кодом
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
            print(f"❌ Ошибка при пересоздании QR-кода для доставки #{self.id}: {e}")
            return False
