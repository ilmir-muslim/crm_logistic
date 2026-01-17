from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from pickup.models import PickupOrder
from logistic.models import DeliveryOrder
from warehouses.models import City, Warehouse, WarehouseSchedule
from counterparties.models import Counterparty


class ClientPickupForm(forms.ModelForm):
    """Форма заявки на ЗАБОР (получение) груза"""

    # Поля для связи с контрагентом (клиентом)
    client_counterparty_id = forms.IntegerField(
        required=False, widget=forms.HiddenInput()
    )

    # Основные поля для клиента
    client_type = forms.ChoiceField(
        choices=[
            ("legal", "Юридическое лицо (ООО, АО)"),
            ("entrepreneur", "Индивидуальный предприниматель (ИП)"),
            ("individual", "Физическое лицо"),
            ("self_employed", "Самозанятый"),
        ],
        label="Тип клиента *",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    client_company = forms.CharField(
        label="Наименование компании *",
        max_length=200,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": 'Например: ООО "Ромашка"'}
        ),
    )

    client_name = forms.CharField(
        label="Контактное лицо *",
        max_length=200,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "ФИО контактного лица"}
        ),
    )

    client_inn = forms.CharField(
        label="ИНН клиента",
        max_length=12,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_kpp = forms.CharField(
        label="КПП клиента",
        max_length=9,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_ogrn = forms.CharField(
        label="ОГРН клиента",
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_address = forms.CharField(
        label="Адрес клиента *",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    client_phone = forms.CharField(
        label="Телефон для связи *",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "type": "tel",
                "placeholder": "+7 (999) 123-45-67",
            }
        ),
    )

    client_email = forms.EmailField(
        label="Email клиента",
        required=False,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "email@example.com"}
        ),
    )

    client_contact_person = forms.CharField(
        label="Контактное лицо",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_director_name = forms.CharField(
        label="ФИО руководителя",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_passport_series = forms.CharField(
        label="Серия паспорта",
        max_length=4,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_passport_number = forms.CharField(
        label="Номер паспорта",
        max_length=6,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_passport_issued_by = forms.CharField(
        label="Кем выдан паспорт",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    client_passport_issued_date = forms.DateField(
        label="Дата выдачи паспорта",
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    client_bank_name = forms.CharField(
        label="Банк клиента",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_bank_account = forms.CharField(
        label="Расчетный счет клиента",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    # Оригинальные поля формы
    delivery_city = forms.ModelChoiceField(
        queryset=City.objects.all(),
        label="Город доставки *",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Выберите город назначения доставки",
    )

    receiving_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(),
        required=False,
        label="Склад приемки",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Склад, куда будет доставлен груз",
    )

    pickup_time_from = forms.TimeField(
        required=False,
        label="Время забора от",
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        help_text="Начало интервала забора (необязательно)",
    )

    pickup_time_to = forms.TimeField(
        required=False,
        label="Время забора до",
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        help_text="Конец интервала забора (необязательно)",
    )

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
            "delivery_address",
            "marketplace",
            "desired_delivery_date",
            "pickup_address",
            "quantity",
            "volume",
            "weight",
            "order_1c_number",
            "cargo_description",
            "pickup_time_from",
            "pickup_time_to",
            "client_company",
            "client_name",
            "client_phone",
            "client_email",
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
            "pickup_time_from": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                    "placeholder": "Например: 09:00",
                }
            ),
            "pickup_time_to": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                    "placeholder": "Например: 18:00",
                }
            ),
            "client_company": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": 'Например: ООО "Ромашка"',
                }
            ),
            "client_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "ФИО контактного лица",
                }
            ),
            "client_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+7 (999) 123-45-67",
                    "type": "tel",
                }
            ),
            "client_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "email@example.com",
                }
            ),
        }

        labels = {
            "delivery_city": "Город доставки *",
            "delivery_address": "Адрес доставки (улица, дом) *",
            "marketplace": "Маркетплейс *",
            "desired_delivery_date": "Желаемая дата поставки *",
            "pickup_address": "Адрес забора груза *",
            "quantity": "Количество мест *",
            "volume": "Общий объем (м³) *",
            "weight": "Общий вес (кг) *",
            "order_1c_number": "№ заказа в 1С",
            "cargo_description": "Комментарий к заказу",
            "receiving_warehouse": "Склад приемки (опционально)",
            "pickup_time_from": "Время забора от (необязательно)",
            "pickup_time_to": "Время забора до (необязательно)",
            "client_company": "Наименование компании *",
            "client_name": "Контактное лицо *",
            "client_phone": "Телефон для связи *",
            "client_email": "Email",
        }

        help_texts = {
            "delivery_city": "Выберите город доставки из списка",
            "pickup_address": "Укажите город, улицу, дом, этаж, наличие лифта",
            "delivery_address": "Укажите улицу, дом, квартиру/офис",
            "quantity": "Общее количество коробок/мест",
            "volume": "Укажите общий объем груза в кубических метрах",
            "weight": "Укажите общий вес груза в килограммах",
            "order_1c_number": "Номер заказа в вашей системе 1С (если есть)",
            "cargo_description": "Любая дополнительная информация о заказе",
            "receiving_warehouse": "Если оставить пустым, склад выберет оператор",
            "pickup_time_from": "Начало интервала забора (например, 09:00)",
            "pickup_time_to": "Конец интервала забора (например, 18:00)",
            "client_company": "Полное наименование компании или ИП",
            "client_name": "ФИО ответственного лица",
            "client_phone": "Номер для оперативной связи",
            "client_email": "На этот email придет подтверждение (если указан)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["delivery_city"].queryset = City.objects.all().order_by("name")

        self.fields["receiving_warehouse"].queryset = (
            Warehouse.objects.filter(city__warehouses__isnull=False)
            .distinct()
            .order_by("city__name", "name")
        )

        self.fields["receiving_warehouse"].label_from_instance = (
            lambda obj: f"{obj.name} ({obj.city.name})"
        )

        self.fields["quantity"].initial = 1

        today = timezone.now().date()

        self.fields["desired_delivery_date"].widget.attrs["min"] = today.strftime(
            "%Y-%m-%d"
        )

        max_date = today + timedelta(days=60)
        self.fields["desired_delivery_date"].widget.attrs["max"] = max_date.strftime(
            "%Y-%m-%d"
        )

        self.fields["desired_delivery_date"].widget.attrs[
            "onfocus"
        ] = "showScheduleHint()"
        self.fields["desired_delivery_date"].widget.attrs[
            "onchange"
        ] = "checkDateAvailability()"

        default_date = today + timedelta(days=1)

        for i in range(1, 8):
            check_date = today + timedelta(days=i)
            if check_date.weekday() < 5:
                default_date = check_date
                break

        self.fields["desired_delivery_date"].initial = default_date

    def clean(self):
        cleaned_data = super().clean()

        pickup_time_from = cleaned_data.get("pickup_time_from")
        pickup_time_to = cleaned_data.get("pickup_time_to")

        if pickup_time_from and pickup_time_to:
            if pickup_time_from >= pickup_time_to:
                raise ValidationError(
                    {"pickup_time_to": "Время 'до' должно быть позже времени 'от'"}
                )

        receiving_warehouse = cleaned_data.get("receiving_warehouse")
        desired_delivery_date = cleaned_data.get("desired_delivery_date")

        if receiving_warehouse and desired_delivery_date:
            day_of_week = desired_delivery_date.isoweekday()

            try:
                schedule = WarehouseSchedule.objects.get(
                    warehouse=receiving_warehouse, day_of_week=day_of_week
                )

                if not schedule.is_working:
                    raise ValidationError(
                        {
                            "desired_delivery_date": f"Склад {receiving_warehouse.name} не работает в выбранный день ({desired_delivery_date.strftime('%A')})."
                        }
                    )

                from django.utils import timezone

                if desired_delivery_date < timezone.now().date():
                    raise ValidationError(
                        {"desired_delivery_date": "Нельзя выбрать дату в прошлом."}
                    )

                if desired_delivery_date == timezone.now().date():
                    current_time = timezone.now().time()
                    if (
                        schedule.pickup_cutoff_time
                        and current_time > schedule.pickup_cutoff_time
                    ):
                        raise ValidationError(
                            {
                                "desired_delivery_date": f"Крайний срок приема заявок на сегодня ({schedule.pickup_cutoff_time.strftime('%H:%M')}) уже прошел."
                            }
                        )

            except WarehouseSchedule.DoesNotExist:
                raise ValidationError(
                    {
                        "desired_delivery_date": f"Склад {receiving_warehouse.name} не работает в выбранный день ({desired_delivery_date.strftime('%A')})."
                    }
                )

        return cleaned_data

    def save(self, commit=True):
        """Переопределяем сохранение для обработки контрагента"""
        instance = super().save(commit=False)

        # Обработка клиента (контрагента)
        client_counterparty_id = self.cleaned_data.get("client_counterparty_id")
        if client_counterparty_id:
            # Используем существующего контрагента
            try:
                client = Counterparty.objects.get(
                    id=client_counterparty_id, is_active=True
                )
                # Обновляем данные контрагента на случай изменений
                self._update_counterparty(client, "client")
            except Counterparty.DoesNotExist:
                client = self._create_counterparty("client")
        else:
            # Создаем нового контрагента
            client = self._create_counterparty("client")

        # Сохраняем связь с контрагентом в заметках
        if client:
            instance.notes = f"""
            Клиент: {client.name} (ID: {client.id})
            ИНН: {client.inn or 'Не указан'}
            Маркетплейс: {self.cleaned_data.get('marketplace', 'Не указан')}
            
            {instance.notes or ''}
            """

        if commit:
            instance.save()

        return instance

    def _create_counterparty(self, prefix):
        """Создает нового контрагента"""
        counterparty_type = self.cleaned_data.get(f"{prefix}_type", "legal")
        name = self.cleaned_data.get(f"{prefix}_company", "")

        if not name:
            return None

        counterparty = Counterparty.objects.create(
            type=counterparty_type,
            name=name,
            inn=self.cleaned_data.get(f"{prefix}_inn", ""),
            kpp=self.cleaned_data.get(f"{prefix}_kpp", ""),
            ogrn=self.cleaned_data.get(f"{prefix}_ogrn", ""),
            address=self.cleaned_data.get(f"{prefix}_address", ""),
            phone=self.cleaned_data.get(f"{prefix}_phone", ""),
            email=self.cleaned_data.get(f"{prefix}_email", ""),
            contact_person=self.cleaned_data.get(f"{prefix}_contact_person", ""),
            director_name=self.cleaned_data.get(f"{prefix}_director_name", ""),
            passport_series=self.cleaned_data.get(f"{prefix}_passport_series", ""),
            passport_number=self.cleaned_data.get(f"{prefix}_passport_number", ""),
            passport_issued_by=self.cleaned_data.get(
                f"{prefix}_passport_issued_by", ""
            ),
            passport_issued_date=self.cleaned_data.get(
                f"{prefix}_passport_issued_date", ""
            ),
            bank_name=self.cleaned_data.get(f"{prefix}_bank_name", ""),
            bank_account=self.cleaned_data.get(f"{prefix}_bank_account", ""),
            is_customer=True,
            notes=f"Создано через форму забора груза",
        )

        return counterparty

    def _update_counterparty(self, counterparty, prefix):
        """Обновляет данные существующего контрагента"""
        counterparty.name = self.cleaned_data.get(
            f"{prefix}_company", counterparty.name
        )
        counterparty.inn = self.cleaned_data.get(f"{prefix}_inn", counterparty.inn)
        counterparty.address = self.cleaned_data.get(
            f"{prefix}_address", counterparty.address
        )
        counterparty.phone = self.cleaned_data.get(
            f"{prefix}_phone", counterparty.phone
        )
        counterparty.email = self.cleaned_data.get(
            f"{prefix}_email", counterparty.email
        )
        counterparty.save()


class ClientDeliveryForm(forms.ModelForm):
    """Форма заявки на ОТПРАВКУ (доставку) груза"""

    # Поля для связи с контрагентами
    client_counterparty_id = forms.IntegerField(
        required=False, widget=forms.HiddenInput()
    )

    # Основные поля для клиента
    client_type = forms.ChoiceField(
        choices=[
            ("legal", "Юридическое лицо (ООО, АО)"),
            ("entrepreneur", "Индивидуальный предприниматель (ИП)"),
            ("individual", "Физическое лицо"),
            ("self_employed", "Самозанятый"),
        ],
        label="Тип клиента *",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    client_company = forms.CharField(
        label="Наименование компании *",
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": 'Например: ООО "Ромашка"',
            }
        ),
    )

    client_name = forms.CharField(
        label="Контактное лицо *",
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "ФИО контактного лица",
            }
        ),
    )

    client_inn = forms.CharField(
        label="ИНН клиента",
        max_length=12,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_kpp = forms.CharField(
        label="КПП клиента",
        max_length=9,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_ogrn = forms.CharField(
        label="ОГРН клиента",
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_address = forms.CharField(
        label="Адрес клиента *",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        required=False,
    )

    client_phone = forms.CharField(
        label="Телефон для связи *",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "+7 (999) 123-45-67",
                "type": "tel",
            }
        ),
    )

    client_email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "email@example.com",
            }
        ),
    )

    client_contact_person = forms.CharField(
        label="Контактное лицо (дополнительно)",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_director_name = forms.CharField(
        label="ФИО руководителя",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_passport_series = forms.CharField(
        label="Серия паспорта",
        max_length=4,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_passport_number = forms.CharField(
        label="Номер паспорта",
        max_length=6,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_passport_issued_by = forms.CharField(
        label="Кем выдан паспорт",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    client_passport_issued_date = forms.DateField(
        label="Дата выдачи паспорта",
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    client_bank_name = forms.CharField(
        label="Банк клиента",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    client_bank_account = forms.CharField(
        label="Расчетный счет клиента",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    # Оригинальные поля формы
    city = forms.ModelChoiceField(
        queryset=City.objects.all(),
        label="Город назначения *",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Город, куда нужно доставить груз",
    )

    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(),
        label="Склад отправки *",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Склад, откуда будет отправлен груз",
    )

    sender = forms.ModelChoiceField(
        queryset=Counterparty.objects.filter(is_active=True),
        required=False,
        widget=forms.HiddenInput(),
        label="Отправитель",
    )

    recipient = forms.ModelChoiceField(
        queryset=Counterparty.objects.filter(is_active=True),
        required=False,
        widget=forms.HiddenInput(),
        label="Получатель",
    )

    privacy_policy = forms.BooleanField(
        label="Я согласен на обработку персональных данных *",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        error_messages={
            "required": "Необходимо согласие с обработкой персональных данных"
        },
    )

    class Meta:
        model = DeliveryOrder
        fields = [
            "date",
            "city",
            "warehouse",
            "fulfillment",
            "quantity",
            "weight",
            "volume",
            "driver_pass_info",
            "sender",
            "recipient",
            "client_company",
            "client_name",
            "client_phone",
            "client_email",
        ]

        widgets = {
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "min": timezone.now().date().strftime("%Y-%m-%d"),
                }
            ),
            "fulfillment": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Фулфилмент Царицыно",
                }
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
            "driver_pass_info": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Данные пропуска водителя (если требуются)",
                }
            ),
            "client_company": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": 'Например: ООО "Ромашка"',
                }
            ),
            "client_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "ФИО контактного лица",
                }
            ),
            "client_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+7 (999) 123-45-67",
                    "type": "tel",
                }
            ),
            "client_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "email@example.com",
                }
            ),
        }

        labels = {
            "date": "Дата доставки *",
            "city": "Город назначения *",
            "warehouse": "Склад отправки *",
            "fulfillment": "Фулфилмент оператор *",
            "quantity": "Количество мест *",
            "weight": "Вес (кг) *",
            "volume": "Объем (м³) *",
            "driver_pass_info": "Данные пропуска",
            "sender": "Отправитель",
            "recipient": "Получатель",
            "client_company": "Наименование компании *",
            "client_name": "Контактное лицо *",
            "client_phone": "Телефон для связи *",
            "client_email": "Email",
        }

        help_texts = {
            "date": "Выберите дату доставки",
            "city": "Город, куда нужно доставить груз",
            "warehouse": "Склад, откуда будет отправлен груз",
            "fulfillment": "Оператор фулфилмента",
            "quantity": "Количество коробок/мест",
            "weight": "Общий вес груза в килограммах",
            "volume": "Общий объем груза в кубических метрах",
            "driver_pass_info": "Номер пропуска, серия, срок действия",
            "sender": "Контрагент, который отправляет груз",
            "recipient": "Контрагент, который получает груз",
            "client_company": "Полное наименование компании или ИП",
            "client_name": "ФИО ответственного лица",
            "client_phone": "Номер для оперативной связи",
            "client_email": "На этот email придет подтверждение (если указан)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = timezone.now().date()
        self.fields["date"].initial = today
        self.fields["quantity"].initial = 1
        self.fields["fulfillment"].initial = "Фулфилмент Царицыно"

        self.fields["city"].queryset = City.objects.all().order_by("name")
        self.fields["warehouse"].queryset = (
            Warehouse.objects.filter(city__warehouses__isnull=False)
            .distinct()
            .order_by("city__name", "name")
        )

        self.fields["warehouse"].label_from_instance = (
            lambda obj: f"{obj.name} ({obj.city.name})"
        )

        self.fields["sender"].queryset = Counterparty.objects.filter(
            is_active=True
        ).order_by("name")
        self.fields["recipient"].queryset = Counterparty.objects.filter(
            is_active=True
        ).order_by("name")

    def clean(self):
        cleaned_data = super().clean()

        warehouse = cleaned_data.get("warehouse")
        date = cleaned_data.get("date")

        if warehouse and date:
            day_of_week = date.isoweekday()

            try:
                schedule = WarehouseSchedule.objects.get(
                    warehouse=warehouse, day_of_week=day_of_week
                )

                if not schedule.is_working:
                    raise ValidationError(
                        {
                            "date": f"Склад {warehouse.name} не работает в выбранный день ({date.strftime('%A')})."
                        }
                    )

                if date < timezone.now().date():
                    raise ValidationError({"date": "Нельзя выбрать дату в прошлом."})

                if date == timezone.now().date():
                    current_time = timezone.now().time()
                    if (
                        schedule.delivery_cutoff_time
                        and current_time > schedule.delivery_cutoff_time
                    ):
                        raise ValidationError(
                            {
                                "date": f"Крайний срок приема заявок на доставку сегодня ({schedule.delivery_cutoff_time.strftime('%H:%M')}) уже прошел."
                            }
                        )

            except WarehouseSchedule.DoesNotExist:
                raise ValidationError(
                    {
                        "date": f"Склад {warehouse.name} не работает в выбранный день ({date.strftime('%A')})."
                    }
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        city_obj = self.cleaned_data.get("city")
        if city_obj:
            instance.city = city_obj.name

        warehouse_obj = self.cleaned_data.get("warehouse")
        if warehouse_obj:
            instance.warehouse = warehouse_obj.name

        instance.status = "submitted"

        # Обработка клиента (контрагента)
        client_counterparty_id = self.cleaned_data.get("client_counterparty_id")
        if client_counterparty_id:
            # Используем существующего контрагента
            try:
                client = Counterparty.objects.get(
                    id=client_counterparty_id, is_active=True
                )
                # Обновляем данные контрагента на случай изменений
                self._update_counterparty(client, "client")
            except Counterparty.DoesNotExist:
                client = self._create_counterparty("client")
        else:
            # Создаем нового контрагента
            client = self._create_counterparty("client")

        if commit:
            instance.save()

        return instance

    def _create_counterparty(self, prefix):
        """Создает нового контрагента для доставки"""
        counterparty_type = self.cleaned_data.get(f"{prefix}_type", "legal")
        name = self.cleaned_data.get(f"{prefix}_company", "")

        if not name:
            return None

        counterparty = Counterparty.objects.create(
            type=counterparty_type,
            name=name,
            inn=self.cleaned_data.get(f"{prefix}_inn", ""),
            kpp=self.cleaned_data.get(f"{prefix}_kpp", ""),
            ogrn=self.cleaned_data.get(f"{prefix}_ogrn", ""),
            address=self.cleaned_data.get(f"{prefix}_address", ""),
            phone=self.cleaned_data.get(f"{prefix}_phone", ""),
            email=self.cleaned_data.get(f"{prefix}_email", ""),
            contact_person=self.cleaned_data.get(f"{prefix}_contact_person", ""),
            director_name=self.cleaned_data.get(f"{prefix}_director_name", ""),
            passport_series=self.cleaned_data.get(f"{prefix}_passport_series", ""),
            passport_number=self.cleaned_data.get(f"{prefix}_passport_number", ""),
            passport_issued_by=self.cleaned_data.get(
                f"{prefix}_passport_issued_by", ""
            ),
            passport_issued_date=self.cleaned_data.get(
                f"{prefix}_passport_issued_date", ""
            ),
            bank_name=self.cleaned_data.get(f"{prefix}_bank_name", ""),
            bank_account=self.cleaned_data.get(f"{prefix}_bank_account", ""),
            is_customer=True,
            notes=f"Создано через форму доставки груза",
        )

        return counterparty

    def _update_counterparty(self, counterparty, prefix):
        """Обновляет данные существующего контрагента"""
        counterparty.name = self.cleaned_data.get(
            f"{prefix}_company", counterparty.name
        )
        counterparty.inn = self.cleaned_data.get(f"{prefix}_inn", counterparty.inn)
        counterparty.address = self.cleaned_data.get(
            f"{prefix}_address", counterparty.address
        )
        counterparty.phone = self.cleaned_data.get(
            f"{prefix}_phone", counterparty.phone
        )
        counterparty.email = self.cleaned_data.get(
            f"{prefix}_email", counterparty.email
        )
        counterparty.save()
