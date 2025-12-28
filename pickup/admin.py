from django.contrib import admin
from .models import PickupOrder


@admin.register(PickupOrder)
class PickupOrderAdmin(admin.ModelAdmin):
    list_display = [
        "tracking_number",
        "pickup_date",
        "pickup_time_range",  # Изменено
        "pickup_address",
        "contact_person",
        "client_name",
        "desired_delivery_date",
        "status",
        "invoice_number",
        "receiving_operator",
        "receiving_warehouse",
        "operator",
        "quantity",
        "created_at",
    ]
    list_filter = [
        "status",
        "pickup_date",
        "operator",
        "receiving_operator",
        "created_at",
    ]
    search_fields = [
        "tracking_number",
        "client_name",
        "contact_person",
        "pickup_address",
        "client_phone",
        "invoice_number",
        "receiving_warehouse",
        "cargo_description",
    ]
    list_per_page = 50
    date_hierarchy = "pickup_date"

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "tracking_number",
                    "pickup_date",
                    "pickup_time_from",  # Изменено
                    "pickup_time_to",  # Добавлено
                    "pickup_address",
                    "contact_person",
                )
            },
        ),
        (
            "Информация о клиенте",
            {
                "fields": (
                    "client_name",
                    "client_company",
                    "client_phone",
                    "client_email",
                    "marketplace",
                )
            },
        ),
        (
            "Детали доставки",
            {
                "fields": (
                    "desired_delivery_date",
                    "delivery_address",
                    "invoice_number",
                )
            },
        ),
        (
            "Приемка груза",
            {
                "fields": (
                    "receiving_operator",
                    "receiving_warehouse",
                )
            },
        ),
        (
            "Характеристики груза",
            {
                "fields": (
                    "quantity",
                    "weight",
                    "volume",
                    "cargo_description",
                    "special_requirements",
                )
            },
        ),
        (
            "Статус и ответственные",
            {"fields": ("status", "operator", "delivery_order", "notes")},
        ),
        (
            "Системная информация",
            {
                "fields": ("created_at", "updated_at", "qr_code"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ["tracking_number", "created_at", "updated_at", "qr_code"]


