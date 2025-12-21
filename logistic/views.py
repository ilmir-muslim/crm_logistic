import json
from pathlib import Path
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings as django_settings
from django.core.mail import send_mail, get_connection
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date, datetime, timedelta
from django.db.models import Count, Sum, Avg, Q
from django.http import HttpResponse, JsonResponse
import pandas as pd
from io import BytesIO
import zipfile

from django.views.decorators.http import require_POST

from .models import DeliveryOrder
from .filters import DeliveryOrderFilter
from pickup.models import PickupOrder
from .pdf_utils import create_delivery_order_pdf, create_daily_report_pdf
from .forms import DailyReportForm, DateRangeReportForm, EmailSettingsForm


class DeliveryOrderListView(LoginRequiredMixin, ListView):
    model = DeliveryOrder
    template_name = "logistic/delivery_order_list.html"
    context_object_name = "orders"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        if hasattr(self.request.user, "profile"):
            user_profile = self.request.user.profile

            if user_profile.is_operator:
                queryset = queryset.filter(operator=self.request.user)

        # Применяем фильтр
        self.filterset = DeliveryOrderFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = DeliveryOrderFilter(
            self.request.GET, queryset=self.get_queryset()
        )

        if hasattr(self.request.user, "profile"):
            context["user_role"] = self.request.user.profile.get_role_display()
            context["is_operator"] = self.request.user.profile.is_operator
            context["is_logistic"] = self.request.user.profile.is_logistic
            context["is_admin"] = self.request.user.profile.is_admin

        return context


class DeliveryOrderDetailView(LoginRequiredMixin, DetailView):
    model = DeliveryOrder
    template_name = "logistic/delivery_order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        queryset = super().get_queryset()

        if (
            hasattr(self.request.user, "profile")
            and self.request.user.profile.is_operator
        ):
            queryset = queryset.filter(operator=self.request.user)

        return queryset


class DeliveryOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = DeliveryOrder
    template_name = "logistic/delivery_order_form.html"
    fields = ["driver_name", "driver_phone", "vehicle", "status"]

    def get_success_url(self):
        return reverse("delivery_order_detail", kwargs={"pk": self.object.pk})

    def get_queryset(self):
        queryset = super().get_queryset()

        if (
            hasattr(self.request.user, "profile")
            and self.request.user.profile.is_operator
        ):
            queryset = queryset.filter(operator=self.request.user)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_edit"] = self.object.status != "shipped"
        return context

    def form_valid(self, form):
        if self.object.status == "shipped":
            form.add_error(None, "Заявка уже отправлена. Редактирование запрещено.")
            return self.form_invalid(form)

        if form.cleaned_data.get("status") == "shipped":
            messages.success(
                self.request,
                "Заявка отмечена как отправленная. Дальнейшее редактирование будет ограничено.",
            )

        response = super().form_valid(form)
        messages.success(self.request, "Данные водителя успешно обновлены!")
        return response


