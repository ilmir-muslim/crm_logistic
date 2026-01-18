from django.contrib import admin
from django.utils import timezone
from .models import (
    City,
    Warehouse,
    ContainerType,
    WarehouseContainer,
    WarehouseSchedule,
)


class WarehouseScheduleInline(admin.TabularInline):
    model = WarehouseSchedule
    extra = 0
    max_num = 7  # Максимум 7 записей (по дням недели)
    can_delete = False
    can_add = False

    # Показываем только для существующих складов
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # Предзаполняем значениями по умолчанию
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Если склад уже существует, убедимся, что есть расписание на все дни
        if obj and obj.pk:
            existing_days = set(obj.schedules.values_list("day_of_week", flat=True))
            all_days = set(range(1, 8))

            # Создаем недостающие дни
            for day in all_days - existing_days:
                WarehouseSchedule.objects.create(
                    warehouse=obj,
                    day_of_week=day,
                    is_working=(
                        True if day <= 5 else False
                    ),  # Пн-Пт рабочие по умолчанию
                    opening_time=timezone.datetime.strptime("08:00", "%H:%M").time(),
                    closing_time=timezone.datetime.strptime("20:00", "%H:%M").time(),
                    pickup_cutoff_time=timezone.datetime.strptime(
                        "16:00", "%H:%M"
                    ).time(),
                    delivery_cutoff_time=timezone.datetime.strptime(
                        "17:00", "%H:%M"
                    ).time(),
                )

        return formset

    # Делаем поле дня недели только для чтения
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("day_of_week",)
        return super().get_readonly_fields(request, obj)

    # Форматируем отображение дня недели
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "day_of_week":
            kwargs["widget"] = admin.widgets.AdminTextInputWidget
        return super().formfield_for_dbfield(db_field, request, **kwargs)


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
        "email",
        "manager",
        "is_24h",
        "available_area",
        "working_status",
    )
    list_filter = ("city", "is_24h")
    search_fields = ("name", "code", "address", "city__name")
    filter_horizontal = ("operators",)

    # Добавляем inline для расписания
    inlines = [WarehouseScheduleInline]

    fieldsets = (
        ("Основная информация", {"fields": ("city", "name", "code", "address")}),
        (
            "Контактная информация",
            {"fields": ("phone", "email", "manager", "operators")},
        ),
        ("Параметры склада", {"fields": ("total_area", "available_area")}),
        (
            "Общие настройки",
            {"fields": ("is_24h",)},
        ),
    )

    def working_status(self, obj):
        """Статус работы склада"""
        if obj.is_open_now:
            return "🟢 Открыт"
        else:
            return "🔴 Закрыт"

    working_status.short_description = "Статус"

    def get_working_hours_display(self, obj):
        """Детальный график работы"""
        return obj.get_working_hours()

    get_working_hours_display.short_description = "График работы"

    # Автоматически создаем расписание при сохранении нового склада
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Если склад новый, создаем расписание по дням недели
        if not change:
            for day in range(1, 8):
                WarehouseSchedule.objects.create(
                    warehouse=obj,
                    day_of_week=day,
                    is_working=(
                        True if day <= 5 else False
                    ),  # Пн-Пт рабочие по умолчанию
                    opening_time=timezone.datetime.strptime("08:00", "%H:%M").time(),
                    closing_time=timezone.datetime.strptime("20:00", "%H:%M").time(),
                    pickup_cutoff_time=timezone.datetime.strptime(
                        "16:00", "%H:%M"
                    ).time(),
                    delivery_cutoff_time=timezone.datetime.strptime(
                        "17:00", "%H:%M"
                    ).time(),
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
        "working_hours",
        "cutoff_times",
    )
    list_filter = ("warehouse", "day_of_week", "is_working")
    search_fields = ("warehouse__name",)

    # Запрещаем добавлять/удалять через админку (только редактировать)
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    fieldsets = (
        ("Основная информация", {"fields": ("warehouse", "day_of_week", "is_working")}),
        ("Рабочие часы", {"fields": ("opening_time", "closing_time")}),
        ("Перерыв", {"fields": ("break_start", "break_end")}),
        ("Крайние сроки", {"fields": ("pickup_cutoff_time", "delivery_cutoff_time")}),
    )

    def get_warehouse_name(self, obj):
        return f"{obj.warehouse.name} ({obj.warehouse.city.name})"

    get_warehouse_name.short_description = "Склад"

    def day_of_week_display(self, obj):
        return obj.get_day_of_week_display()

    day_of_week_display.short_description = "День недели"

    def working_hours(self, obj):
        if obj.is_working:
            return f"{obj.opening_time.strftime('%H:%M')} - {obj.closing_time.strftime('%H:%M')}"
        else:
            return "Выходной"

    working_hours.short_description = "Время работы"

    def cutoff_times(self, obj):
        if obj.is_working:
            return f"Забор: {obj.pickup_cutoff_time.strftime('%H:%M')}, Доставка: {obj.delivery_cutoff_time.strftime('%H:%M')}"
        else:
            return "-"

    cutoff_times.short_description = "Крайние сроки"
