from django.contrib import admin
from .models import PickupOrder


@admin.register(PickupOrder)
class PickupOrderAdmin(admin.ModelAdmin):
    list_display = [
        "pickup_date",
        "client_name",
        "pickup_address",
        "status",
        "quantity",
        "operator",
        "created_at",
    ]
    list_filter = ["status", "pickup_date", "operator", "created_at"]
    search_fields = [
        "client_name",
        "pickup_address",
        "client_phone",
        "cargo_description",
    ]
    list_per_page = 20
    date_hierarchy = "pickup_date"

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "pickup_date",
                    "client_name",
                    "client_phone",
                    "client_email",
                    "pickup_address",
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
    )

    readonly_fields = ["created_at", "updated_at"]