@require_POST
@login_required
def update_delivery_order_field(request, pk):
    """Обновление одного поля заявки на доставку"""
    try:
        order = DeliveryOrder.objects.get(pk=pk)
    except DeliveryOrder.DoesNotExist:
        return JsonResponse({"success": False, "error": "Заявка не найдена"})

    # Проверка прав
    if not (
        request.user.is_superuser
        or request.user.groups.filter(name="Логисты").exists()
        or request.user == order.operator
    ):
        return JsonResponse({"success": False, "error": "Нет прав на редактирование"})

    data = json.loads(request.body)
    field = data.get("field")
    value = data.get("value")

    # Разрешенные поля для редактирования
    allowed_fields = [
        "city",
        "warehouse",
        "quantity",
        "weight",
        "volume",
        "status",
        "driver_name",
        "driver_phone",
        "date",  # Добавлено для редактирования даты
    ]

    if field not in allowed_fields:
        return JsonResponse(
            {"success": False, "error": "Поле не доступно для редактирования"}
        )

    try:
        # Преобразование типов
        if field in ["quantity"]:
            value = int(value)
        elif field in ["weight", "volume"]:
            value = float(value) if value else None
        elif field == "date":
            # Преобразуем строку даты
            from datetime import datetime

            try:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"success": False, "error": "Неверный формат даты"})

        setattr(order, field, value)
        order.save()

        # Для статуса возвращаем отображаемое значение
        if field == "status":
            display_value = order.get_status_display()
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "date":
            # Для даты возвращаем отформатированное значение
            display_value = order.date.strftime("%d.%m.%Y")
            return JsonResponse({"success": True, "display_value": display_value})

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def dashboard(request):
    today = date.today()

    user = request.user
    queryset_filter = Q()
    if hasattr(user, "profile") and user.profile.is_operator:
        queryset_filter = Q(operator=user)

    delivery_stats = {
        "total": DeliveryOrder.objects.filter(queryset_filter).count(),
        "today": DeliveryOrder.objects.filter(queryset_filter & Q(date=today)).count(),
        "submitted": DeliveryOrder.objects.filter(
            queryset_filter & Q(status="submitted")
        ).count(),
        "driver_assigned": DeliveryOrder.objects.filter(
            queryset_filter & Q(status="driver_assigned")
        ).count(),
        "shipped": DeliveryOrder.objects.filter(
            queryset_filter & Q(status="shipped")
        ).count(),
    }

    if hasattr(user, "profile") and (user.profile.is_admin or user.profile.is_logistic):
        delivery_stats["total_weight"] = (
            DeliveryOrder.objects.aggregate(Sum("weight"))["weight__sum"] or 0
        )
        delivery_stats["total_volume"] = (
            DeliveryOrder.objects.aggregate(Sum("volume"))["volume__sum"] or 0
        )
    else:
        delivery_stats["total_weight"] = (
            DeliveryOrder.objects.filter(queryset_filter).aggregate(Sum("weight"))[
                "weight__sum"
            ]
            or 0
        )
        delivery_stats["total_volume"] = (
            DeliveryOrder.objects.filter(queryset_filter).aggregate(Sum("volume"))[
                "volume__sum"
            ]
            or 0
        )

    pickup_filter = Q()
    if hasattr(user, "profile") and user.profile.is_operator:
        pickup_filter = Q(operator=user)

    pickup_stats = {
        "total": PickupOrder.objects.filter(pickup_filter).count(),
        "today": PickupOrder.objects.filter(
            pickup_filter & Q(pickup_date=today)
        ).count(),
        "new": PickupOrder.objects.filter(pickup_filter & Q(status="new")).count(),
        "confirmed": PickupOrder.objects.filter(
            pickup_filter & Q(status="confirmed")
        ).count(),
        "picked_up": PickupOrder.objects.filter(
            pickup_filter & Q(status="picked_up")
        ).count(),
        "cancelled": PickupOrder.objects.filter(
            pickup_filter & Q(status="cancelled")
        ).count(),
    }

    seven_days_ago = today - timedelta(days=7)
    delivery_chart_data = []

    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        count = DeliveryOrder.objects.filter(queryset_filter & Q(date=day)).count()
        delivery_chart_data.append({"date": day.strftime("%d.%m"), "count": count})

    recent_deliveries = DeliveryOrder.objects.filter(queryset_filter).order_by(
        "-created_at"
    )[:5]
    recent_pickups = PickupOrder.objects.filter(pickup_filter).order_by("-created_at")[
        :5
    ]

    # ЗАГРУЖАЕМ ТЕКУЩИЕ НАСТРОЙКИ EMAIL ДЛЯ АВТОЗАПОЛНЕНИЯ
    email_settings = load_email_settings()
    if email_settings is None:
        email_settings = {}

    context = {
        "delivery_stats": delivery_stats,
        "pickup_stats": pickup_stats,
        "delivery_chart_data": delivery_chart_data,
        "recent_deliveries": recent_deliveries,
        "recent_pickups": recent_pickups,
        "today": today,
        "email_settings": email_settings,
    }

    if hasattr(request.user, "profile"):
        context["user_role"] = request.user.profile.get_role_display()
        context["is_operator"] = request.user.profile.is_operator
        context["is_logistic"] = request.user.profile.is_logistic
        context["is_admin"] = request.user.profile.is_admin

    return render(request, "dashboard/dashboard.html", context)


