from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from logistic.models import DeliveryOrder
from warehouses.models import City, Warehouse


class DailyReportForm(forms.Form):
    """Форма для выбора даты ежедневного отчета"""

    date = forms.DateField(
        label="Дата отчета",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
                "max": timezone.now().date().strftime("%Y-%m-%d"),
            }
        ),
        initial=timezone.now().date(),
    )

    report_type = forms.ChoiceField(
        label="Тип отчета",
        choices=[
            ("delivery", "По доставкам"),
            ("pickup", "По заборам"),
            ("combined", "Комбинированный"),
        ],
        initial="delivery",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    format = forms.ChoiceField(
        label="Формат",
        choices=[
            ("pdf", "PDF"),
            ("excel", "Excel"),
        ],
        initial="pdf",
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class DateRangeReportForm(forms.Form):
    """Форма для выбора периода отчета"""

    start_date = forms.DateField(
        label="Дата начала",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        initial=timezone.now().date(),
    )

    end_date = forms.DateField(
        label="Дата окончания",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        initial=timezone.now().date(),
    )

    report_type = forms.ChoiceField(
        label="Тип отчета",
        choices=[
            ("delivery", "По доставкам"),
            ("pickup", "По заборам"),
        ],
        initial="delivery",
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class EmailSettingsForm(forms.Form):
    """Упрощенная форма для настройки параметров email"""

    email_host = forms.CharField(
        label="Почтовый сервер",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "smtp.yandex.ru"}
        ),
        help_text="Адрес вашего почтового сервера",
    )

    email_port = forms.IntegerField(
        label="Порт",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "587"}),
        initial=587,
        help_text="Обычно 587",
    )

    email_host_user = forms.CharField(
        label="Email для авторизации",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "ваш_email@example.com"}
        ),
        help_text="Ваш полный email адрес",
    )

    email_host_password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "ваш_пароль"}
        ),
        required=False,
        help_text="Пароль от почты или пароль приложения",
    )

    default_from_email = forms.CharField(
        label="Email отправителя",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "noreply@ваш-домен.ru"}
        ),
        help_text="Этот email увидят получатели",
    )

    operator_email = forms.CharField(
        label="Email оператора",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "operator@ваш-домен.ru"}
        ),
        help_text="Для уведомлений о новых заявках",
    )


class DeliveryOrderCreateForm(forms.ModelForm):
    """Форма для создания новой заявки на доставку"""

    class Meta:
        model = DeliveryOrder
        fields = [
            "date",
            "pickup_address",
            "delivery_address",
            "fulfillment",
            "quantity",
            "weight",
            "volume",
            "status",
            "driver_name",
            "driver_phone",
            "vehicle",
            "driver_pass_info",
        ]
        widgets = {
            "date": forms.DateInput(
                attrs={"type": "date", "class": "form-control", "required": "required"}
            ),
            "pickup_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Адрес отправки груза",
                    "required": "required",
                }
            ),
            "delivery_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Адрес доставки груза",
                    "required": "required",
                }
            ),
            "fulfillment": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "min": "1", "required": "required"}
            ),
            "weight": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "В кг",
                    "required": "required",
                }
            ),
            "volume": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "В м³",
                    "required": "required",
                }
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "driver_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "ФИО водителя (опционально)",
                }
            ),
            "driver_phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+7 (XXX) XXX-XX-XX"}
            ),
            "vehicle": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Марка и номер ТС"}
            ),
            "driver_pass_info": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Данные пропуска"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].initial = "submitted"

        # Ограничиваем выбор фулфилмент операторов только операторами
        self.fields["fulfillment"].queryset = User.objects.filter(
            profile__role="operator"
        ).order_by("first_name", "last_name", "username")

    def clean(self):
        cleaned_data = super().clean()
        city = cleaned_data.get("city")
        warehouse = cleaned_data.get("warehouse")
        receiving_warehouse = cleaned_data.get("receiving_warehouse")
        delivery_address = cleaned_data.get("delivery_address")

        # Проверка, что склады принадлежат выбранному городу
        if city:
            if warehouse and warehouse.city != city:
                raise forms.ValidationError(
                    "Выбранный склад отправки не принадлежит выбранному городу."
                )
            if receiving_warehouse and receiving_warehouse.city != city:
                raise forms.ValidationError(
                    "Выбранный склад приемки не принадлежит выбранному городу."
                )

        # Проверка, что если выбран город, то должен быть выбран склад отправки
        if city and not warehouse:
            raise forms.ValidationError(
                "При выборе города необходимо выбрать склад отправки."
            )

        # Проверка: либо склад приемки, либо адрес доставки
        if not receiving_warehouse and not delivery_address:
            raise forms.ValidationError(
                "Укажите либо склад приемки, либо адрес доставки."
            )

        # Проверка, что не выбраны одновременно склад приемки и адрес доставки
        if receiving_warehouse and delivery_address:
            raise forms.ValidationError(
                "Выберите либо склад приемки, либо адрес доставки, но не оба варианта одновременно."
            )

        # Проверка, что склады отправки и приемки не одинаковые
        if warehouse and receiving_warehouse and warehouse.id == receiving_warehouse.id:
            raise forms.ValidationError(
                "Склад отправки и склад приемки не могут быть одинаковыми."
            )

        return cleaned_data
