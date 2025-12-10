import django_filters

from utils.text_utils import normalize_phone, normalize_search_text
from .models import PickupOrder
from django.db.models import Q


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

    # Кастомный фильтр для поиска по клиенту без учета регистра
    client_name = django_filters.CharFilter(
        method="filter_client_name_ignore_case", label="Клиент"
    )

    # Кастомный фильтр для поиска по адресу без учета регистра
    pickup_address = django_filters.CharFilter(
        method="filter_address_ignore_case", label="Адрес забора"
    )

    # Кастомные фильтры для телефона и email
    client_phone = django_filters.CharFilter(
        method="filter_phone_ignore_case", label="Телефон клиента"
    )

    client_email = django_filters.CharFilter(
        field_name="client_email", lookup_expr="icontains", label="Email клиента"
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
        fields = []

    def filter_client_name_ignore_case(self, queryset, name, value):
        """
        Фильтрация по имени клиента без учета регистра
        """
        if value:
            normalized_value = normalize_search_text(value)
            # Создаем поисковый запрос с разными вариантами регистра
            return queryset.filter(
                Q(client_name__icontains=normalized_value)
                | Q(client_name__icontains=value.title())  # С заглавной буквы
                | Q(client_name__icontains=value.upper())  # В верхнем регистре
            )
        return queryset

    def filter_address_ignore_case(self, queryset, name, value):
        """
        Фильтрация по адресу без учета регистра
        """
        if value:
            normalized_value = normalize_search_text(value)
            return queryset.filter(
                Q(pickup_address__icontains=normalized_value)
                | Q(pickup_address__icontains=value.title())
                | Q(pickup_address__icontains=value.upper())
            )
        return queryset

    def filter_phone_ignore_case(self, queryset, name, value):
        """
        Фильтрация по телефону
        """
        if value:
            normalized_phone = normalize_phone(value)
            if normalized_phone:
                # Ищем по полному номеру или по последним 4-7 цифрам
                return queryset.filter(
                    Q(client_phone__icontains=normalized_phone)
                    | Q(client_phone__icontains=normalized_phone[-4:])
                    | Q(client_phone__icontains=normalized_phone[-7:])
                )
        return queryset
