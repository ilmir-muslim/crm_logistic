from django.contrib import admin
from .models import (
    City,
    Warehouse,
    ContainerType,
    WarehouseContainer,
    WarehouseSchedule,
)


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
    )
    list_filter = ("city", "is_24h")
    search_fields = ("name", "code", "address", "city__name")
    filter_horizontal = ("operators",)

    fieldsets = (
        ("Основная информация", {"fields": ("city", "name", "code", "address")}),
        (
            "Контактная информация",
            {"fields": ("phone", "email", "manager", "operators")},
        ),
        ("Параметры склада", {"fields": ("total_area", "available_area")}),
        (
            "График работы",
            {"fields": ("opening_time", "closing_time", "work_days", "is_24h")},
        ),
    )

    def get_working_hours(self, obj):
        return obj.get_working_hours()

    get_working_hours.short_description = "График работы"


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
        "warehouse",
        "day_of_week",
        "is_working",
        "opening_time",
        "closing_time",
        "pickup_cutoff_time",
        "delivery_cutoff_time",
    )
    list_filter = ("warehouse", "day_of_week", "is_working")
    search_fields = ("warehouse__name",)

    fieldsets = (
        ("Основная информация", {"fields": ("warehouse", "day_of_week", "is_working")}),
        ("Рабочие часы", {"fields": ("opening_time", "closing_time")}),
        ("Перерыв", {"fields": ("break_start", "break_end")}),
        ("Крайние сроки", {"fields": ("pickup_cutoff_time", "delivery_cutoff_time")}),
        ("Ограничения", {"fields": ("max_daily_pickups", "max_daily_deliveries")}),
    )
