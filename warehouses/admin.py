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

    fieldsets = (
        (None, {"fields": ("is_working", "day_of_week")}),
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
        (
            "Крайние сроки приема",
            {
                "fields": ("pickup_cutoff_time", "delivery_cutoff_time"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("day_of_week",)
        return super().get_readonly_fields(request, obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by("day_of_week")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "day_of_week":
            kwargs["widget"] = forms.TextInput(attrs={"readonly": "readonly"})
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
                pickup_cutoff_time = (
                    timezone.datetime.strptime("16:00", "%H:%M").time()
                    if is_working
                    else None
                )
                delivery_cutoff_time = (
                    timezone.datetime.strptime("17:00", "%H:%M").time()
                    if is_working
                    else None
                )

                WarehouseSchedule.objects.create(
                    warehouse=obj,
                    day_of_week=day,
                    is_working=is_working,
                    opening_time=opening_time,
                    closing_time=closing_time,
                    pickup_cutoff_time=pickup_cutoff_time,
                    delivery_cutoff_time=delivery_cutoff_time,
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
        "cutoff_times",
    )
    list_filter = ("warehouse", "day_of_week", "is_working")
    search_fields = ("warehouse__name",)
    readonly_fields = ("day_of_week", "warehouse")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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
        (
            "Крайние сроки приема",
            {
                "fields": ("pickup_cutoff_time", "delivery_cutoff_time"),
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

    def cutoff_times(self, obj):
        if obj.is_working:
            pickup_str = (
                obj.pickup_cutoff_time.strftime("%H:%M")
                if obj.pickup_cutoff_time
                else "Не указано"
            )
            delivery_str = (
                obj.delivery_cutoff_time.strftime("%H:%M")
                if obj.delivery_cutoff_time
                else "Не указано"
            )
            return f"Забор: {pickup_str}, Доставка: {delivery_str}"
        else:
            return "-"

    cutoff_times.short_description = "Крайние сроки"
