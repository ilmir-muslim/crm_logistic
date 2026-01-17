from datetime import datetime, timedelta
from django.utils import timezone
from warehouses.models import WarehouseSchedule


def get_available_dates_for_warehouse(warehouse, days_ahead=30):
    """
    Возвращает список доступных дат для указанного склада
    """
    available_dates = []
    today = timezone.now().date()

    for i in range(days_ahead):
        check_date = today + timedelta(days=i)
        day_of_week = check_date.isoweekday()

        try:
            schedule = WarehouseSchedule.objects.get(
                warehouse=warehouse, day_of_week=day_of_week
            )

            # Проверяем, что день рабочий
            if schedule.is_working:
                # Проверяем, что если это сегодня, то время не прошло
                if check_date == today:
                    current_time = timezone.now().time()
                    if (
                        schedule.pickup_cutoff_time
                        and current_time < schedule.pickup_cutoff_time
                    ):
                        available_dates.append(check_date)
                else:
                    available_dates.append(check_date)

        except WarehouseSchedule.DoesNotExist:
            continue

    return available_dates


def get_next_available_date_for_warehouse(warehouse):
    """
    Возвращает ближайшую доступную дату для склада
    """
    today = timezone.now().date()

    for i in range(60):  # Ищем на 2 месяца вперед
        check_date = today + timedelta(days=i)
        day_of_week = check_date.isoweekday()

        try:
            schedule = WarehouseSchedule.objects.get(
                warehouse=warehouse, day_of_week=day_of_week
            )

            if schedule.is_working:
                if check_date == today:
                    current_time = timezone.now().time()
                    if (
                        schedule.pickup_cutoff_time
                        and current_time < schedule.pickup_cutoff_time
                    ):
                        return check_date
                else:
                    return check_date

        except WarehouseSchedule.DoesNotExist:
            continue

    return None


def is_date_available_for_warehouse(warehouse, date):
    """
    Проверяет, доступна ли дата для указанного склада
    """
    day_of_week = date.isoweekday()

    try:
        schedule = WarehouseSchedule.objects.get(
            warehouse=warehouse, day_of_week=day_of_week
        )

        if not schedule.is_working:
            return False

        # Проверяем, если это сегодня, то время не должно быть позже крайнего срока
        if date == timezone.now().date():
            current_time = timezone.now().time()
            if (
                schedule.pickup_cutoff_time
                and current_time > schedule.pickup_cutoff_time
            ):
                return False

        return True

    except WarehouseSchedule.DoesNotExist:
        return False
