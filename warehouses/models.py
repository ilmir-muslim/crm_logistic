from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator


class City(models.Model):
    """Город с информацией о логистических возможностях"""

    name = models.CharField(max_length=100, verbose_name="Название города", unique=True)
    region = models.CharField(
        max_length=100, verbose_name="Регион/Область", blank=True, null=True
    )
    timezone = models.CharField(
        max_length=50, verbose_name="Часовой пояс", default="Europe/Moscow"
    )

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    """Склад с доступными объемами и графиком работы"""

    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="warehouses", verbose_name="Город"
    )
    name = models.CharField(max_length=200, verbose_name="Название склада")
    code = models.CharField(max_length=50, verbose_name="Код склада", unique=True)

    # Контактная информация
    address = models.TextField(verbose_name="Адрес склада")
    phone = models.CharField(max_length=20, verbose_name="Телефон склада")
    email = models.EmailField(verbose_name="Email склада", blank=True, null=True)

    # Ответственные лица
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_warehouses",
        verbose_name="Менеджер склада",
    )
    operators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="operated_warehouses",
        verbose_name="Операторы",
        blank=True,
    )

    # Параметры склада
    total_area = models.FloatField(
        verbose_name="Общая площадь (м²)",
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
    )
    available_area = models.FloatField(
        verbose_name="Доступная площадь (м²)",
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
    )

    # График работы
    opening_time = models.TimeField(
        verbose_name="Время открытия",
        default=timezone.datetime.strptime("09:00", "%H:%M").time(),
        blank=True,
        null=True,
    )
    closing_time = models.TimeField(
        verbose_name="Время закрытия",
        default=timezone.datetime.strptime("18:00", "%H:%M").time(),
        blank=True,
        null=True,
    )
    work_days = models.CharField(
        max_length=100,
        verbose_name="Рабочие дни",
        default="пн-пт",
        help_text="пн-пт, сб, вс",
        blank=True,
        null=True,
    )
    is_24h = models.BooleanField(verbose_name="Круглосуточный", default=False)

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"
        ordering = ["city", "name"]

    def __str__(self):
        return f"{self.name} ({self.city.name})"

    def get_working_hours(self):
        """Возвращает строку с графиком работы"""
        if self.is_24h:
            return "24/7"

        # Проверяем, что времена не None
        if not self.opening_time or not self.closing_time:
            return "График работы не указан"

        return f"{self.opening_time.strftime('%H:%M')} - {self.closing_time.strftime('%H:%M')}, {self.work_days}"

    def get_available_capacity_percentage(self):
        """Возвращает процент доступной площади"""
        if self.total_area > 0:
            return round((self.available_area / self.total_area) * 100, 1)
        return 0


    @property
    def is_open_now(self):
        """Проверяет, работает ли склад сейчас"""
        if self.is_24h:
            return True

        now = timezone.now()
        current_time = now.time()
        current_day = now.strftime("%a").lower()

        # Проверяем, что времена не None
        if not self.opening_time or not self.closing_time:
            return False

        # Простая проверка времени
        if current_time < self.opening_time or current_time > self.closing_time:
            return False

        # Проверка дней недели
        if "пн-пт" in self.work_days and current_day in ["sat", "sun"]:
            return False

        return True
    
    def get_detailed_working_hours(self):
        """Возвращает детальный график работы на основе расписания"""
        if self.is_24h:
            return "Круглосуточно"
        
        schedules = self.schedules.filter(is_working=True).order_by('day_of_week')
        if not schedules.exists():
            return "График работы не указан"
        
        # Группируем по одинаковому времени работы
        schedule_dict = {}
        for schedule in schedules:
            key = f"{schedule.opening_time.strftime('%H:%M')}-{schedule.closing_time.strftime('%H:%M')}"
            if key not in schedule_dict:
                schedule_dict[key] = []
            schedule_dict[key].append(schedule.get_day_of_week_display())
        
        result = []
        for time_range, days in schedule_dict.items():
            if len(days) == 7:
                result.append(f"Ежедневно: {time_range}")
            elif len(days) == 5 and all(day in days for day in ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]):
                result.append(f"Пн-Пт: {time_range}")
            elif len(days) == 2 and all(day in days for day in ["Суббота", "Воскресенье"]):
                result.append(f"Сб-Вс: {time_range}")
            else:
                days_str = ", ".join(days)
                result.append(f"{days_str}: {time_range}")
        
        return "; ".join(result)

    def is_working_day(self, date):
        """Проверяет, работает ли склад в указанную дату"""
        day_of_week = date.isoweekday()
        try:
            schedule = WarehouseSchedule.objects.get(
                warehouse=self, 
                day_of_week=day_of_week
            )
            return schedule.is_working
        except WarehouseSchedule.DoesNotExist:
            return False