def delivery_order_pdf(request, pk):
    order = get_object_or_404(DeliveryOrder, pk=pk)

    if hasattr(request.user, "profile") and request.user.profile.is_operator:
        if order.operator != request.user:
            messages.error(request, "У вас нет доступа к этой заявке")
            return redirect("delivery_order_list")

    pdf = create_delivery_order_pdf(order)

    if pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f"delivery_{order.tracking_number or order.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    else:
        messages.error(request, "Ошибка при генерации PDF")
        return redirect("delivery_order_detail", pk=pk)


def daily_report_pdf(request):
    date_str = request.GET.get("date")
    if date_str:
        try:
            report_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            report_date = timezone.now().date()
    else:
        report_date = timezone.now().date()

    orders = DeliveryOrder.objects.filter(date=report_date)

    if hasattr(request.user, "profile") and request.user.profile.is_operator:
        orders = orders.filter(operator=request.user)

    pdf = create_daily_report_pdf(report_date, orders)

    if pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f"daily_report_{report_date.strftime('%Y%m%d')}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    else:
        messages.error(request, "Ошибка при генерации отчета")
        return redirect("dashboard")


def delivery_orders_bulk_pdf(request):
    order_ids = request.GET.getlist("order_ids")

    if not order_ids:
        messages.error(request, "Не выбраны заявки для экспорта")
        return redirect("delivery_order_list")

    orders = DeliveryOrder.objects.filter(id__in=order_ids)

    if hasattr(request.user, "profile") and request.user.profile.is_operator:
        orders = orders.filter(operator=request.user)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for order in orders:
            pdf = create_delivery_order_pdf(order)
            if pdf:
                filename = f"delivery_{order.tracking_number or order.id}.pdf"
                zip_file.writestr(filename, pdf)

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="delivery_orders.zip"'
    return response


def reports_dashboard(request):
    context = {
        "daily_form": DailyReportForm(),
        "range_form": DateRangeReportForm(),
    }

    if hasattr(request.user, "profile"):
        context["user_role"] = request.user.profile.get_role_display()
        context["is_operator"] = request.user.profile.is_operator
        context["is_logistic"] = request.user.profile.is_logistic
        context["is_admin"] = request.user.profile.is_admin

    return render(request, "reports/reports_dashboard.html", context)


def generate_daily_report(request):
    if request.method == "GET":
        form = DailyReportForm(request.GET)

        if form.is_valid():
            report_date = form.cleaned_data["date"]
            report_type = form.cleaned_data["report_type"]
            format_type = form.cleaned_data["format"]

            user_filter = {}
            if hasattr(request.user, "profile") and request.user.profile.is_operator:
                user_filter = {"operator": request.user}

            if format_type == "pdf":
                if report_type == "delivery":
                    orders = DeliveryOrder.objects.filter(
                        date=report_date, **user_filter
                    )
                    pdf = create_daily_report_pdf(report_date, orders)

                    if pdf:
                        response = HttpResponse(pdf, content_type="application/pdf")
                        filename = (
                            f"delivery_report_{report_date.strftime('%Y%m%d')}.pdf"
                        )
                        response["Content-Disposition"] = (
                            f'attachment; filename="{filename}"'
                        )
                        return response

                elif report_type == "pickup":
                    from pickup.pdf_utils import create_daily_pickup_report_pdf

                    orders = PickupOrder.objects.filter(
                        pickup_date=report_date, **user_filter
                    )
                    pdf = create_daily_pickup_report_pdf(report_date, orders)

                    if pdf:
                        response = HttpResponse(pdf, content_type="application/pdf")
                        filename = f"pickup_report_{report_date.strftime('%Y%m%d')}.pdf"
                        response["Content-Disposition"] = (
                            f'attachment; filename="{filename}"'
                        )
                        return response

            elif format_type == "excel":
                return generate_excel_report(report_date, report_type, user_filter)

    messages.error(request, "Ошибка при генерации отчета")
    return redirect("reports_dashboard")


def generate_excel_report(date, report_type, user_filter):
    if report_type == "delivery":
        orders = DeliveryOrder.objects.filter(date=date, **user_filter)

        data = []
        for order in orders:
            data.append(
                {
                    "Номер": order.tracking_number or f"#{order.id}",
                    "Дата": order.date.strftime("%d.%m.%Y"),
                    "Город": order.city,
                    "Склад": order.warehouse,
                    "Места": order.quantity,
                    "Вес (кг)": order.weight,
                    "Объем (м³)": order.volume,
                    "Статус": order.get_status_display(),
                    "Водитель": order.driver_name or "",
                    "Телефон водителя": order.driver_phone or "",
                    "ТС": order.vehicle or "",
                    "Оператор": order.operator.username if order.operator else "",
                }
            )

        df = pd.DataFrame(data)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Доставки", index=False)

            worksheet = writer.sheets["Доставки"]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 30)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        filename = f"delivery_report_{date.strftime('%Y%m%d')}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    return None


