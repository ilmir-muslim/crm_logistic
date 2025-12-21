from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from pickup.models import PickupOrder
from warehouses.models import City, Warehouse


class ClientOrderForm(forms.ModelForm):
    """Форма заявки на отправку для клиентов"""

    # Новые поля для выбора города и склада
    delivery_city = forms.ModelChoiceField(
        queryset=City.objects.all(),
        label="Город доставки *",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Выберите город назначения доставки",
    )

    # Склад будет выбираться автоматически или оператором
    receiving_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(),
        required=False,
        label="Склад приемки",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Склад, куда будет доставлен груз (опционально)",
    )

    # Дополнительное поле для согласия
    privacy_policy = forms.BooleanField(
        label="Я согласен на обработку персональных данных *",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        error_messages={
            "required": "Необходимо согласие с обработкой персональных данных"
        },
    )
    client_email = forms.EmailField(
        required=False,
        label="Email",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "email@example.com"}
        ),
    )
    class Meta:
        model = PickupOrder
        fields = [
            "delivery_address",
            "marketplace",
            "desired_delivery_date",
            "pickup_address",
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
                    "placeholder": "Улица, дом, квартира/офис, этаж, наличие лифта",
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
            "delivery_city": "Город доставки *",
            "delivery_address": "Адрес доставки (улица, дом) *",
            "marketplace": "Маркетплейс *",
            "desired_delivery_date": "Желаемая дата поставки *",
            "pickup_address": "Адрес забора груза *",
            "client_company": "Наименование контрагента *",
            "client_name": "Контактное лицо *",
            "client_phone": "Телефон для связи *",
            "client_email": "Email *",
            "quantity": "Количество мест *",
            "volume": "Общий объем (м³) *",
            "weight": "Общий вес (кг) *",
            "order_1c_number": "№ заказа в 1С",
            "cargo_description": "Комментарий к заказу",
            "receiving_warehouse": "Склад приемки (опционально)",
        }

        help_texts = {
            "delivery_city": "Выберите город доставки из списка",
            "pickup_address": "Укажите город, улицу, дом, этаж, наличие лифта",
            "delivery_address": "Укажите улицу, дом, квартиру/офис",
            "client_email": "На этот email будет отправлено подтверждение заявки",
            "quantity": "Общее количество коробок/мест",
            "volume": "Укажите общий объем груза в кубических метрах",
            "weight": "Укажите общий вес груза в килограммах",
            "order_1c_number": "Номер заказа в вашей системе 1С (если есть)",
            "cargo_description": "Любая дополнительная информация о заказе",
            "receiving_warehouse": "Если оставить пустым, склад выберет оператор",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Сортируем города по названию
        self.fields["delivery_city"].queryset = City.objects.all().order_by("name")

        # Склады - только активные
        self.fields["receiving_warehouse"].queryset = Warehouse.objects.filter(
            city__warehouses__isnull=False
        ).distinct().order_by("city__name", "name")
        
        self.fields["receiving_warehouse"].label_from_instance = (
            lambda obj: f"{obj.name} ({obj.city.name})"
        )

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

    def clean(self):
        """Дополнительная валидация"""
        cleaned_data = super().clean()

        # Проверяем, что если выбран склад, то он активен
        warehouse = cleaned_data.get("receiving_warehouse")
        if warehouse:
            if not warehouse.is_open_now:
                raise ValidationError(
                    "Выбранный склад не работает в настоящее время. "
                    "Выберите другой склад или оставьте поле пустым."
                )

        return cleaned_data

    def save(self, commit=True):
        """Сохранение формы с установкой дополнительных полей"""
        instance = super().save(commit=False)

        # Автоматически устанавливаем город в адрес доставки
        delivery_city = self.cleaned_data.get("delivery_city")
        delivery_address = self.cleaned_data.get("delivery_address", "")

        if delivery_city:
            # Форматируем полный адрес: город, улица, дом...
            instance.delivery_address = f"{delivery_city.name}, {delivery_address}"
            instance.delivery_city = delivery_city

        if commit:
            instance.save()

        return instance
