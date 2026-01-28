### BEGIN: warehouses/admin.py
from django.contrib import admin
from django.utils import timezone
from django import forms

from warehouses.forms import WarehouseScheduleForm
from .models import (
    City,
    Warehouse,
    ContainerType,
    WarehouseContainer,
    WarehouseSchedule,
)


class WarehouseScheduleInline(admin.TabularInline):
    model = WarehouseSchedule
    form = WarehouseScheduleForm
    extra = 0
    max_num = 7
    min_num = 7
    can_delete = False
    can_add = False
    day_count = 0  # Инициализируем счетчик класса

    # Исключаем поле day_of_week из отображения
    exclude = ("day_of_week",)

    # Определяем порядок полей с кастомными названиями дней
    fields = (
        "day_display",  # Кастомное текстовое поле для названия дня
        "is_working",
        "opening_time",
        "closing_time",
        "break_start",
        "break_end",
    )

    # Делаем day_display только для чтения
    readonly_fields = ("day_display",)

    def day_display(self, obj=None):
        """
        Отображает название дня недели.
        Для существующих объектов берет из БД,
        для новых - вычисляет по позиции в форме.
        """
        # Определяем список дней недели
        days_of_week = [
            "Понедельник",
            "Вторник",
            "Среда",
            "Четверг",
            "Пятница",
            "Суббота",
            "Воскресенье",
        ]

        # Если объект уже существует и сохранен в БД
        if obj and obj.pk and obj.day_of_week:
            return f" {obj.get_day_of_week_display()}"

        # Для новых объектов определяем день по порядковому номеру формы
        # Используем счетчик класса
        day_index = WarehouseScheduleInline.day_count
        WarehouseScheduleInline.day_count += 1

        if day_index < len(days_of_week):
            return days_of_week[day_index]

        return "День недели"

    day_display.short_description = "День недели"

    def get_queryset(self, request):
        """Сортируем записи по дням недели (пн-вс)"""
        qs = super().get_queryset(request)
        return qs.order_by("day_of_week")

    def get_formset(self, request, obj=None, **kwargs):
        """Создаем формы с уже установленными днями недели"""
        # Сбрасываем счетчик перед созданием formset
        WarehouseScheduleInline.day_count = 0

        formset = super().get_formset(request, obj, **kwargs)

        # Для новых объектов (складов) создаем 7 записей с днями недели
        if not obj:
            # Устанавливаем initial данные для 7 дней
            initial_data = []
            for day_num in range(1, 8):  # от 1 до 7
                initial_data.append(
                    {
                        "day_of_week": day_num,
                        "is_working": True if day_num <= 5 else False,
                    }
                )
            kwargs["initial"] = initial_data

        return formset


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "timezone")
    search_fields = ("name", "region")
    ordering = ("name",)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "code",
        "phone",
        "manager",
        "working_status",
        "available_area",
    )
    list_filter = ("city",)
    search_fields = ("name", "code", "address", "city__name")
    filter_horizontal = ("operators",)

    inlines = [WarehouseScheduleInline]

    fieldsets = (
        ("Основная информация", {"fields": ("city", "name", "code", "address")}),
        (
            "Контактная информация",
            {"fields": ("phone", "email", "manager", "operators")},
        ),
        ("Параметры склада", {"fields": ("total_area", "available_area")}),
    )

    def working_status(self, obj):
        if obj.is_open_now:
            return "🟢 Открыт"
        else:
            return "🔴 Закрыт"

    working_status.short_description = "Статус"

    def get_working_hours_display(self, obj):
        return obj.get_working_hours()

    get_working_hours_display.short_description = "График работы"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not change:
            for day in range(1, 8):
                is_working = True if day <= 5 else False

                # Определяем время в зависимости от того, рабочий ли день
                opening_time = (
                    timezone.datetime.strptime("08:00", "%H:%M").time()
                    if is_working
                    else None
                )
                closing_time = (
                    timezone.datetime.strptime("20:00", "%H:%M").time()
                    if is_working
                    else None
                )

                WarehouseSchedule.objects.create(
                    warehouse=obj,
                    day_of_week=day,
                    is_working=is_working,
                    opening_time=opening_time,
                    closing_time=closing_time,
                )


@admin.register(ContainerType)
class ContainerTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "category",
        "length",
        "width",
        "height",
        "volume",
        "weight_capacity",
        "is_reusable",
    )
    list_filter = ("category", "is_reusable")
    search_fields = ("name", "code")

    fieldsets = (
        (
            "Основная информация",
            {"fields": ("name", "code", "category", "description")},
        ),
        ("Размеры", {"fields": ("length", "width", "height", "volume")}),
        ("Характеристики", {"fields": ("weight_capacity", "is_reusable")}),
        (
            "Цены",
            {
                "fields": ("purchase_price", "rental_price_per_day"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(WarehouseContainer)
class WarehouseContainerAdmin(admin.ModelAdmin):
    list_display = (
        "warehouse",
        "container_type",
        "available_quantity",
        "total_quantity",
        "reserved_quantity",
        "min_stock_level",
        "stock_percentage",
    )
    list_filter = ("warehouse", "container_type")
    search_fields = ("warehouse__name", "container_type__name")

    fieldsets = (
        ("Основная информация", {"fields": ("warehouse", "container_type")}),
        (
            "Количество",
            {
                "fields": (
                    "total_quantity",
                    "available_quantity",
                    "reserved_quantity",
                    "min_stock_level",
                )
            },
        ),
        ("Хранение", {"fields": ("storage_location", "last_restock_date")}),
    )

    def stock_percentage(self, obj):
        return f"{obj.stock_percentage}%"

    stock_percentage.short_description = "Запасы"


@admin.register(WarehouseSchedule)
class WarehouseScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "get_warehouse_name",
        "day_of_week_display",
        "is_working",
        "working_hours_display",
    )
    list_filter = ("warehouse", "day_of_week", "is_working")
    search_fields = ("warehouse__name",)
    readonly_fields = ("day_of_week", "warehouse")

    # УДАЛЕНО: has_add_permission и has_delete_permission
    # Разрешаем добавление и удаление для каскадных операций

    fieldsets = (
        ("Основная информация", {"fields": ("warehouse", "day_of_week", "is_working")}),
        (
            "Часы работы",
            {
                "fields": ("opening_time", "closing_time"),
                "classes": ("collapse",),
            },
        ),
        (
            "Перерыв",
            {
                "fields": ("break_start", "break_end"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_warehouse_name(self, obj):
        return f"{obj.warehouse.name} ({obj.warehouse.city.name})"

    get_warehouse_name.short_description = "Склад"

    def day_of_week_display(self, obj):
        return obj.get_day_of_week_display()

    day_of_week_display.short_description = "День недели"

    def working_hours_display(self, obj):
        return obj.working_hours

    working_hours_display.short_description = "Время работы"


### END: warehouses/admin.py