def statistics_report(request):
    if request.method == "GET":
        form = DateRangeReportForm(request.GET)

        if form.is_valid():
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]
            report_type = form.cleaned_data["report_type"]

            context = {
                "start_date": start_date,
                "end_date": end_date,
                "report_type": report_type,
                "form": form,
            }

            user_filter = {}
            if hasattr(request.user, "profile") and request.user.profile.is_operator:
                user_filter = {"operator": request.user}

            if report_type == "delivery":
                orders = DeliveryOrder.objects.filter(
                    date__range=[start_date, end_date], **user_filter
                )

                stats = {
                    "total_orders": orders.count(),
                    "by_status": orders.values("status").annotate(count=Count("id")),
                    "by_city": orders.values("city").annotate(
                        count=Count("id"),
                        total_weight=Sum("weight"),
                        total_volume=Sum("volume"),
                        avg_weight=Avg("weight"),
                    ),
                    "by_warehouse": orders.values("warehouse").annotate(
                        count=Count("id")
                    ),
                    "total_weight": orders.aggregate(Sum("weight"))["weight__sum"] or 0,
                    "total_volume": orders.aggregate(Sum("volume"))["volume__sum"] or 0,
                    "total_quantity": orders.aggregate(Sum("quantity"))["quantity__sum"]
                    or 0,
                }

                context["stats"] = stats
                context["orders"] = orders

            elif report_type == "pickup":
                orders = PickupOrder.objects.filter(
                    pickup_date__range=[start_date, end_date], **user_filter
                )

                stats = {
                    "total_orders": orders.count(),
                    "by_status": orders.values("status").annotate(count=Count("id")),
                    "by_client": orders.values("client_name").annotate(
                        count=Count("id"),
                        total_weight=Sum("weight"),
                        total_quantity=Sum("quantity"),
                    ),
                    "total_weight": orders.aggregate(Sum("weight"))["weight__sum"] or 0,
                    "total_volume": orders.aggregate(Sum("volume"))["volume__sum"] or 0,
                    "total_quantity": orders.aggregate(Sum("quantity"))["quantity__sum"]
                    or 0,
                    "converted_to_delivery": orders.filter(
                        delivery_order__isnull=False
                    ).count(),
                }

                context["stats"] = stats
                context["orders"] = orders

            return render(request, "reports/statistics_report.html", context)

    return render(
        request, "reports/statistics_report.html", {"form": DateRangeReportForm()}
    )


