import django_filters
from .models import DeliveryOrder


class DeliveryOrderFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(field_name="date", lookup_expr="exact")
    date__gte = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="Дата от"
    )
    date__lte = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="Дата до"
    )

    class Meta:
        model = DeliveryOrder
        fields = ["city", "warehouse", "fulfillment", "status"]
