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
