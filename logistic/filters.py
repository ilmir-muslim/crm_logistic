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

    city = django_filters.NumberFilter(field_name="city__id", label="Город (ID)")

    city_name = django_filters.CharFilter(
        field_name="city__name", lookup_expr="icontains", label="Название города"
    )

    warehouse = django_filters.NumberFilter(
        field_name="warehouse__id", label="Склад (ID)"
    )

    warehouse_name = django_filters.CharFilter(
        field_name="warehouse__name", lookup_expr="icontains", label="Название склада"
    )

    logistic = django_filters.CharFilter(
        method="filter_logistic_ignore_case", label="Логист"
    )

    status = django_filters.ChoiceFilter(
        choices=DeliveryOrder.STATUS_CHOICES, empty_label="Все статусы"
    )

    class Meta:
        model = DeliveryOrder
        fields = []

    def filter_logistic_ignore_case(self, queryset, name, value):
        if value:
            normalized_value = normalize_search_text(value)
            return queryset.filter(
                Q(logistic__username__icontains=normalized_value)
                | Q(logistic__first_name__icontains=normalized_value)
                | Q(logistic__last_name__icontains=normalized_value)
            )
        return queryset


