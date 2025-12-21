from django import forms
from django.utils import timezone
from warehouses.models import City, Warehouse
from .models import PickupOrder
from django.contrib.auth.models import User


class PickupOrderForm(forms.ModelForm):
    """Форма для создания и редактирования заявки на забор"""

    pickup_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"type": "time", "class": "form-control"}, format="%H:%M"
        ),
        required=False,
        label="Время забора",
    )

    # Поле для выбора города доставки
    delivery_city = forms.ModelChoiceField(
        queryset=City.objects.all(),
        required=False,
        label="Город доставки",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Выберите город назначения",
    )

    class Meta:
        model = PickupOrder
        fields = [
            "pickup_date",
            "pickup_time",
            "pickup_address",
            "contact_person",
            "delivery_city",
            "delivery_address",
            "client_name",
            "client_company",
            "client_phone",
            "client_email",
            "marketplace",
            "desired_delivery_date",
            "invoice_number",
            "receiving_warehouse",
            "quantity",
            "weight",
            "volume",
            "cargo_description",
            "special_requirements",
            "status",
            "notes",
        ]

        widgets = {
            "pickup_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "pickup_address": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "contact_person": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "ФИО лица для выдачи груза",
                }
            ),
            "delivery_address": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "client_name": forms.TextInput(attrs={"class": "form-control"}),
            "client_company": forms.TextInput(attrs={"class": "form-control"}),
            "client_phone": forms.TextInput(
                attrs={"class": "form-control", "type": "tel"}
            ),
            "client_email": forms.EmailInput(attrs={"class": "form-control"}),
            "marketplace": forms.Select(attrs={"class": "form-select"}),
            "desired_delivery_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "invoice_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Номер транспортной накладной",
                }
            ),
            "receiving_warehouse": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "weight": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1", "min": "0.1"}
            ),
            "volume": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.01"}
            ),
            "cargo_description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "special_requirements": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Операторы
        operators = User.objects.filter(
            profile__role__in=["operator", "logistic", "admin"]
        ).order_by("username")

        # Активные склады для забора
        self.fields["receiving_warehouse"].queryset = Warehouse.objects.all()
        self.fields["receiving_warehouse"].label_from_instance = (
            lambda obj: f"{obj.name} ({obj.city.name})"
        )

        # Города
        self.fields["delivery_city"].queryset = City.objects.all()
        self.fields["delivery_city"].label_from_instance = lambda obj: f"{obj.name}"

        # Устанавливаем минимальные даты
        today = timezone.now().date()
        self.fields["pickup_date"].widget.attrs["min"] = today.strftime("%Y-%m-%d")
        self.fields["desired_delivery_date"].widget.attrs["min"] = today.strftime(
            "%Y-%m-%d"
        )

        # Устанавливаем начальные значения
        if not self.instance.pk:  # Только для создания
            self.fields["pickup_date"].initial = today
            self.fields["desired_delivery_date"].initial = today + timezone.timedelta(
                days=1
            )

        # Статусы
        self.fields["status"].choices = [
            ("ready", "Готов к выдаче"),
            ("payment", "На оплате"),
        ]
