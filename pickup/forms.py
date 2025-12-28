from django import forms
from django.utils import timezone
from .models import PickupOrder


class PickupOrderForm(forms.ModelForm):
    """Форма для создания и редактирования заявки на забор"""

    pickup_time_from = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"type": "time", "class": "form-control"}, format="%H:%M"
        ),
        required=False,
        label="Время забора от",
    )

    pickup_time_to = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"type": "time", "class": "form-control"}, format="%H:%M"
        ),
        required=False,
        label="Время забора до",
    )

    class Meta:
        model = PickupOrder
        fields = [
            "pickup_date",
            "pickup_time_from",
            "pickup_time_to",
            "pickup_address",
            "contact_person",
            "client_name",
            "client_phone",
            "client_email",
            "marketplace",
            "desired_delivery_date",
            "invoice_number",
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
                    "rows": 2,
                    "readonly": "readonly",
                    "id": "pickupAddress",
                }
            ),
            "contact_person": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "ФИО лица для выдачи груза",
                }
            ),
            "client_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Имя компании или ФИО клиента",
                }
            ),
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

    def save(self, commit=True):
        """Сохраняет форму, автоматически заполняя client_company из client_name"""
        instance = super().save(commit=False)

        # Автоматически заполняем поле client_company из client_name
        if instance.client_name:
            instance.client_company = instance.client_name

        if commit:
            instance.save()

        return instance


