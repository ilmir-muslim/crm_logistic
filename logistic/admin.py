from django.contrib import admin
from .models import DeliveryOrder


@admin.register(DeliveryOrder)
class DeliveryOrderAdmin(admin.ModelAdmin):
    list_display = [
        "tracking_number",
        "date",
        "pickup_address",
        "delivery_address",
        "status",
        "quantity",
        "driver_name",
    ]
    list_filter = ["status", "date"]
    search_fields = [
        "tracking_number",
        "pickup_address",
        "delivery_address",
        "driver_name",
        "vehicle",
    ]
    readonly_fields = ["qr_code_preview", "created_at", "tracking_number"]
    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "tracking_number",
                    "date",
                    "pickup_address",
                    "delivery_address",
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
    actions = ["regenerate_qr_codes"]

    def regenerate_qr_codes(self, request, queryset):
        """Действие для перегенерации QR-кодов"""
        count = 0
        for order in queryset:
            if order.regenerate_qr_code():
                count += 1
        
        self.message_user(request, f"Перегенерировано {count} QR-кодов (только ссылка на PDF)")
    
    regenerate_qr_codes.short_description = "Перегенерировать QR-коды (ссылка на PDF)"

