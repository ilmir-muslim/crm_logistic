import django_filters
from .models import DeliveryOrder
from django.db.models import Q
from utils.text_utils import normalize_search_text


class DeliveryOrderFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(field_name="date", lookup_expr="exact")
    date__gte = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="Дата от"
    )
    date__lte = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="Дата до"
    )

    city = django_filters.CharFilter(method="filter_city_ignore_case", label="Город")

    warehouse = django_filters.CharFilter(
        method="filter_warehouse_ignore_case", label="Склад отправки"
    )

    fulfillment = django_filters.CharFilter(
        method="filter_fulfillment_ignore_case", label="Фулфилмент оператор"
    )

    status = django_filters.ChoiceFilter(
        choices=DeliveryOrder.STATUS_CHOICES, empty_label="Все статусы"
    )

    class Meta:
        model = DeliveryOrder
        fields = []

    def filter_city_ignore_case(self, queryset, name, value):
        if value:
            normalized_value = normalize_search_text(value)
            return queryset.filter(
                Q(city__icontains=normalized_value)
                | Q(city__icontains=value.title())
                | Q(city__icontains=value.upper())
            )
        return queryset

    def filter_warehouse_ignore_case(self, queryset, name, value):
        if value:
            normalized_value = normalize_search_text(value)
            return queryset.filter(
                Q(warehouse__icontains=normalized_value)
                | Q(warehouse__icontains=value.title())
                | Q(warehouse__icontains=value.upper())
            )
        return queryset

    def filter_fulfillment_ignore_case(self, queryset, name, value):
        if value:
            normalized_value = normalize_search_text(value)
            return queryset.filter(
                Q(fulfillment__icontains=normalized_value)
                | Q(fulfillment__icontains=value.title())
                | Q(fulfillment__icontains=value.upper())
            )
        return queryset
