from django.contrib import admin
from .models import DeliveryOrder


@admin.register(DeliveryOrder)
class DeliveryOrderAdmin(admin.ModelAdmin):
    list_display = ["date", "city", "warehouse", "status", "quantity"]
    list_filter = ["city", "warehouse", "status", "date"]
    search_fields = ["city", "driver_name", "vehicle"]
