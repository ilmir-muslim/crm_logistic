from django import forms
from .models import WarehouseSchedule


class WarehouseScheduleForm(forms.ModelForm):
    """Форма для расписания работы с улучшенным виджетом времени"""

    # Переопределяем поля времени с использованием HTML5 виджета
    opening_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"type": "time", "class": "vTimeField", "step": "300"}  # шаг 5 минут
        ),
        required=False,
    )

    closing_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"type": "time", "class": "vTimeField", "step": "300"}
        ),
        required=False,
    )

    break_start = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"type": "time", "class": "vTimeField", "step": "300"}
        ),
        required=False,
    )

    break_end = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"type": "time", "class": "vTimeField", "step": "300"}
        ),
        required=False,
    )

    pickup_cutoff_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"type": "time", "class": "vTimeField", "step": "300"}
        ),
        required=False,
    )

    delivery_cutoff_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"type": "time", "class": "vTimeField", "step": "300"}
        ),
        required=False,
    )

    class Meta:
        model = WarehouseSchedule
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "day_of_week" in self.fields:
            instance = kwargs.get("instance")
            if instance:
                self.fields["day_of_week"].widget.attrs["readonly"] = True
                self.fields["day_of_week"].help_text = (
                    f"День недели: {instance.get_day_of_week_display()}"
                )
            self.fields["day_of_week"].required = False
