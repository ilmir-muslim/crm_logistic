from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import re
from pickup.models import PickupOrder


class ClientOrderForm(forms.ModelForm):
    """Форма заявки на отправку для клиентов"""

    # Дополнительное поле для согласия
    privacy_policy = forms.BooleanField(
        label="Я согласен на обработку персональных данных *",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        error_messages={
            "required": "Необходимо согласие с обработкой персональных данных"
        },
    )

    class Meta:
        model = PickupOrder
        fields = [
            "desired_delivery_date",
            "pickup_address",
            "delivery_address",
            "marketplace",
            "client_company",
            "client_name",
            "client_phone",
            "client_email",
            "quantity",
            "volume",
            "weight",
            "order_1c_number",
            "cargo_description",
        ]

        widgets = {
            "desired_delivery_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "min": timezone.now().date().strftime("%Y-%m-%d"),
                }
            ),
            "pickup_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Город, улица, дом, квартира/офис, этаж, наличие лифта",
                }
            ),
            "delivery_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Город, улица, дом, квартира/офис, этаж, наличие лифта",
                }
            ),
            "marketplace": forms.Select(attrs={"class": "form-select"}),
            "client_company": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": 'Например: ООО "Ромашка"',
                }
            ),
            "client_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ФИО контактного лица"}
            ),
            "client_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+7 (999) 123-45-67",
                    "type": "tel",
                }
            ),
            "client_email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "email@example.com"}
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 100,
                    "placeholder": "Например: 5",
                }
            ),
            "volume": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                    "max": "100",
                    "placeholder": "Например: 2.5",
                }
            ),
            "weight": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.1",
                    "min": "0.1",
                    "max": "10000",
                    "placeholder": "Например: 150.5",
                }
            ),
            "order_1c_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Например: 000123456"}
            ),
            "cargo_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Дополнительная информация о грузе, особые требования и т.д.",
                }
            ),
        }

        labels = {
            "desired_delivery_date": "Желаемая дата поставки *",
            "pickup_address": "Адрес забора *",
            "delivery_address": "Адрес доставки *",
            "marketplace": "Маркетплейс *",
            "client_company": "Наименование контрагента *",
            "client_name": "Контактное лицо *",
            "client_phone": "Телефон для связи *",
            "client_email": "Email *",
            "quantity": "Количество мест *",
            "volume": "Общий объем (м³) *",
            "weight": "Общий вес (кг) *",
            "order_1c_number": "№ заказа в 1С",
            "cargo_description": "Комментарий к заказу",
        }

        help_texts = {
            "pickup_address": "Укажите город, улицу, дом, этаж, наличие лифта",
            "delivery_address": "Укажите полный адрес доставки",
            "client_email": "На этот email будет отправлено подтверждение заявки",
            "quantity": "Общее количество коробок/мест",
            "volume": "Укажите общий объем груза в кубических метрах",
            "weight": "Укажите общий вес груза в килограммах",
            "order_1c_number": "Номер заказа в вашей системе 1С (если есть)",
            "cargo_description": "Любая дополнительная информация о заказе",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Устанавливаем начальное значение для quantity
        self.fields["quantity"].initial = 1

        # Устанавливаем минимальную дату
        today = timezone.now().date()
        self.fields["desired_delivery_date"].widget.attrs["min"] = today.strftime(
            "%Y-%m-%d"
        )

        # Устанавливаем начальную дату (через 2 дня)
        default_date = today + timedelta(days=2)
        self.fields["desired_delivery_date"].initial = default_date

        # Отладочная информация
        print("Форма инициализирована")
        print(f"Поля формы: {self.fields.keys()}")

    def clean(self):
        """Дополнительная валидация"""
        cleaned_data = super().clean()
        print("Данные после очистки:", cleaned_data)
        return cleaned_data

    def save(self, commit=True):
        """Сохранение формы с отладочной информацией"""
        instance = super().save(commit=False)
        print("Сохранение экземпляра:", instance)
        print("Данные для сохранения:", self.cleaned_data)

        if commit:
            instance.save()
            print("Экземпляр сохранен с ID:", instance.id)

        return instance

    