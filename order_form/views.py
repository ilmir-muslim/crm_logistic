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

from .forms import ClientPickupForm, ClientDeliveryForm
from warehouses.models import City, ContainerType, WarehouseSchedule
from counterparties.models import Counterparty


class PickupOrderFormView(FormView):
    """Представление для формы заявки на ЗАБОР груза"""

    template_name = "order_form/pickup_form.html"
    form_class = ClientPickupForm
    success_url = reverse_lazy("order_form_success")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cities = (
            City.objects.filter(warehouses__isnull=False).distinct().order_by("name")
        )

        cities_data = []
        for city in cities:
            warehouses = city.warehouses.all().prefetch_related(
                Prefetch(
                    "schedules",
                    queryset=WarehouseSchedule.objects.filter(is_working=True).order_by(
                        "day_of_week"
                    ),
                )
            )

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
                        "is_open_now": warehouse.is_open_now,  # Используем свойство модели
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
        context["cities_data_json"] = json.dumps(cities_data, default=str)

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

    def form_valid(self, form):
        """Сохранение заявки на забор с обработкой контрагентов"""
        try:
            # Сохраняем форму с данными
            order = form.save(commit=False)

            # Устанавливаем дополнительные поля
            order.pickup_date = timezone.now().date()
            order.status = "ready"

            # Получаем warehouse и устанавливаем оператора
            warehouse = form.cleaned_data.get("receiving_warehouse")
            if warehouse:
                if warehouse.manager:
                    order.operator = warehouse.manager
                    order.receiving_operator = warehouse.manager
                order.receiving_warehouse = warehouse

            # Сохраняем в базе данных
            order.save()

            # Перезагружаем объект из базы
            order.refresh_from_db()

            print(
                f"✅ Заявка на забор создана: ID={order.id}, Tracking={order.tracking_number}"
            )

            # Отправляем email клиенту
            try:
                self.send_confirmation_email(order)
                print(f"✅ Email отправлен клиенту")
            except Exception as e:
                print(f"❌ Ошибка при отправке email клиенту: {e}")

            # Отправляем уведомление оператору
            try:
                self.send_operator_notification(order)
                print(f"✅ Уведомление отправлено оператору")
            except Exception as e:
                print(f"❌ Ошибка при отправке уведомления оператору: {e}")

            # Сохраняем данные в сессии
            self.request.session["order_id"] = order.id
            self.request.session["tracking_number"] = order.tracking_number
            self.request.session["order_type"] = "pickup"

            # Принудительно сохраняем сессию
            self.request.session.modified = True
            self.request.session.save()

            return redirect(self.get_success_url())

        except Exception as e:
            import traceback

            print(f"❌ Ошибка при сохранении заявки на забор: {e}")
            print(traceback.format_exc())
            messages.error(
                self.request,
                f"Произошла ошибка при отправке заявки: {str(e)[:100]}... Пожалуйста, попробуйте еще раз или свяжитесь с нами по телефону.",
            )
            return self.form_invalid(form)

    def send_confirmation_email(self, order):
        """Отправка подтверждения клиенту"""
        try:
            subject = f"Заявка на забор #{order.tracking_number} принята"
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

            return True

        except Exception as e:
            print(f"❌ Ошибка при отправке email клиенту: {e}")
            return False

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

            return True

        except Exception as e:
            print(f"❌ Ошибка при отправке email оператору: {e}")
            return False


class DeliveryOrderFormView(FormView):
    """Представление для формы заявки на ОТПРАВКУ груза"""

    template_name = "order_form/delivery_form.html"
    form_class = ClientDeliveryForm
    success_url = reverse_lazy("order_form_success")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cities = (
            City.objects.filter(warehouses__isnull=False).distinct().order_by("name")
        )

        cities_data = []
        for city in cities:
            warehouses = city.warehouses.all().prefetch_related("schedules")

            warehouses_list = []
            for warehouse in warehouses:
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
                        "is_open_now": warehouse.is_open_now,  # Используем свойство модели
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
        context["cities_data_json"] = json.dumps(cities_data, default=str)

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

    def form_valid(self, form):
        """Сохранение заявки на доставку с обработкой клиента"""
        try:
            order = form.save(commit=False)
            order.status = "submitted"
            order.operator = None 
            order.save()
            order.refresh_from_db()

            print(
                f"✅ Заявка на доставку создана: ID={order.id}, Tracking={order.tracking_number}"
            )

            try:
                client_email = form.cleaned_data.get("client_email")
                if client_email:
                    self.send_confirmation_email(
                        order,
                        form.cleaned_data["client_company"],
                        form.cleaned_data["client_name"],
                        client_email,
                    )
                    print(f"✅ Email отправлен клиенту: {client_email}")
            except Exception as e:
                print(f"❌ Ошибка при отправке email клиенту: {e}")

            try:
                self.send_operator_notification(order)
                print(f"✅ Уведомление отправлено оператору")
            except Exception as e:
                print(f"❌ Ошибка при отправке уведомления оператору: {e}")

            self.request.session["order_id"] = order.id
            self.request.session["tracking_number"] = order.tracking_number
            self.request.session["order_type"] = "delivery"

            self.request.session.modified = True
            self.request.session.save()

            return redirect(self.get_success_url())

        except Exception as e:
            import traceback

            print(f"❌ Ошибка при сохранении заявки на доставку: {e}")
            print(traceback.format_exc())
            messages.error(
                self.request,
                f"Произошла ошибка при отправке заявки: {str(e)[:100]}... Пожалуйста, попробуйте еще раз или свяжитесь с нами по телефону.",
            )
            return self.form_invalid(form)

    def send_confirmation_email(self, order, company_name, contact_name, client_email):
        """Отправка подтверждения клиенту"""
        try:
            subject = f"Заявка на доставку #{order.tracking_number} принята"

            message = f"""
            Ваша заявка на доставку груза #{order.tracking_number} принята.
            
            Детали заявки:
            Компания: {company_name}
            Контактное лицо: {contact_name}
            Дата доставки: {order.date}
            Город: {order.city}
            Склад отправки: {order.warehouse}
            
            Мы свяжемся с вами в ближайшее время.
            
            С уважением,
            Команда ФФ Царицыно
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client_email],
                fail_silently=True,
            )

            return True

        except Exception as e:
            print(f"❌ Ошибка при отправке email клиенту: {e}")
            return False

    def send_operator_notification(self, order):
        """Отправка уведомления оператору"""
        try:
            subject = f"Новая заявка на доставку #{order.tracking_number}"
            context = {
                "order": order,
                "tracking_number": order.tracking_number,
                "SITE_URL": settings.SITE_URL,
            }

            txt_template = "order_form/emails/operator_notification_delivery.txt"
            html_template = "order_form/emails/operator_notification_delivery.html"

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

            return True

        except Exception as e:
            print(f"❌ Ошибка при отправке email оператору: {e}")
            return False


def order_success_view(request):
    """Страница успешной отправки заявки"""
    order_id = request.session.get("order_id")
    tracking_number = request.session.get("tracking_number")
    order_type = request.session.get("order_type", "delivery")

    print(
        f"🔍 order_success_view вызван: order_id={order_id}, tracking_number={tracking_number}, order_type={order_type}"
    )

    context = {
        "order_id": order_id,
        "tracking_number": tracking_number,
        "order_type": order_type,
    }

    return render(request, "order_form/order_success.html", context)
