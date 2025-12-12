# [file name]: order_form/views.py
from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import datetime

from .forms import ClientOrderForm
from pickup.models import PickupOrder


class ClientOrderFormView(FormView):
    """Представление для формы заявки клиента"""

    template_name = "order_form/client_order_form.html"
    form_class = ClientOrderForm
    success_url = reverse_lazy("order_form_success")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Добавляем информацию о графике и объемах для отображения в шаблоне
        context["delivery_schedule"] = [
            {
                "city": "Москва (Электросталь, Коледино, Подольск)",
                "pickup_days": "вторник, среда",
                "delivery_days": "среда, пятница",
            },
            {
                "city": "Тула (Алексин)",
                "pickup_days": "вторник, среда",
                "delivery_days": "вторник, суббота",
            },
            {
                "city": "Рязань (Пошевски)",
                "pickup_days": "четверг, суббота",
                "delivery_days": "пятница, воскресенье",
            },
            {
                "city": "Краснодар, Невинномысск",
                "pickup_days": "четверг",
                "delivery_days": "суббота",
            },
            {
                "city": "Санкт-Петербург",
                "pickup_days": "четверг",
                "delivery_days": "суббота",
            },
            {
                "city": "Екатеринбург",
                "pickup_days": "четверг",
                "delivery_days": "суббота",
            },
        ]

        context["box_sizes"] = [
            {
                "name": "Коробка XL",
                "length": 12,
                "width": 8,
                "height": 18,
                "volume": 1.7,
            },
            {"name": "Коробка L", "length": 6, "width": 8, "height": 5, "volume": 0.24},
            {"name": "Коробка M", "length": 6, "width": 4, "height": 4, "volume": 0.1},
            {"name": "Коробка S", "length": 4, "width": 3, "height": 4, "volume": 0.05},
        ]

        return context

    def form_valid(self, form):
        """Сохранение заявки и отправка уведомлений"""
        try:
            # Создаем объект заявки
            order = form.save(commit=False)

            # Устанавливаем дополнительные поля
            order.pickup_date = (
                timezone.now().date()
            )  # Дата забора будет уточнена оператором
            order.status = "new"
            order.notes = f'Заявка создана через веб-форму. Маркетплейс: {form.cleaned_data["marketplace"]}'

            # Сохраняем заявку
            order.save()

            # Отправляем email уведомление клиенту (с обработкой ошибок)
            try:
                self.send_confirmation_email(order)
            except Exception as e:
                print(f"Ошибка при отправке письма клиенту: {e}")

            # Отправляем email уведомление оператору (с обработкой ошибок)
            try:
                self.send_operator_notification(order)
            except Exception as e:
                print(f"Ошибка при отправке письма оператору: {e}")

            # Сохраняем ID заявки в сессии для страницы успеха
            self.request.session["order_id"] = order.id
            self.request.session["tracking_number"] = order.tracking_number

            return super().form_valid(form)

        except Exception as e:
            # Логируем ошибку
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

            # Сначала проверяем существование шаблонов
            txt_template = "order_form/emails/operator_notification.txt"
            html_template = "order_form/emails/operator_notification.html"

            message = render_to_string(txt_template, context)
            html_message = render_to_string(html_template, context)

            # Отправляем на email оператора из настроек или на дефолтный
            operator_email = getattr(
                settings, "OPERATOR_EMAIL", settings.DEFAULT_FROM_EMAIL
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[operator_email],
                html_message=html_message,
                fail_silently=True,  # Не прерывать выполнение при ошибке email
            )

            print(f"✅ Email отправлен оператору: {operator_email}")

        except Exception as e:
            print(f"❌ Ошибка при отправке email оператору: {e}")
            import traceback

            print(traceback.format_exc())
            # Не выбрасываем исключение, чтобы не прерывать выполнение


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