class ContainerType(models.Model):
    """Тип тары/контейнера"""

    CONTAINER_CATEGORIES = [
        ("pallet", "Паллеты"),
        ("box", "Коробки"),
        ("bag", "Мешки"),
        ("drum", "Бочки"),
        ("container", "Контейнеры"),
        ("other", "Прочее"),
    ]

    name = models.CharField(max_length=100, verbose_name="Название тары")
    code = models.CharField(max_length=20, verbose_name="Код тары", unique=True)
    category = models.CharField(
        max_length=20, choices=CONTAINER_CATEGORIES, verbose_name="Категория"
    )
    length = models.FloatField(
        verbose_name="Длина (см)", validators=[MinValueValidator(0)]
    )
    width = models.FloatField(
        verbose_name="Ширина (см)", validators=[MinValueValidator(0)]
    )
    height = models.FloatField(
        verbose_name="Высота (см)", validators=[MinValueValidator(0)]
    )
    weight_capacity = models.FloatField(
        verbose_name="Грузоподъемность (кг)", validators=[MinValueValidator(0)]
    )
    volume = models.FloatField(
        verbose_name="Объем (м³)",
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
    )
    description = models.TextField(verbose_name="Описание", blank=True, null=True)
    is_reusable = models.BooleanField(default=False, verbose_name="Многоразовая")
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена закупки",
        blank=True,
        null=True,
    )
    rental_price_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Аренда в сутки",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Тип тары"
        verbose_name_plural = "Типы тары"

    def __str__(self):
        return f"{self.name} ({self.code})"

    def calculate_volume(self):
        """Рассчитывает объем в м³"""
        volume_cm = self.length * self.width * self.height
        return round(volume_cm / 1000000, 3)  # Конвертация см³ в м³

    def save(self, *args, **kwargs):
        """Автоматически рассчитываем объем при сохранении"""
        if not self.volume:
            self.volume = self.calculate_volume()
        super().save(*args, **kwargs)


class WarehouseContainer(models.Model):
    """Доступные объемы тары на складе"""

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="containers",
        verbose_name="Склад",
    )
    container_type = models.ForeignKey(
        ContainerType, on_delete=models.CASCADE, verbose_name="Тип тары"
    )
    total_quantity = models.IntegerField(
        verbose_name="Общее количество", validators=[MinValueValidator(0)]
    )
    available_quantity = models.IntegerField(
        verbose_name="Доступное количество", validators=[MinValueValidator(0)]
    )
    reserved_quantity = models.IntegerField(
        verbose_name="Зарезервировано", default=0, validators=[MinValueValidator(0)]
    )
    min_stock_level = models.IntegerField(
        verbose_name="Минимальный запас", default=10, validators=[MinValueValidator(0)]
    )
    storage_location = models.CharField(
        max_length=100,
        verbose_name="Место хранения",
        blank=True,
        null=True,
        help_text="Секция, стеллаж, ячейка",
    )
    last_restock_date = models.DateField(
        verbose_name="Дата последнего пополнения", blank=True, null=True
    )

    class Meta:
        verbose_name = "Тара на складе"
        verbose_name_plural = "Тара на складах"
        unique_together = ["warehouse", "container_type"]

    def __str__(self):
        return f"{self.container_type.name} на {self.warehouse.name}"

    @property
    def is_low_stock(self):
        """Проверяет, низкий ли запас"""
        return self.available_quantity <= self.min_stock_level

    @property
    def stock_percentage(self):
        """Возвращает процент доступного запаса"""
        if self.total_quantity > 0:
            return round((self.available_quantity / self.total_quantity) * 100, 1)
        return 0

    def reserve(self, quantity):
        """Резервирует тару"""
        if quantity <= self.available_quantity:
            self.available_quantity -= quantity
            self.reserved_quantity += quantity
            self.save()
            return True
        return False

    def release(self, quantity):
        """Освобождает зарезервированную тару"""
        if quantity <= self.reserved_quantity:
            self.reserved_quantity -= quantity
            self.available_quantity += quantity
            self.save()
            return True
        return False


class WarehouseSchedule(models.Model):
    """Детальный график приема заявок по дням"""

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name="Склад",
    )
    day_of_week = models.IntegerField(
        choices=[
            (1, "Понедельник"),
            (2, "Вторник"),
            (3, "Среда"),
            (4, "Четверг"),
            (5, "Пятница"),
            (6, "Суббота"),
            (7, "Воскресенье"),
        ],
        verbose_name="День недели",
    )
    is_working = models.BooleanField(default=True, verbose_name="Рабочий день")
    opening_time = models.TimeField(verbose_name="Время открытия")
    closing_time = models.TimeField(verbose_name="Время закрытия")
    break_start = models.TimeField(
        verbose_name="Начало перерыва", blank=True, null=True
    )
    break_end = models.TimeField(verbose_name="Конец перерыва", blank=True, null=True)
    pickup_cutoff_time = models.TimeField(
        verbose_name="Крайний срок приема заявок на забор",
        help_text="После этого времени заявки на следующий день",
    )
    delivery_cutoff_time = models.TimeField(
        verbose_name="Крайний срок приема заявок на доставку"
    )


    class Meta:
        verbose_name = "График работы по дням"
        verbose_name_plural = "Графики работы по дням"
        unique_together = ["warehouse", "day_of_week"]

    def __str__(self):
        return f"{self.get_day_of_week_display()} - {self.warehouse.name}"

    @property
    def working_hours(self):
        """Возвращает рабочие часы"""
        return f"{self.opening_time.strftime('%H:%M')}-{self.closing_time.strftime('%H:%M')}"

    def is_available_for_time(self, time):
        """Проверяет доступность в указанное время"""
        if not self.is_working:
            return False

        if time < self.opening_time or time > self.closing_time:
            return False

        if self.break_start and self.break_end:
            if self.break_start <= time <= self.break_end:
                return False

        return True
