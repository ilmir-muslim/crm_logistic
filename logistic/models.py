### BEGIN: logistic/models.py (обновленная версия)
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
    city = models.CharField(max_length=100, verbose_name="Город назначения")
    warehouse = models.CharField(max_length=100, verbose_name="Склад отправки")
    fulfillment = models.CharField(max_length=100, verbose_name="Фулфилмент оператор")
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
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Новые поля для этапа 3
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
            return f"{self.tracking_number} - {self.city} от {self.date}"
        return f"Доставка в {self.city} от {self.date}"

    def get_absolute_url(self):
        return reverse("delivery_order_detail", kwargs={"pk": self.pk})

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
                old = DeliveryOrder.objects.get(pk=self.pk)
                # Проверяем, изменились ли данные, которые влияют на QR
                qr_relevant_fields = [
                    old.date != self.date,
                    old.city != self.city,
                    old.quantity != self.quantity,
                    old.weight != self.weight,
                    old.volume != self.volume,
                    old.status != self.status,
                    old.driver_name != self.driver_name,
                    old.driver_phone != self.driver_phone,
                    old.vehicle != self.vehicle,
                    old.driver_pass_info != self.driver_pass_info,
                ]

                if any(qr_relevant_fields):
                    # Удаляем старый QR-код
                    if self.qr_code and os.path.exists(self.qr_code.path):
                        os.remove(self.qr_code.path)
                    self.qr_code = None
            except DeliveryOrder.DoesNotExist:
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

        # Если QR-код уже существует и файл есть - ничего не делаем
        if self.qr_code:
            if os.path.exists(self.qr_code.path):
                return

        # Данные для QR-кода
        qr_data = f"""
Доставка #{self.id}
Сквозной номер: {self.tracking_number}
Город: {self.city}
Дата: {self.date}
Места: {self.quantity}
Вес: {self.weight} кг
Объем: {self.volume} м³
Статус: {self.get_status_display()}
Водитель: {self.driver_name or 'Не назначен'}
Телефон: {self.driver_phone or 'Не указан'}
ТС: {self.vehicle or 'Не указано'}
Пропуск: {self.driver_pass_info or 'Не требуется'}
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
            qr_dir = settings.MEDIA_ROOT / "qr_codes" / "delivery"
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

        except Exception as e:
            print(f"Ошибка при создании QR-кода для заявки #{self.id}: {e}")

    def is_editable(self):
        """Проверяет, можно ли редактировать заявку"""
        return self.status != "shipped"

    def get_status_color(self):
        """Возвращает цвет статуса для отображения"""
        colors = {
            "submitted": "warning",
            "driver_assigned": "info",
            "shipped": "success",
        }
        return colors.get(self.status, "secondary")


### END: logistic/models.py
