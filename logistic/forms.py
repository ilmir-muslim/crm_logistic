from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from logistic.models import DeliveryOrder
from warehouses.models import City, Warehouse
from counterparties.models import Counterparty


class LogisticModelChoiceField(forms.ModelChoiceField):
    """Кастомное поле для выбора логиста с отображением полного имени"""

    def label_from_instance(self, obj):
        """Возвращает полное имя пользователя или логин, если имя отсутствует"""
        full_name = obj.get_full_name()
        if full_name and full_name.strip():
            return full_name
        return obj.username


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

    pickup_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
        label="Склад отправки",
    )

    delivery_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
        label="Склад доставки",
    )

    new_sender_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введите наименование нового отправителя",
            }
        ),
        label="Новый отправитель",
    )
    new_sender_type = forms.ChoiceField(
        required=False,
        choices=[("", "Выберите тип")] + Counterparty.TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Тип нового отправителя",
    )
    new_sender_address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Адрес нового отправителя",
            }
        ),
        label="Адрес нового отправителя",
    )

    new_recipient_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введите наименование нового получателя",
            }
        ),
        label="Новый получатель",
    )
    new_recipient_type = forms.ChoiceField(
        required=False,
        choices=[("", "Выберите тип")] + Counterparty.TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Тип нового получателя",
    )
    new_recipient_address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Адрес нового получателя",
            }
        ),
        label="Адрес нового получателя",
    )

    class Meta:
        model = DeliveryOrder
        fields = [
            "date",
            "sender",
            "pickup_address",
            "pickup_warehouse",
            "recipient",
            "delivery_address",
            "delivery_warehouse",
            "logistic",
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
            "sender": forms.Select(
                attrs={
                    "class": "form-select counterparty-select",
                    "data-counterparty-type": "sender",
                }
            ),
            "pickup_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Адрес отправки (если отправитель не выбран)",
                }
            ),
            "recipient": forms.Select(
                attrs={
                    "class": "form-select counterparty-select",
                    "data-counterparty-type": "recipient",
                }
            ),
            "delivery_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Адрес доставки (если получатель не выбран)",
                }
            ),
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
        labels = {
            "sender": "Отправитель (контрагент)",
            "pickup_address": "Адрес отправки (вручную)",
            "recipient": "Получатель (контрагент)",
            "delivery_address": "Адрес доставки (вручную)",
            "logistic": "Логист",
        }
        help_texts = {
            "sender": "Выберите существующего контрагента или создайте нового ниже",
            "recipient": "Выберите существующего контрагента или создайте нового ниже",
            "pickup_address": "Заполняется, если отправитель не выбран из списка контрагентов",
            "delivery_address": "Заполняется, если получатель не выбран из списка контрагентов",
            "logistic": "Логист, ответственный за заявку",
        }

    def __init__(self, *args, **kwargs):
        # Получаем пользователя из kwargs, если он передан
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["status"].initial = "submitted"

        # Используем кастомное поле для выбора логиста
        self.fields["logistic"] = LogisticModelChoiceField(
            queryset=User.objects.filter(profile__role="logistic").order_by(
                "first_name", "last_name", "username"
            ),
            required=False,
            widget=forms.Select(attrs={"class": "form-select"}),
            label="Логист",
            help_text="Логист, ответственный за заявку",
        )

        # Автоматически выбираем текущего пользователя как логиста, если он логист
        if self.user and hasattr(self.user, "profile"):
            if self.user.profile.is_logistic:
                self.fields["logistic"].initial = self.user
            else:
                self.fields["logistic"].initial = None

            # Если пользователь не админ, блокируем поле выбора логиста
            if not self.user.profile.is_admin:
                self.fields["logistic"].widget.attrs["disabled"] = "disabled"
                self.fields["logistic"].widget.attrs["readonly"] = "readonly"
                self.fields["logistic"].help_text = (
                    "Логист выбирается автоматически на основе вашей учетной записи. Изменить может только администратор."
                )
            else:
                # Для админов показываем всех логистов с полными именами
                self.fields["logistic"].help_text = "Выберите логиста"

        self.fields["sender"].queryset = Counterparty.objects.filter(
            is_active=True
        ).order_by("name")
        self.fields["recipient"].queryset = Counterparty.objects.filter(
            is_active=True
        ).order_by("name")

    def clean(self):
        cleaned_data = super().clean()

        sender = cleaned_data.get("sender")
        pickup_address = cleaned_data.get("pickup_address")
        new_sender_name = cleaned_data.get("new_sender_name")
        new_sender_type = cleaned_data.get("new_sender_type")
        new_sender_address = cleaned_data.get("new_sender_address")

        recipient = cleaned_data.get("recipient")
        delivery_address = cleaned_data.get("delivery_address")
        new_recipient_name = cleaned_data.get("new_recipient_name")
        new_recipient_type = cleaned_data.get("new_recipient_type")
        new_recipient_address = cleaned_data.get("new_recipient_address")

        if not sender and not pickup_address and not new_sender_name:
            raise forms.ValidationError(
                "Укажите отправителя: выберите существующего контрагента, "
                "введите адрес вручную или создайте нового контрагента."
            )

        if new_sender_name:
            if not new_sender_type:
                raise forms.ValidationError(
                    "Для нового отправителя необходимо указать тип контрагента."
                )
            if not new_sender_address:
                raise forms.ValidationError(
                    "Для нового отправителя необходимо указать адрес."
                )

        if not recipient and not delivery_address and not new_recipient_name:
            raise forms.ValidationError(
                "Укажите получателя: выберите существующего контрагента, "
                "введите адрес вручную или создайте нового контрагента."
            )

        if new_recipient_name:
            if not new_recipient_type:
                raise forms.ValidationError(
                    "Для нового получателя необходимо указать тип контрагента."
                )
            if not new_recipient_address:
                raise forms.ValidationError(
                    "Для нового получателя необходимо указать адрес."
                )

        return cleaned_data

    def save(self, commit=True, user=None):
        """Сохраняет форму, создавая новых контрагентов при необходимости"""
        instance = super().save(commit=False)

        # Если логист не выбран (для не-админов поле disabled)
        # устанавливаем текущего пользователя как логиста, если он логист
        if (
            not instance.logistic
            and self.user
            and hasattr(self.user, "profile")
            and self.user.profile.is_logistic
        ):
            instance.logistic = self.user

        new_sender_name = self.cleaned_data.get("new_sender_name")
        if new_sender_name:
            sender = Counterparty.objects.create(
                type=self.cleaned_data["new_sender_type"],
                name=new_sender_name,
                address=self.cleaned_data["new_sender_address"],
                created_by=user,
            )
            instance.sender = sender
            instance.pickup_address = ""

        new_recipient_name = self.cleaned_data.get("new_recipient_name")
        if new_recipient_name:
            recipient = Counterparty.objects.create(
                type=self.cleaned_data["new_recipient_type"],
                name=new_recipient_name,
                address=self.cleaned_data["new_recipient_address"],
                created_by=user,
            )
            instance.recipient = recipient
            instance.delivery_address = ""

        if commit:
            instance.save()

        return instance
