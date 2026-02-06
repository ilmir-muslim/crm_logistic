from django.contrib import admin
from .models import DeliveryOrder


@admin.register(DeliveryOrder)
class DeliveryOrderAdmin(admin.ModelAdmin):
    list_display = [
        "tracking_number",
        "date",
        "sender_display",
        "recipient_display",
        "status",
        "quantity",
        "driver_name",
        "logistic_display",
    ]
    list_filter = ["status", "date", "logistic"]
    search_fields = [
        "tracking_number",
        "sender__name",
        "pickup_address",
        "recipient__name",
        "delivery_address",
        "driver_name",
        "vehicle",
        "logistic__username",
        "logistic__first_name",
        "logistic__last_name",
    ]
    readonly_fields = [
        "qr_code_preview",
        "created_at",
        "tracking_number",
        "sender_display",
        "recipient_display",
        "logistic_display",
    ]
    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "tracking_number",
                    "date",
                    "sender",
                    "pickup_address",
                    "pickup_warehouse",
                    "recipient",
                    "delivery_address",
                    "delivery_warehouse",
                    "delivery_city",
                    "logistic",
                    "status",
                )
            },
        ),
        ("Характеристики груза", {"fields": ("quantity", "weight", "volume")}),
        (
            "Информация о перевозке",
            {
                "fields": (
                    "driver_name",
                    "driver_phone",
                    "vehicle",
                    "driver_pass_info",
                    "operator",
                )
            },
        ),
        ("QR-код", {"fields": ("qr_code_preview", "qr_code")}),
        ("Системная информация", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def sender_display(self, obj):
        """Отображение отправителя в списке"""
        if obj.sender:
            return f"{obj.sender.name} ({obj.sender.get_type_display()})"
        elif obj.pickup_warehouse:
            return f"{obj.pickup_warehouse.name} ({obj.pickup_warehouse.address})"
        elif obj.pickup_address:
            return (
                obj.pickup_address[:50] + "..."
                if len(obj.pickup_address) > 50
                else obj.pickup_address
            )
        return "Не указан"

    sender_display.short_description = "Отправитель"

    def recipient_display(self, obj):
        """Отображение получателя в списке"""
        if obj.recipient:
            return f"{obj.recipient.name} ({obj.recipient.get_type_display()})"
        elif obj.delivery_warehouse:
            return f"{obj.delivery_warehouse.name} ({obj.delivery_warehouse.address})"
        elif obj.delivery_address:
            return (
                obj.delivery_address[:50] + "..."
                if len(obj.delivery_address) > 50
                else obj.delivery_address
            )
        return "Не указан"

    recipient_display.short_description = "Получатель"

    def logistic_display(self, obj):
        """Отображение логиста в списке"""
        if obj.logistic:
            if obj.logistic.get_full_name():
                return obj.logistic.get_full_name()
            return obj.logistic.username
        return "Не назначен"

    logistic_display.short_description = "Логист"

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

        self.message_user(
            request, f"Перегенерировано {count} QR-кодов (только ссылка на PDF)"
        )

    regenerate_qr_codes.short_description = "Перегенерировать QR-коды (ссылка на PDF)"


