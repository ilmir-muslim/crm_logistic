from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from .models import PickupOrder, Carrier
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
        label="Оператор фулфилмента",
    )

    logistic = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True, profile__role="logistic"),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Логист",
        help_text="Ответственный логист",
    )

    carrier = forms.ModelChoiceField(
        queryset=Carrier.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Перевозчик",
        help_text="Компания перевозчик для забора груза",
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
            "logistic",
            "carrier",
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
                    "class": "form-select",
                    "data-placeholder": "Выберите оператора фулфилмента",
                }
            ),
            "logistic": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-placeholder": "Выберите логиста",
                }
            ),
            "carrier": forms.Select(
                attrs={
                    "class": "form-select",
                    "data-placeholder": "Выберите перевозчика",
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
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        today = timezone.now().date()
        self.fields["pickup_date"].widget.attrs["min"] = today.strftime("%Y-%m-%d")
        self.fields["desired_delivery_date"].widget.attrs["min"] = today.strftime(
            "%Y-%m-%d"
        )

        self.fields["status"].choices = [
            ("ready", "Готова к выдаче"),
            ("payment", "На оплате"),
            ("accepted", "Принята"),
        ]

        # Настройка отображения имен пользователей
        for field_name in ["receiving_operator", "logistic"]:
            self.fields[field_name].label_from_instance = self.get_user_display_name

        # Логика в зависимости от роли пользователя
        if self.user and hasattr(self.user, "profile"):
            user_role = self.user.profile.role

            if user_role == "logistic":
                # Для логиста: поле логиста заполняется автоматически и недоступно для редактирования
                self.fields["logistic"].initial = self.user
                self.fields["logistic"].disabled = True
                self.fields["logistic"].widget.attrs["readonly"] = True
                self.fields["logistic"].help_text = (
                    "Заполняется автоматически (вы логист)"
                )

                # Оператора фулфилмента логист может выбирать
                self.fields["receiving_operator"].queryset = User.objects.filter(
                    is_active=True, profile__role="operator"
                )

            elif user_role == "operator":
                # Для оператора фулфилмента: поле оператора заполняется автоматически и недоступно для редактирования
                self.fields["receiving_operator"].initial = self.user
                self.fields["receiving_operator"].disabled = True
                self.fields["receiving_operator"].widget.attrs["readonly"] = True
                self.fields["receiving_operator"].help_text = (
                    "Заполняется автоматически (вы оператор фулфилмента)"
                )

                # Логиста оператор может выбирать
                self.fields["logistic"].queryset = User.objects.filter(
                    is_active=True, profile__role="logistic"
                )

            elif user_role == "admin":
                # Админ может выбирать и оператора и логиста
                self.fields["receiving_operator"].queryset = User.objects.filter(
                    is_active=True, profile__role__in=["operator", "admin"]
                )
                self.fields["logistic"].queryset = User.objects.filter(
                    is_active=True, profile__role__in=["logistic", "admin"]
                )
                self.fields["receiving_operator"].help_text = (
                    "Выберите оператора фулфилмента"
                )
                self.fields["logistic"].help_text = "Выберите логиста"

    def get_user_display_name(self, user):
        """Возвращает отображаемое имя пользователя (Фамилия Имя)"""
        if user.first_name and user.last_name:
            return f"{user.last_name} {user.first_name}"
        elif user.first_name:
            return user.first_name
        else:
            return user.username

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
        """Сохраняет форму с учетом ролей пользователей"""
        instance = super().save(commit=False)

        # Установка значений в зависимости от роли пользователя
        if self.user and hasattr(self.user, "profile"):
            user_role = self.user.profile.role

            if user_role == "logistic":
                instance.logistic = self.user
            elif user_role == "operator":
                instance.receiving_operator = self.user

        if commit:
            instance.save()
        return instance
