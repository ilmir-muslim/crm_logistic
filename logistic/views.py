import base64
import json
import os
from pathlib import Path
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings as django_settings
from django.core.mail import send_mail, get_connection
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date, datetime, timedelta
from django.db.models import Count, Sum, Q
from django.http import HttpResponse, JsonResponse
import pandas as pd
from io import BytesIO
import zipfile

from django.views.decorators.http import require_POST
from weasyprint import HTML


from .models import DeliveryOrder
from pickup.models import PickupOrder
from .pdf_utils import create_delivery_order_pdf, create_daily_report_pdf, create_delivery_orders_list_pdf
from .forms import DailyReportForm, DateRangeReportForm, DeliveryOrderCreateForm, EmailSettingsForm


class DeliveryOrderListView(LoginRequiredMixin, ListView):
    model = DeliveryOrder
    template_name = "logistic/delivery_order_list.html"
    context_object_name = "orders"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_authenticated and hasattr(self.request.user, "profile"):
            if self.request.user.profile.role == "operator":
                queryset = queryset.filter(operator=self.request.user)

        date_gte = self.request.GET.get("date__gte")
        date_lte = self.request.GET.get("date__lte")
        city = self.request.GET.get("city")
        warehouse = self.request.GET.get("warehouse")
        status = self.request.GET.get("status")
        fulfillment = self.request.GET.get("fulfillment")

        if date_gte:
            queryset = queryset.filter(date__gte=date_gte)
        if date_lte:
            queryset = queryset.filter(date__lte=date_lte)
        if city and city != "":
            queryset = queryset.filter(city_id=city)
        if warehouse and warehouse != "":
            queryset = queryset.filter(warehouse_id=warehouse)
        if status:
            queryset = queryset.filter(status=status)
        if fulfillment:
            queryset = queryset.filter(fulfillment_id=fulfillment)

        sort = self.request.GET.get("sort", "date")
        order = self.request.GET.get("order", "desc")

        allowed_sort_fields = [
            "date",
            "city",
            "warehouse",
            "fulfillment",
            "quantity",
            "weight",
            "status",
            "driver_name",
        ]

        if sort in allowed_sort_fields:
            if order == "desc":
                sort_field = f"-{sort}"
            else:
                sort_field = sort
            queryset = queryset.order_by(sort_field)
        else:
            queryset = queryset.order_by("-date")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_operator"] = (
            self.request.user.is_authenticated
            and hasattr(self.request.user, "profile")
            and self.request.user.profile.role == "operator"
        )
        context["is_logistic"] = (
            self.request.user.is_authenticated
            and hasattr(self.request.user, "profile")
            and self.request.user.profile.role == "logistic"
        )
        context["sort"] = self.request.GET.get("sort", "date")
        context["order"] = self.request.GET.get("order", "desc")

        from django.contrib.auth.models import User

        context["operators_list"] = User.objects.filter(
            is_active=True, profile__role="operator"
        ).order_by("first_name", "last_name", "username")

        from warehouses.models import City, Warehouse

        context["cities"] = City.objects.all().order_by("name")

        context["warehouses"] = (
            Warehouse.objects.select_related("city").all().order_by("name")
        )

        if self.request.GET.get("fulfillment"):
            try:
                fulfillment_user = User.objects.get(
                    id=self.request.GET.get("fulfillment")
                )
                context["selected_fulfillment"] = fulfillment_user
            except User.DoesNotExist:
                pass

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

    if not (
        request.user.is_superuser
        or request.user.groups.filter(name="Логисты").exists()
        or request.user == order.operator
    ):
        return JsonResponse({"success": False, "error": "Нет прав на редактирование"})

    data = json.loads(request.body)
    field = data.get("field")
    value = data.get("value")

    allowed_fields = [
        "sender",
        "sender_address",
        "recipient",
        "recipient_address",
        "quantity",
        "weight",
        "volume",
        "status",
        "driver_name",
        "driver_phone",
        "date",
        "fulfillment",
    ]

    if field not in allowed_fields:
        return JsonResponse(
            {"success": False, "error": "Поле не доступно для редактирования"}
        )

    try:
        if field in ["quantity"]:
            value = int(value)
        elif field in ["weight", "volume"]:
            value = float(value) if value else None
        elif field == "date":
            from datetime import datetime

            try:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"success": False, "error": "Неверный формат даты"})
        elif field == "fulfillment":
            if value:
                from django.contrib.auth.models import User

                try:
                    value = User.objects.get(id=value)
                except User.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "error": "Пользователь не найден"}
                    )
            else:
                value = None
        elif field in ["sender", "recipient"]:
            if value:
                from counterparties.models import Counterparty

                try:
                    value = Counterparty.objects.get(id=value)
                except Counterparty.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "error": "Контрагент не найден"}
                    )
            else:
                value = None
        elif field in ["sender_address", "recipient_address"]:
            pass

        setattr(order, field, value)
        order.save()

        if field == "status":
            display_value = order.get_status_display()
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "date":
            display_value = order.date.strftime("%d.%m.%Y")
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "fulfillment":
            display_value = order.get_fulfillment_display()
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "sender":
            display_value = order.get_sender_display()
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "recipient":
            display_value = order.get_recipient_display()
            return JsonResponse({"success": True, "display_value": display_value})
        elif field in ["sender_address", "recipient_address"]:
            display_value = value if value else ""
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
    """Экспорт выбранных заявок на доставку в ZIP-архив"""
    order_ids = request.GET.getlist("order_ids")

    if not order_ids:
        messages.error(request, "Не выбраны заявки для экспорта")
        return redirect("delivery_order_list")

    try:
        orders = DeliveryOrder.objects.filter(id__in=order_ids)

        if hasattr(request.user, "profile") and request.user.profile.is_operator:
            orders = orders.filter(operator=request.user)

        if not orders.exists():
            messages.error(request, "Не найдено заявок для экспорта")
            return redirect("delivery_order_list")

        zip_buffer = BytesIO()
        success_count = 0

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for order in orders:
                try:
                    pdf = create_delivery_order_pdf(order)
                    if pdf:
                        filename = f"delivery_{order.tracking_number or order.id}.pdf"
                        zip_file.writestr(filename, pdf)
                        success_count += 1
                        print(f"✅ PDF создан для заявки {order.id}: {filename}")
                    else:
                        print(f"⚠️ PDF не создан для заявки {order.id}")
                except Exception as e:
                    print(f"❌ Ошибка при создании PDF для заявки {order.id}: {e}")
                    import traceback

                    traceback.print_exc()

        if success_count == 0:
            messages.error(request, "Не удалось создать ни одного PDF файла")
            return redirect("delivery_order_list")

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="delivery_orders.zip"'

        print(f"✅ Создан архив с {success_count} файлами")
        return response

    except Exception as e:
        print(f"❌ Критическая ошибка при создании архива: {e}")
        import traceback

        traceback.print_exc()
        messages.error(request, f"Ошибка при создании архива: {str(e)[:100]}")
        return redirect("delivery_order_list")


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
                    "Адрес отправки": order.pickup_address or "",
                    "Адрес доставки": order.delivery_address or "",
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

    elif report_type == "pickup":
        orders = PickupOrder.objects.filter(pickup_date=date, **user_filter)

        data = []
        for order in orders:
            data.append(
                {
                    "Номер": order.tracking_number or f"#{order.id}",
                    "Дата забора": order.pickup_date.strftime("%d.%m.%Y"),
                    "Время забора": (
                        order.pickup_time.strftime("%H:%M") if order.pickup_time else ""
                    ),
                    "Адрес забора": order.pickup_address or "",
                    "Контакт для выдачи": order.contact_person or "",
                    "Клиент": order.client_name or "",
                    "Компания": order.client_company or "",
                    "Телефон": order.client_phone or "",
                    "Email": order.client_email or "",
                    "Маркетплейс": order.marketplace or "",
                    "Дата поставки": order.desired_delivery_date.strftime("%d.%m.%Y"),
                    "Адрес доставки": order.delivery_address or "",
                    "Номер накладной": order.invoice_number or "",
                    "Склад приемки": (
                        order.receiving_warehouse.name
                        if order.receiving_warehouse
                        else ""
                    ),
                    "Оператор приемки": (
                        order.receiving_operator.username
                        if order.receiving_operator
                        else ""
                    ),
                    "Места": order.quantity,
                    "Вес (кг)": order.weight,
                    "Объем (м³)": order.volume,
                    "Статус": order.get_status_display(),
                    "Оператор": order.operator.username if order.operator else "",
                }
            )

        df = pd.DataFrame(data)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Заборы", index=False)

            worksheet = writer.sheets["Заборы"]
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
        filename = f"pickup_report_{date.strftime('%Y%m%d')}.xlsx"
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

    current_settings = load_email_settings() or {}

    initial_data = {
        "email_host": current_settings.get("email_host", ""),
        "email_port": current_settings.get("email_port", 587),
        "email_host_user": current_settings.get("email_host_user", ""),
        "email_host_password": "", 
        "default_from_email": current_settings.get("default_from_email", ""),
        "operator_email": current_settings.get("operator_email", ""),
    }

    if request.method == "POST":
        host = request.POST.get("email_host")
        if host == "custom":
            host = request.POST.get("custom_email_host", "")

        new_password = request.POST.get("email_host_password", "")
        if not new_password and current_settings.get("email_host_password"):
            password = current_settings["email_host_password"]
        else:
            password = new_password

        try:
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

            settings_file = Path(django_settings.BASE_DIR) / "email_settings.json"
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=4)

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
            host = request.POST.get("email_host")
            if host == "custom":
                host = request.POST.get("custom_email_host", "")

            port = int(request.POST.get("email_port", 587))
            username = request.POST.get("email_host_user", "")
            password = request.POST.get("email_host_password", "")
            use_tls = request.POST.get("email_use_tls") == "1"

            if not host or not username:
                return JsonResponse(
                    {"success": False, "error": "Заполните обязательные поля"}
                )

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


