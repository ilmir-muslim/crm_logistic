import json
from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db.models import Prefetch

from .forms import ClientOrderForm
from pickup.models import PickupOrder
from warehouses.models import City, Warehouse, ContainerType, WarehouseSchedule


class ClientOrderFormView(FormView):
    """Представление для формы заявки клиента"""

    template_name = "order_form/client_order_form.html"
    form_class = ClientOrderForm
    success_url = reverse_lazy("order_form_success")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем все города со складами (только активные склады)
        cities = (
            City.objects.filter(warehouses__isnull=False).distinct().order_by("name")
        )

        cities_data = []
        for city in cities:
            # Получаем склады для города с расписаниями
            warehouses = city.warehouses.all().prefetch_related(
                Prefetch(
                    "schedules",
                    queryset=WarehouseSchedule.objects.filter(is_working=True).order_by(
                        "day_of_week"
                    ),
                )
            )

            # Формируем данные о складах
            warehouses_list = []
            for warehouse in warehouses:
                schedules = []
                for schedule in warehouse.schedules.all():
                    schedules.append(
                        {
                            "day_of_week": schedule.get_day_of_week_display(),
                            "opening_time": schedule.opening_time.strftime("%H:%M"),
                            "closing_time": schedule.closing_time.strftime("%H:%M"),
                            "pickup_cutoff_time": schedule.pickup_cutoff_time.strftime(
                                "%H:%M"
                            ),
                            "delivery_cutoff_time": schedule.delivery_cutoff_time.strftime(
                                "%H:%M"
                            ),
                            "max_daily_pickups": schedule.max_daily_pickups,
                        }
                    )

                warehouses_list.append(
                    {
                        "id": warehouse.id,
                        "name": warehouse.name,
                        "code": warehouse.code,
                        "address": warehouse.address,
                        "phone": warehouse.phone,
                        "email": warehouse.email or "",
                        "manager": (
                            warehouse.manager.get_full_name()
                            if warehouse.manager
                            else "Не назначен"
                        ),
                        "working_hours": warehouse.get_working_hours(),
                        "is_24h": warehouse.is_24h,
                        "is_open_now": warehouse.is_open_now,
                        "total_area": warehouse.total_area or 0,
                        "available_area": warehouse.available_area or 0,
                        "schedules": schedules,
                    }
                )

            cities_data.append(
                {
                    "id": city.id,
                    "name": city.name,
                    "region": city.region or "",
                    "warehouses": warehouses_list,
                }
            )

        context["cities_data"] = cities_data
        # Сериализуем данные в JSON для JavaScript
        context["cities_data_json"] = json.dumps(cities_data, default=str)

        # Получаем типы коробок из базы данных
        box_types = ContainerType.objects.filter(category="box").order_by("volume")
        context["box_sizes"] = []

        for box in box_types:
            context["box_sizes"].append(
                {
                    "name": box.name,
                    "code": box.code,
                    "length": box.length,
                    "width": box.width,
                    "height": box.height,
                    "volume": box.volume or box.calculate_volume(),
                    "weight_capacity": box.weight_capacity,
                    "description": box.description or "",
                }
            )

        return context

    # Остальной код остается без изменений...
    def form_valid(self, form):
        """Сохранение заявки и отправка уведомлений"""
        try:
            # Создаем объект заявки
            order = form.save(commit=False)

            # Устанавливаем дополнительные поля
            order.pickup_date = timezone.now().date()
            order.status = "ready"
            order.notes = f'Заявка создана через веб-форму. Маркетплейс: {form.cleaned_data["marketplace"]}'

            # Автоматически назначаем оператора если склад выбран
            warehouse = form.cleaned_data.get("receiving_warehouse")
            if warehouse and warehouse.manager:
                order.operator = warehouse.manager
                order.receiving_operator = warehouse.manager

            # Сохраняем заявку
            order.save()

            # Отправляем email уведомления
            try:
                self.send_confirmation_email(order)
            except Exception as e:
                print(f"Ошибка при отправке письма клиенту: {e}")

            try:
                self.send_operator_notification(order)
            except Exception as e:
                print(f"Ошибка при отправке письма оператору: {e}")

            # Сохраняем ID заявки в сессии для страницы успеха
            self.request.session["order_id"] = order.id
            self.request.session["tracking_number"] = order.tracking_number

            return super().form_valid(form)

        except Exception as e:
            import traceback

            print(f"Ошибка при сохранении заявки: {e}")
            print(traceback.format_exc())
            messages.error(
                self.request,
                "Произошла ошибка при отправке заявки. Пожалуйста, попробуйте еще раз или свяжитесь с нами по телефону.",
            )
            return self.form_invalid(form)

    def send_confirmation_email(self, order):
        """Отправка подтверждения клиенту"""
        try:
            subject = f"Заявка #{order.tracking_number} принята"
            context = {
                "order": order,
                "tracking_number": order.tracking_number,
                "company_name": order.client_company or order.client_name,
            }

            txt_template = "order_form/emails/confirmation_email.txt"
            html_template = "order_form/emails/confirmation_email.html"

            message = render_to_string(txt_template, context)
            html_message = render_to_string(html_template, context)

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.client_email],
                html_message=html_message,
                fail_silently=True,
            )

            print(f"✅ Email отправлен клиенту: {order.client_email}")

        except Exception as e:
            print(f"❌ Ошибка при отправке email клиенту: {e}")
            import traceback

            print(traceback.format_exc())

    def send_operator_notification(self, order):
        """Отправка уведомления оператору"""
        try:
            subject = f"Новая заявка на забор #{order.tracking_number}"
            context = {
                "order": order,
                "tracking_number": order.tracking_number,
                "SITE_URL": settings.SITE_URL,
            }

            txt_template = "order_form/emails/operator_notification.txt"
            html_template = "order_form/emails/operator_notification.html"

            message = render_to_string(txt_template, context)
            html_message = render_to_string(html_template, context)

            operator_email = getattr(
                settings, "OPERATOR_EMAIL", settings.DEFAULT_FROM_EMAIL
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[operator_email],
                html_message=html_message,
                fail_silently=True,
            )

            print(f"✅ Email отправлен оператору: {operator_email}")

        except Exception as e:
            print(f"❌ Ошибка при отправке email оператору: {e}")
            import traceback

            print(traceback.format_exc())


def order_success_view(request):
    """Страница успешной отправки заявки"""
    order_id = request.session.get("order_id")
    tracking_number = request.session.get("tracking_number")

    context = {
        "order_id": order_id,
        "tracking_number": tracking_number,
    }

    # Очищаем данные из сессии
    if "order_id" in request.session:
        del request.session["order_id"]
    if "tracking_number" in request.session:
        del request.session["tracking_number"]

    return render(request, "order_form/order_success.html", context)
