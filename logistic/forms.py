from django import forms
from django.utils import timezone


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
