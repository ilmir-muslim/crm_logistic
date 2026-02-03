from django.contrib import admin
from .models import PickupOrder, Carrier


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "contact_person",
        "phone",
        "email",
        "is_active",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "created_at",
    ]
    search_fields = [
        "name",
        "contact_person",
        "phone",
        "email",
    ]
    list_per_page = 50
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "name",
                    "contact_person",
                    "phone",
                    "email",
                    "is_active",
                )
            },
        ),
        (
            "Системная информация",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ["created_at", "updated_at"]


@admin.register(PickupOrder)
class PickupOrderAdmin(admin.ModelAdmin):
    list_display = [
        "tracking_number",
        "pickup_date",
        "pickup_time_range",
        "pickup_address",
        "contact_person",
        "get_sender_display",
        "get_recipient_display",
        "desired_delivery_date",
        "status",
        "invoice_number",
        "receiving_operator",
        "receiving_warehouse",
        "get_carrier_display",
        "operator",
        "quantity",
        "created_at",
    ]
    list_filter = [
        "status",
        "pickup_date",
        "operator",
        "receiving_operator",
        "carrier",
        "created_at",
    ]
    search_fields = [
        "tracking_number",
        "sender__name",
        "sender__inn",
        "recipient__name",
        "recipient__inn",
        "contact_person",
        "pickup_address",
        "invoice_number",
        "receiving_warehouse__name",
        "carrier__name",
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
                    "pickup_time_from",
                    "pickup_time_to",
                    "pickup_address",
                    "contact_person",
                )
            },
        ),
        (
            "Информация о контрагентах",
            {
                "fields": (
                    "sender",
                    "recipient",
                    "marketplace",
                )
            },
        ),
        (
            "Детали доставки",
            {
                "fields": (
                    "desired_delivery_date",
                    "delivery_city",
                    "delivery_address",
                    "invoice_number",
                    "order_1c_number",
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
            "Перевозчик",
            {"fields": ("carrier",)},
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
    actions = ["regenerate_qr_codes"]

    def get_sender_display(self, obj):
        """Отображение отправителя в списке"""
        if obj.sender:
            return obj.sender.name
        return "Не указан"

    get_sender_display.short_description = "Отправитель"

    def get_recipient_display(self, obj):
        """Отображение получателя в списке"""
        if obj.recipient:
            return obj.recipient.name
        return "Не указан"

    get_recipient_display.short_description = "Получатель"

    def get_carrier_display(self, obj):
        """Отображение перевозчика в списке"""
        if obj.carrier:
            return obj.carrier.name
        return "Не указан"

    get_carrier_display.short_description = "Перевозчик"

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


