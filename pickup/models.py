from django.db import models
from django.urls import reverse
from django.conf import settings
from logistic.models import DeliveryOrder


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

    class Meta:
        verbose_name = "Заявка на забор груза"
        verbose_name_plural = "Заявки на забор груза"
        ordering = ["-pickup_date", "-created_at"]

    def __str__(self):
        return f"Забор от {self.client_name} на {self.pickup_date}"

    def get_absolute_url(self):
        """Возвращает URL для просмотра деталей заявки"""
        return reverse("pickup_order_detail", kwargs={"pk": self.pk})

    @property
    def is_convertible_to_delivery(self):
        """Можно ли преобразовать в заявку на доставку"""
        return self.status in ["confirmed", "picked_up"] and not self.delivery_order

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