class DeliveryOrderCreateView(LoginRequiredMixin, CreateView):
    """Создание новой заявки на доставку"""

    model = DeliveryOrder
    template_name = "logistic/delivery_order_create_form.html"
    form_class = DeliveryOrderCreateForm

    def form_valid(self, form):
        form.instance.operator = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Заявка на доставку успешно создана!")
        return response

    def get_success_url(self):
        return reverse("delivery_order_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, "profile"):
            context["is_operator"] = self.request.user.profile.is_operator
            context["is_logistic"] = self.request.user.profile.is_logistic
            context["is_admin"] = self.request.user.profile.is_admin
        return context


@login_required
def get_operators(request):
    """API для получения списка операторов фулфилмента"""
    from django.contrib.auth.models import User

    operators = User.objects.filter(is_active=True, profile__role="operator").order_by(
        "first_name", "last_name", "username"
    )

    operators_list = []
    for operator in operators:
        operators_list.append(
            {
                "id": operator.id,
                "username": operator.username,
                "first_name": operator.first_name,
                "last_name": operator.last_name,
                "full_name": f"{operator.first_name} {operator.last_name}".strip()
                or operator.username,
                "fulfillment": (
                    operator.profile.fulfillment
                    if hasattr(operator, "profile")
                    else None
                ),
            }
        )

    return JsonResponse(operators_list, safe=False)


@login_required
def delivery_order_qr_pdf(request, pk):
    """Скачать QR-коды заявки на доставку в PDF формате (несколько QR-кодов по количеству мест)"""
    order = get_object_or_404(DeliveryOrder, pk=pk)

    if hasattr(request.user, "profile") and request.user.profile.is_operator:
        if order.operator != request.user:
            messages.error(request, "У вас нет доступа к этой заявке")
            return redirect("delivery_order_list")

    if not order.qr_code:
        order.generate_qr_code()

    if not order.qr_code:
        messages.error(request, "QR-код недоступен")
        return redirect("delivery_order_detail", pk=pk)

    try:
        qr_code_path = order.qr_code.path
        if not os.path.exists(qr_code_path):
            messages.error(request, "Файл QR-кода не найден")
            return redirect("delivery_order_detail", pk=pk)

        with open(qr_code_path, "rb") as f:
            qr_image_data = base64.b64encode(f.read()).decode("utf-8")

        client_name = order.get_recipient_display()
        if len(client_name) > 25:
            client_name = client_name[:22] + "..." 

        qr_items_html = ""
        items_per_page = 12  
        total_items = order.quantity

        page_width = 210  
        page_height = 297  
        margin = 10  

        cell_width = (page_width - 2 * margin) / 3 
        cell_height = (page_height - 2 * margin) / 4 

        qr_size = min(cell_width - 10, cell_height - 15) 

        for page_num in range(0, (total_items + items_per_page - 1) // items_per_page):
            qr_items_html += f'<div class="page page-{page_num + 1}">'

            for position in range(items_per_page):
                item_index = page_num * items_per_page + position
                if item_index >= total_items:
                    break

                i = item_index + 1 

                row = position // 3  
                col = position % 3  

                x = margin + col * cell_width + (cell_width - qr_size) / 2
                y = margin + row * cell_height + 5  

                qr_items_html += f"""
                <div class="qr-item" style="position: absolute; left: {x}mm; top: {y}mm; width: {qr_size}mm; height: {qr_size}mm;">
                    <div class="qr-header">Фулфилмент Царицыно</div>
                    <div class="qr-date">Дата: {order.date.strftime('%d.%m.%Y')}</div>
                    <img src="data:image/png;base64,{qr_image_data}" />
                    <div class="qr-client">Клиент: {client_name}</div>
                    <div class="qr-counter">{i} из {total_items}</div>
                </div>
                """

            qr_items_html += "</div>"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: A4 portrait;
                    margin: 0;
                }}
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    font-size: 7pt;
                }}
                .page {{
                    width: 210mm;
                    height: 297mm;
                    position: relative;
                    page-break-after: always;
                    border: 1px solid #ccc; /* Для визуализации границ страницы */
                }}
                .page:last-child {{
                    page-break-after: avoid;
                }}
                .qr-item {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    box-sizing: border-box;
                    padding: 3mm;
                    border: 0.5px solid #999;
                    background-color: white;
                    overflow: hidden;
                }}
                .qr-header {{
                    font-size: 8pt;
                    font-weight: bold;
                    margin-bottom: 1mm;
                    color: #000;
                    line-height: 1.2;
                }}
                .qr-date {{
                    font-size: 7pt;
                    margin-bottom: 2mm;
                    color: #333;
                    line-height: 1.2;
                }}
                .qr-item img {{
                    width: 80%;
                    height: auto;
                    max-width: 30mm;
                    max-height: 30mm;
                    margin: 1mm 0;
                }}
                .qr-client {{
                    font-size: 7pt;
                    margin: 1mm 0;
                    color: #000;
                    line-height: 1.2;
                    max-width: 100%;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .qr-counter {{
                    font-size: 7pt;
                    font-weight: bold;
                    margin-top: 1mm;
                    color: #000;
                    line-height: 1.2;
                }}
            </style>
        </head>
        <body>
            {qr_items_html}
        </body>
        </html>
        """

        html = HTML(string=html_content)
        pdf = html.write_pdf()

        if pdf:
            response = HttpResponse(pdf, content_type="application/pdf")
            filename = f"delivery_qr_{order.tracking_number or order.id}_{order.quantity}_places.pdf"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        else:
            messages.error(request, "Ошибка при генерации PDF")
            return redirect("delivery_order_detail", pk=pk)

    except Exception as e:
        print(f"❌ Ошибка при создании PDF с QR-кодами: {e}")
        import traceback

        traceback.print_exc()
        messages.error(request, f"Ошибка при создании PDF: {str(e)}")
        return redirect("delivery_order_detail", pk=pk)



@require_POST
@login_required
def bulk_update_delivery_orders(request):
    """Массовое обновление выбранных заявок"""
    try:
        if not (
            request.user.is_superuser
            or request.user.groups.filter(name="Логисты").exists()
        ):
            return JsonResponse(
                {"success": False, "error": "Нет прав на массовое редактирование"}
            )

        data = json.loads(request.body)
        order_ids = data.get("order_ids", [])
        field = data.get("field")
        value = data.get("value")

        if not order_ids:
            return JsonResponse({"success": False, "error": "Не выбраны заявки"})

        if not field:
            return JsonResponse(
                {"success": False, "error": "Не указано поле для обновления"}
            )

        allowed_fields = [
            "status",
            "driver_name",
            "driver_phone",
            "vehicle",
            "date",
            "fulfillment",
            "quantity",
            "weight",
            "volume",
        ]

        if field not in allowed_fields:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Поле не доступно для массового редактирования",
                }
            )

        orders = DeliveryOrder.objects.filter(id__in=order_ids)

        if hasattr(request.user, "profile") and request.user.profile.is_operator:
            orders = orders.filter(operator=request.user)

        if not orders.exists():
            return JsonResponse({"success": False, "error": "Заявки не найдены"})

        updated_count = 0
        for order in orders:
            try:
                if order.status == "shipped" and field != "status":
                    continue  

                if field in ["quantity"]:
                    new_value = int(value) if value else 0
                elif field in ["weight", "volume"]:
                    new_value = float(value) if value else 0.0
                elif field == "date":
                    try:
                        new_value = datetime.strptime(value, "%Y-%m-%d").date()
                    except ValueError:
                        continue
                elif field == "fulfillment":
                    if value:
                        from django.contrib.auth.models import User

                        try:
                            new_value = User.objects.get(id=value)
                        except User.DoesNotExist:
                            continue
                    else:
                        new_value = None
                else:
                    new_value = value

                setattr(order, field, new_value)
                order.save()
                updated_count += 1

            except Exception as e:
                print(f"Ошибка при обновлении заявки {order.id}: {e}")
                continue

        return JsonResponse(
            {
                "success": True,
                "updated_count": updated_count,
                "total_count": len(order_ids),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def delivery_orders_list_pdf(request):
    """Экспорт списка выбранных заявок на доставку в PDF (одним файлом)"""
    order_ids = request.GET.getlist("order_ids")

    if not order_ids:
        messages.error(request, "Не выбраны заявки для экспорта")
        return redirect("delivery_order_list")

    try:
        orders = DeliveryOrder.objects.filter(id__in=order_ids)

        if hasattr(request.user, "profile") and request.user.profile.is_operator:
            orders = orders.filter(operator=request.user)

        if not orders.exists():
            messages.error(request, "Не найдено заявок для экспорта")
            return redirect("delivery_order_list")

        pdf = create_delivery_orders_list_pdf(orders)

        if pdf:
            response = HttpResponse(pdf, content_type="application/pdf")
            filename = f"delivery_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        else:
            messages.error(request, "Ошибка при генерации PDF списка")
            return redirect("delivery_order_list")

    except Exception as e:
        print(f"❌ Ошибка при создании PDF списка: {e}")
        import traceback

        traceback.print_exc()
        messages.error(request, f"Ошибка при создании PDF списка: {str(e)[:100]}")
        return redirect("delivery_order_list")