@login_required
def email_settings_view(request):
    """Представление для настройки параметров email"""

    # Загружаем текущие настройки для автозаполнения
    current_settings = load_email_settings() or {}

    # Инициализация формы с текущими настройками
    initial_data = {
        "email_host": current_settings.get("email_host", ""),
        "email_port": current_settings.get("email_port", 587),
        "email_host_user": current_settings.get("email_host_user", ""),
        "email_host_password": "",  # Пароль не показываем в форме
        "default_from_email": current_settings.get("default_from_email", ""),
        "operator_email": current_settings.get("operator_email", ""),
    }

    if request.method == "POST":
        # Обрабатываем данные формы
        host = request.POST.get("email_host")
        if host == "custom":
            host = request.POST.get("custom_email_host", "")

        # Обрабатываем пароль: если поле пустое, оставляем старый пароль
        new_password = request.POST.get("email_host_password", "")
        if not new_password and current_settings.get("email_host_password"):
            password = current_settings["email_host_password"]
        else:
            password = new_password

        try:
            # Формируем настройки
            settings_data = {
                "email_backend": "django.core.mail.backends.smtp.EmailBackend",
                "email_host": host,
                "email_port": int(request.POST.get("email_port", 587)),
                "email_use_tls": request.POST.get("email_use_tls") == "1",
                "email_use_ssl": False,
                "email_host_user": request.POST.get("email_host_user", ""),
                "email_host_password": password,
                "default_from_email": request.POST.get("default_from_email", ""),
                "operator_email": request.POST.get("operator_email", ""),
                "enable_operator_notifications": request.POST.get(
                    "enable_operator_notifications"
                )
                == "on",
            }

            # Сохраняем в JSON файл
            settings_file = Path(django_settings.BASE_DIR) / "email_settings.json"
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=4)

            # Тестовая отправка
            if request.POST.get("send_test"):
                test_email = request.POST.get("email_host_user")
                try:
                    send_test_email(settings_data, test_email)
                    messages.success(
                        request, "Настройки сохранены. Тестовое письмо отправлено!"
                    )
                except Exception as e:
                    messages.warning(
                        request,
                        f"Настройки сохранены, но тестовое письмо не отправлено: {str(e)[:100]}...",
                    )
            else:
                messages.success(request, "Настройки email успешно сохранены!")

            return redirect("dashboard")

        except Exception as e:
            messages.error(request, f"Ошибка: {str(e)[:100]}...")
    else:
        # Для GET-запроса создаем форму с текущими настройками
        form = EmailSettingsForm(initial=initial_data)

    context = {
        "form": form,
        "title": "Настройки Email",
    }

    if hasattr(request.user, "profile"):
        context["user_role"] = request.user.profile.get_role_display()
        context["is_operator"] = request.user.profile.is_operator
        context["is_logistic"] = request.user.profile.is_logistic
        context["is_admin"] = request.user.profile.is_admin

    return render(request, "logistic/email_settings.html", context)


@login_required
def test_email_connection(request):
    """AJAX-тестирование подключения к SMTP без сохранения настроек"""
    if (
        request.method == "POST"
        and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):
        try:
            # Определяем хост
            host = request.POST.get("email_host")
            if host == "custom":
                host = request.POST.get("custom_email_host", "")

            # Получаем остальные параметры
            port = int(request.POST.get("email_port", 587))
            username = request.POST.get("email_host_user", "")
            password = request.POST.get("email_host_password", "")
            use_tls = request.POST.get("email_use_tls") == "1"

            # Проверяем обязательные поля
            if not host or not username:
                return JsonResponse(
                    {"success": False, "error": "Заполните обязательные поля"}
                )

            # Тестируем подключение
            connection = get_connection(
                backend="django.core.mail.backends.smtp.EmailBackend",
                host=host,
                port=port,
                username=username,
                password=password,
                use_tls=use_tls,
                use_ssl=False,
                timeout=10,
            )

            connection.open()
            connection.close()

            return JsonResponse({"success": True, "message": "Подключение успешно"})

        except Exception as e:
            error_msg = str(e)
            # Упрощаем сообщение об ошибке для пользователя
            if "Connection refused" in error_msg:
                error_msg = "Сервер недоступен. Проверьте хост и порт."
            elif "authentication failed" in error_msg.lower():
                error_msg = "Ошибка авторизации. Проверьте логин и пароль."
            elif "STARTTLS" in error_msg:
                error_msg = (
                    "Сервер не поддерживает шифрование. Попробуйте отключить TLS."
                )

            return JsonResponse({"success": False, "error": error_msg})

    return JsonResponse({"success": False, "error": "Некорректный запрос"})


def send_test_email(settings_data, to_email):
    """Отправка тестового письма"""
    connection = get_connection(
        backend=settings_data["email_backend"],
        host=settings_data["email_host"],
        port=settings_data["email_port"],
        username=settings_data["email_host_user"],
        password=settings_data["email_host_password"],
        use_tls=settings_data["email_use_tls"],
        use_ssl=settings_data["email_use_ssl"],
    )

    send_mail(
        subject="✅ Тест: Настройки email работают!",
        message="Поздравляем! Настройки email в CRM Логистика успешно сохранены и работают.\n\n"
        "Теперь вы будете получать уведомления о новых заявках.",
        from_email=settings_data["default_from_email"],
        recipient_list=[to_email],
        connection=connection,
        fail_silently=False,
    )


def load_email_settings():
    """Функция для загрузки настроек email из файла"""
    try:
        settings_file = Path(django_settings.BASE_DIR) / "email_settings.json"
        if settings_file.exists():
            with open(settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return None
