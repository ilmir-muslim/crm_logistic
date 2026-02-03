from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from .models import PickupOrder
from counterparties.models import Counterparty
from warehouses.models import Warehouse


class PickupOrderForm(forms.ModelForm):
    """Форма для создания и редактирования заявки на забор"""

    pickup_time_from = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        required=False,
        label="Время забора от",
        input_formats=["%H:%M"],
    )

    pickup_time_to = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        required=False,
        label="Время забора до",
        input_formats=["%H:%M"],
    )

    sender = forms.ModelChoiceField(
        queryset=Counterparty.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Отправитель *",
        help_text="Контрагент, который отправляет груз",
    )

    recipient = forms.ModelChoiceField(
        queryset=Counterparty.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Получатель *",
        help_text="Контрагент, который получает груз",
    )

    receiving_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
        label="Склад приемки",
    )

    receiving_operator = forms.ModelChoiceField(
        queryset=User.objects.filter(
            is_active=True, profile__role__in=["operator", "logistic", "admin"]
        ),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Оператор приемки",
    )

    class Meta:
        model = PickupOrder
        fields = [
            "pickup_date",
            "pickup_time_from",
            "pickup_time_to",
            "pickup_address",
            "contact_person",
            "sender",
            "recipient",
            "marketplace",
            "desired_delivery_date",
            "invoice_number",
            "receiving_warehouse",
            "receiving_operator",
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
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "id": "pickupAddress",
                    "placeholder": "Нажмите кнопку 'Выбрать адрес' для заполнения",
                    "required": "required",
                }
            ),
            "contact_person": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "ФИО лица для выдачи груза",
                }
            ),
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
            "receiving_operator": forms.Select(
                attrs={
                    "class": "form-select select2",
                    "data-placeholder": "Выберите оператора приемки",
                }
            ),
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

        today = timezone.now().date()
        self.fields["pickup_date"].widget.attrs["min"] = today.strftime("%Y-%m-%d")
        self.fields["desired_delivery_date"].widget.attrs["min"] = today.strftime(
            "%Y-%m-%d"
        )

        self.fields["status"].choices = [
            ("ready", "Готов к выдаче"),
            ("payment", "На оплате"),
        ]

    def clean_pickup_time_from(self):
        """Очистка поля времени"""
        time = self.cleaned_data.get("pickup_time_from")
        if isinstance(time, str) and time.strip() == "":
            return None
        return time

    def clean_pickup_time_to(self):
        """Очистка поля времени"""
        time = self.cleaned_data.get("pickup_time_to")
        if isinstance(time, str) and time.strip() == "":
            return None
        return time

    def save(self, commit=True):
        """Сохраняет форму"""
        instance = super().save(commit=commit)
        return instance
