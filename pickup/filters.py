import django_filters
from .models import PickupOrder


class PickupOrderFilter(django_filters.FilterSet):
    pickup_date = django_filters.DateFilter(
        field_name="pickup_date", lookup_expr="exact", label="Дата забора"
    )
    pickup_date__gte = django_filters.DateFilter(
        field_name="pickup_date", lookup_expr="gte", label="Дата забора от"
    )
    pickup_date__lte = django_filters.DateFilter(
        field_name="pickup_date", lookup_expr="lte", label="Дата забора до"
    )

    client_name = django_filters.CharFilter(
        field_name="client_name", lookup_expr="icontains", label="Клиент"
    )

    status = django_filters.ChoiceFilter(
        choices=PickupOrder.STATUS_CHOICES, empty_label="Все статусы"
    )

    has_delivery = django_filters.BooleanFilter(
        field_name="delivery_order",
        lookup_expr="isnull",
        exclude=True,
        label="Есть связанная доставка",
    )

    class Meta:
        model = PickupOrder
        fields = ["pickup_date", "client_name", "status", "operator"]
