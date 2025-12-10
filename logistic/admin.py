from django.contrib import admin
from .models import DeliveryOrder


@admin.register(DeliveryOrder)
class DeliveryOrderAdmin(admin.ModelAdmin):
    list_display = [
        "tracking_number",
        "date",
        "city",
        "warehouse",
        "status",
        "quantity",
        "driver_name",
    ]
    list_filter = ["city", "warehouse", "status", "date"]
    search_fields = ["tracking_number", "city", "driver_name", "vehicle"]
    readonly_fields = ["qr_code_preview", "created_at", "tracking_number"]
    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "tracking_number",
                    "date",
                    "city",
                    "warehouse",
                    "fulfillment",
                    "status",
                )
            },
        ),
        ("Характеристики груза", {"fields": ("quantity", "weight", "volume")}),
        (
            "Информация о перевозке",
            {"fields": ("driver_name", "driver_phone", "vehicle", "operator")},
        ),
        ("QR-код", {"fields": ("qr_code_preview", "qr_code")}),
        ("Системная информация", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return f'<img src="{obj.qr_code.url}" width="150" height="150" />'
        return "QR-код не сгенерирован"

    qr_code_preview.short_description = "Превью QR-кода"
    qr_code_preview.allow_tags = True
