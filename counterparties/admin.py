from django.contrib import admin
from .models import Counterparty


@admin.register(Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "type",
        "inn",
        "address",
        "phone",
        "is_active",
        "created_at",
    ]
    list_filter = [
        "type",
        "is_active",
        "is_supplier",
        "is_customer",
        "is_carrier",
        "created_at",
    ]
    search_fields = [
        "name",
        "full_name",
        "inn",
        "kpp",
        "ogrn",
        "phone",
        "email",
        "address",
    ]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "type",
                    "name",
                    "full_name",
                    ("phone", "email"),
                    ("address", "actual_address"),
                )
            },
        ),
        (
            "Реквизиты",
            {
                "fields": (
                    ("inn", "kpp"),
                    "ogrn",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Дополнительная информация",
            {
                "fields": (
                    "director_name",
                    "contact_person",
                    ("passport_series", "passport_number"),
                    ("passport_issued_by", "passport_issued_date"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Банковские реквизиты",
            {
                "fields": (
                    "bank_name",
                    "bank_account",
                    ("bank_bik", "bank_correspondent_account"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Статусы",
            {
                "fields": (
                    "is_active",
                    "is_supplier",
                    "is_customer",
                    "is_carrier",
                )
            },
        ),
        (
            "Системная информация",
            {
                "fields": (
                    "notes",
                    "created_by",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
