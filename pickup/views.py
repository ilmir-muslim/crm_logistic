import base64
import json
import os
import zipfile
from io import BytesIO
from datetime import datetime
from django.db import transaction
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.decorators.http import require_POST
import qrcode
from weasyprint import HTML

from counterparties.models import Counterparty
from crm_logistic import settings
from utils.pdf_generator import generate_qr_code_pdf


from .models import PickupOrder
from .filters import PickupOrderFilter
from .forms import PickupOrderForm
from .pdf_utils import create_pickup_order_pdf, create_pickup_orders_list_pdf


class PickupOrderListView(LoginRequiredMixin, ListView):
    model = PickupOrder
    template_name = "pickup/pickup_order_list.html"
    context_object_name = "orders"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_authenticated and hasattr(self.request.user, "profile"):
            if self.request.user.profile.role == "operator":
                queryset = queryset.filter(operator=self.request.user)

        pickup_date_gte = self.request.GET.get("pickup_date__gte")
        pickup_date_lte = self.request.GET.get("pickup_date__lte")
        client_name = self.request.GET.get("client_name")
        pickup_address = self.request.GET.get("pickup_address")
        invoice_number = self.request.GET.get("invoice_number")
        status = self.request.GET.get("status")

        if pickup_date_gte:
            queryset = queryset.filter(pickup_date__gte=pickup_date_gte)
        if pickup_date_lte:
            queryset = queryset.filter(pickup_date__lte=pickup_date_lte)
        if client_name:
            queryset = queryset.filter(client_name__icontains=client_name)
        if pickup_address:
            queryset = queryset.filter(pickup_address__icontains=pickup_address)
        if invoice_number:
            queryset = queryset.filter(invoice_number__icontains=invoice_number)
        if status:
            queryset = queryset.filter(status=status)

        sort = self.request.GET.get("sort", "-pickup_date")
        order = self.request.GET.get("order", "desc")

        allowed_sort_fields = [
            "invoice_number",
            "pickup_date",
            "pickup_time",
            "pickup_address",
            "contact_person",
            "desired_delivery_date",
            "status",
            "client_name",
            "operator",
            "quantity",
        ]

        if sort in allowed_sort_fields:
            if order == "desc":
                sort_field = f"-{sort}"
            else:
                sort_field = sort
            queryset = queryset.order_by(sort_field)
        else:
            queryset = queryset.order_by("-pickup_date")

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
        context["sort"] = self.request.GET.get("sort", "pickup_date")
        context["order"] = self.request.GET.get("order", "desc")
        return context


class PickupOrderDetailView(LoginRequiredMixin, DetailView):
    model = PickupOrder
    template_name = "pickup/pickup_order_detail.html"
    context_object_name = "order"

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

        if hasattr(self.request.user, "profile"):
            context["is_operator"] = self.request.user.profile.is_operator
            context["is_logistic"] = self.request.user.profile.is_logistic
            context["is_admin"] = self.request.user.profile.is_admin

        return context


class PickupOrderCreateView(LoginRequiredMixin, CreateView):
    model = PickupOrder
    template_name = "pickup/pickup_order_form.html"
    form_class = PickupOrderForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["counterparties"] = Counterparty.objects.filter(
            is_active=True
        ).order_by("name")
        return context

    def form_valid(self, form):
        form.instance.operator = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Заявка на забор успешно создана!")
        return response

    def get_success_url(self):
        return reverse("pickup_order_detail", kwargs={"pk": self.object.pk})


class PickupOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = PickupOrder
    template_name = "pickup/pickup_order_form.html"
    form_class = PickupOrderForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["counterparties"] = Counterparty.objects.filter(
            is_active=True
        ).order_by("name")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        if (
            hasattr(self.request.user, "profile")
            and self.request.user.profile.is_operator
        ):
            queryset = queryset.filter(operator=self.request.user)

        return queryset

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Заявка успешно обновлена!")
        return response

    def get_success_url(self):
        return reverse("pickup_order_detail", kwargs={"pk": self.object.pk})


class ConvertToDeliveryView(LoginRequiredMixin, DetailView):
    model = PickupOrder
    template_name = "pickup/convert_to_delivery.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.is_convertible_to_delivery:
            messages.error(
                request,
                "Невозможно преобразовать заявку. Проверьте статус или наличие уже созданной доставки.",
            )
            return redirect("pickup_order_detail", pk=self.object.pk)

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.is_convertible_to_delivery:
            messages.error(
                request,
                "Невозможно преобразовать заявки. Проверьте статус или наличие уже созданной доставки.",
            )
            return redirect("pickup_order_detail", pk=self.object.pk)

        try:
            with transaction.atomic():
                delivery_order = self.object.create_delivery_order(request.user)

                if delivery_order:
                    messages.success(
                        request,
                        f"Заявка на доставку #{delivery_order.id} успешно создана на основе заявки на забор!",
                    )
                    return redirect("delivery_order_detail", pk=delivery_order.pk)
                else:
                    messages.error(request, "Ошибка при создании заявки на доставку.")
                    return redirect("pickup_order_detail", pk=self.object.pk)

        except Exception as e:
            messages.error(request, f"Ошибка: {str(e)}")
            return redirect("pickup_order_detail", pk=self.object.pk)


@require_POST
@login_required
def update_pickup_order_field(request, pk):
    """Обновление одного поля заявки на забор"""
    try:
        order = PickupOrder.objects.get(pk=pk)
    except PickupOrder.DoesNotExist:
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
        "invoice_number",
        "pickup_date",
        "pickup_time_from",
        "pickup_time_to",
        "pickup_address",
        "contact_person",
        "client_name",
        "desired_delivery_date",
        "quantity",
        "status",
        "operator",
        "receiving_warehouse",
    ]

    if field not in allowed_fields:
        return JsonResponse(
            {"success": False, "error": "Поле не доступно для редактирования"}
        )

    try:
        if field == "quantity":
            value = int(value) if value else 1
        elif field == "pickup_date" and value:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        elif field in ["pickup_time_from", "pickup_time_to"]:
            if value and value.strip():
                value = datetime.strptime(value, "%H:%M").time()
            else:
                value = None 
        elif field == "desired_delivery_date" and value:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        elif field == "operator":
            if value:
                try:
                    value = User.objects.get(id=value)
                except User.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "error": "Пользователь не найден"}
                    )
            else:
                value = None
        elif field == "receiving_warehouse":
            if value:
                try:
                    from warehouses.models import Warehouse

                    value = Warehouse.objects.get(id=value)
                except Warehouse.DoesNotExist:
                    return JsonResponse({"success": False, "error": "Склад не найден"})
            else:
                value = None

        setattr(order, field, value)
        order.save()

        if field == "status":
            display_value = order.get_status_display()
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "operator":
            display_value = ""
            if order.operator:
                display_value = (
                    order.operator.get_full_name() or order.operator.username
                )
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "receiving_warehouse":
            display_value = ""
            if order.receiving_warehouse:
                display_value = f"{order.receiving_warehouse.name} ({order.receiving_warehouse.city.name})"
            return JsonResponse({"success": True, "display_value": display_value})
        elif field in ["pickup_time_from", "pickup_time_to"]:
            return JsonResponse(
                {"success": True, "display_value": order.pickup_time_range}
            )
        elif field == "pickup_date":
            display_value = (
                order.pickup_date.strftime("%d.%m.%Y") if order.pickup_date else ""
            )
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "desired_delivery_date":
            display_value = (
                order.desired_delivery_date.strftime("%d.%m.%Y")
                if order.desired_delivery_date
                else ""
            )
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "invoice_number":
            display_value = value or ""
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "client_name":
            display_value = (
                (value[:20] + "...") if value and len(value) > 20 else (value or "")
            )
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "contact_person":
            display_value = (
                (value[:20] + "...")
                if value and len(value) > 20
                else (value or order.client_name or "")
            )
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "pickup_address":
            display_value = (
                (value[:30] + "...") if value and len(value) > 30 else (value or "")
            )
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "quantity":
            return JsonResponse({"success": True, "display_value": str(value)})

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def pickup_order_pdf(request, pk):
    order = get_object_or_404(PickupOrder, pk=pk)

    if hasattr(request.user, "profile") and request.user.profile.is_operator:
        if order.operator != request.user:
            messages.error(request, "У вас нет доступа к этой заявке")
            return redirect("pickup_order_list")

    pdf = create_pickup_order_pdf(order)

    if pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f"pickup_{order.tracking_number or order.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    else:
        messages.error(request, "Ошибка при генерации PDF")
        return redirect("pickup_order_detail", pk=pk)


def pickup_orders_bulk_pdf(request):
    """Экспорт выбранных заявок на забор в ZIP-архив"""
    order_ids = request.GET.getlist("order_ids")

    if not order_ids:
        messages.error(request, "Не выбраны заявки для экспорта")
        return redirect("pickup_order_list")

    try:
        orders = PickupOrder.objects.filter(id__in=order_ids)

        if hasattr(request.user, "profile") and request.user.profile.is_operator:
            orders = orders.filter(operator=request.user)

        if not orders.exists():
            messages.error(request, "Не найдено заявок для экспорта")
            return redirect("pickup_order_list")

        zip_buffer = BytesIO()
        success_count = 0

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for order in orders:
                try:
                    pdf = create_pickup_order_pdf(order)
                    if pdf:
                        filename = f"pickup_{order.tracking_number or order.id}.pdf"
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
            return redirect("pickup_order_list")

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="pickup_orders.zip"'

        print(f"✅ Создан архив с {success_count} файлами")
        return response

    except Exception as e:
        print(f"❌ Критическая ошибка при создании архива: {e}")
        import traceback

        traceback.print_exc()
        messages.error(request, f"Ошибка при создании архива: {str(e)[:100]}")
        return redirect("pickup_order_list")


@login_required
def get_operators(request):
    """API для получения списка операторов"""
    operators = User.objects.filter(
        is_active=True, profile__role__in=["operator", "logistic", "admin"]
    ).order_by("first_name", "last_name", "username")

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
            }
        )

    return JsonResponse(operators_list, safe=False)


def pickup_order_qr_pdf(request, pk):
    """Скачать QR-коды заявки на забор в PDF формате (по одному QR на страницу 75x120 мм)"""
    order = get_object_or_404(PickupOrder, pk=pk)

    if hasattr(request.user, "profile") and request.user.profile.is_operator:
        if order.operator != request.user:
            messages.error(request, "У вас нет доступа к этой заявке")
            return redirect("pickup_order_list")

    if not order.qr_code:
        order.generate_qr_code()

    if not order.qr_code:
        messages.error(request, "QR-код недоступен")
        return redirect("pickup_order_detail", pk=pk)

    try:
        qr_code_path = order.qr_code.path
        if not os.path.exists(qr_code_path):
            messages.error(request, "Файл QR-кода не найден")
            return redirect("pickup_order_detail", pk=pk)

        with open(qr_code_path, "rb") as f:
            qr_image_data = base64.b64encode(f.read()).decode("utf-8")

        sender_display = order.get_client_name() or "не указан"
        pickup_display = order.pickup_address or "не указан"
        delivery_display = order.delivery_address or "не указан"

        contact_person = order.contact_person or ""

        qr_items_html = ""
        total_items = order.quantity

        for i in range(1, total_items + 1):
            qr_items_html += f"""
            <div class="page">
                <div class="qr-container">
                    <div class="header-section">
                        <div class="company-name">Фулфилмент Царицыно</div>
                        <div class="order-header">
                            <div class="order-number">Заявка: {order.tracking_number or f"#{order.id}"}</div>
                            <div class="order-date">Дата: {order.pickup_date.strftime('%d.%m.%Y') if order.pickup_date else datetime.now().strftime('%d.%m.%Y')}</div>
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <div class="client-block">
                            <div class="info-label">Клиент:</div>
                            <div class="info-text">{sender_display}</div>
                        </div>
                        {f'<div class="contact-block"><div class="info-label">Контакты:</div><div class="info-text">{contact_person}</div></div>' if contact_person else ''}
                    </div>
                    
                    <div class="address-section">
                        <div class="address-block">
                            <div class="address-label">Откуда:</div>
                            <div class="address-text">{pickup_display}</div>
                        </div>
                        <div class="address-block">
                            <div class="address-label">Куда:</div>
                            <div class="address-text">{delivery_display}</div>
                        </div>
                    </div>
                    
                    <div class="qr-code-section">
                        <img src="data:image/png;base64,{qr_image_data}" class="qr-image" />
                    </div>
                    
                    <div class="footer-section">
                        <div class="counter">Место {i} из {total_items}</div>
                        <div class="cargo-info">
                            <div class="cargo-item">Мест: {order.quantity}</div>
                            <div class="cargo-item">Вес: {order.weight} кг</div>
                            <div class="cargo-item">Объем: {order.volume} м³</div>
                        </div>
                    </div>
                </div>
            </div>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: 75mm 120mm;
                    margin: 2mm;
                }}
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    font-size: 13px;
                    line-height: 1.1;
                }}
                .page {{
                    page-break-after: always;
                    width: 71mm;
                    height: 116mm;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                .page:last-child {{
                    page-break-after: avoid;
                }}
                .qr-container {{
                    width: 100%;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1mm;
                    box-sizing: border-box;
                    border: 0.5mm solid #ccc;
                    border-radius: 1mm;
                }}
                .header-section {{
                    width: 100%;
                    text-align: center;
                    margin-bottom: 0.5mm;
                }}
                .company-name {{
                    font-weight: bold;
                    font-size: 13px;
                    color: #000;
                    margin-bottom: 0.3mm;
                }}
                .order-header {{
                    display: flex;
                    justify-content: space-between;
                    font-size: 10px;
                    color: #444;
                }}
                .info-section {{
                    width: 100%;
                    margin-bottom: 0.5mm;
                }}
                .client-block, .contact-block {{
                    margin-bottom: 0.3mm;
                }}
                .info-label {{
                    font-weight: bold;
                    font-size: 13px;
                    color: #000;
                    margin-bottom: 0.1mm;
                }}
                .info-text {{
                    font-size: 13px;
                    color: #333;
                    word-break: break-word;
                }}
                .address-section {{
                    width: 100%;
                    margin-bottom: 1mm;
                }}
                .address-block {{
                    margin-bottom: 0.5mm;
                }}
                .address-label {{
                    font-weight: bold;
                    font-size: 13px;
                    color: #000;
                    margin-bottom: 0.2mm;
                }}
                .address-text {{
                    font-size: 13px;
                    color: #333;
                    word-break: break-word;
                    line-height: 1.2;
                }}
                .qr-code-section {{
                    flex-grow: 1;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    width: 100%;
                    margin: 0.5mm 0;
                }}
                .qr-image {{
                    width: 55mm;
                    height: 55mm;
                    max-width: 90%;
                    max-height: 90%;
                }}
                .footer-section {{
                    width: 100%;
                    text-align: center;
                }}
                .counter {{
                    font-size: 10px;
                    color: #000;
                    margin-bottom: 0.3mm;
                }}
                .cargo-info {{
                    width: calc(100% + 2mm); 
                    margin-left: -5mm;
                    margin-right: -5mm;
                    font-weight: bold;
                    display: flex;
                    justify-content: space-between;
                    font-size: 12px;
                    color: #000;
                    border-top: 0.3mm solid #eee;
                    padding-top: 0.3mm;
                    box-sizing: border-box;
                }}
                .cargo-item {{
                    flex: 1;
                    text-align: center;
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
            filename = f"pickup_qr_{order.tracking_number or order.id}_{order.quantity}_places.pdf"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        else:
            messages.error(request, "Ошибка при генерации PDF")
            return redirect("pickup_order_detail", pk=pk)

    except Exception as e:
        print(f"❌ Ошибка при создании PDF с QR-кодами для забора: {e}")
        import traceback

        traceback.print_exc()
        messages.error(request, f"Ошибка при создании PDF: {str(e)}")
        return redirect("pickup_order_detail", pk=pk)


@require_POST
@login_required
def bulk_update_pickup_orders(request):
    """Массовое обновление выбранных заявок на забор"""
    try:
        import json
        from datetime import datetime
        from django.http import JsonResponse
        from django.contrib.auth.models import User
        from warehouses.models import Warehouse

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

        orders = PickupOrder.objects.filter(id__in=order_ids)

        if hasattr(request.user, "profile") and request.user.profile.role == "operator":
            orders = orders.filter(operator=request.user)

        if not orders.exists():
            return JsonResponse(
                {"success": False, "error": "Заявки не найдены или нет прав доступа"}
            )

        allowed_bulk_fields = [
            "operator",
            "status",
            "receiving_warehouse",
            "receiving_operator",
            "pickup_date",
            "desired_delivery_date",
        ]

        if field not in allowed_bulk_fields:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Поле не доступно для массового редактирования",
                }
            )

        updated_count = 0

        for order in orders:
            try:
                if field == "operator":
                    if value:
                        try:
                            operator_value = User.objects.get(id=value)
                            order.operator = operator_value
                        except User.DoesNotExist:
                            continue
                    else:
                        order.operator = None

                elif field == "status":
                    if value in ["ready", "payment"]:
                        order.status = value

                elif field == "receiving_warehouse":
                    if value:
                        try:
                            warehouse_value = Warehouse.objects.get(id=value)
                            order.receiving_warehouse = warehouse_value
                        except Warehouse.DoesNotExist:
                            continue
                    else:
                        order.receiving_warehouse = None

                elif field == "receiving_operator":
                    if value:
                        try:
                            operator_value = User.objects.get(id=value)
                            order.receiving_operator = operator_value
                        except User.DoesNotExist:
                            continue
                    else:
                        order.receiving_operator = None

                elif field == "pickup_date":
                    if value:
                        try:
                            date_value = datetime.strptime(value, "%Y-%m-%d").date()
                            order.pickup_date = date_value
                        except ValueError:
                            continue
                    else:
                        order.pickup_date = None

                elif field == "desired_delivery_date":
                    if value:
                        try:
                            date_value = datetime.strptime(value, "%Y-%m-%d").date()
                            order.desired_delivery_date = date_value
                        except ValueError:
                            continue
                    else:
                        order.desired_delivery_date = None

                order.save()
                updated_count += 1

            except Exception as e:
                print(f"Ошибка при обновлении заявки {order.id}: {e}")
                continue

        return JsonResponse(
            {
                "success": True,
                "updated_count": updated_count,
                "message": f"Обновлено {updated_count} из {len(order_ids)} заявок",
            }
        )

    except Exception as e:
        print(f"Ошибка в bulk_update_pickup_orders: {e}")
        return JsonResponse({"success": False, "error": str(e)})


def pickup_orders_list_pdf(request):
    """Экспорт выбранных заявок на забор в один PDF файл (таблица)"""
    order_ids = request.GET.getlist("order_ids")

    if not order_ids:
        messages.error(request, "Не выбраны заявки для экспорта")
        return redirect("pickup_order_list")

    try:
        orders = PickupOrder.objects.filter(id__in=order_ids)

        if hasattr(request.user, "profile") and request.user.profile.is_operator:
            orders = orders.filter(operator=request.user)

        if not orders.exists():
            messages.error(request, "Не найдено заявок для экспорта")
            return redirect("pickup_order_list")

        orders = orders.order_by("pickup_date", "pickup_time_from")

        pdf = create_pickup_orders_list_pdf(orders)

        if pdf:
            response = HttpResponse(pdf, content_type="application/pdf")
            filename = (
                f'pickup_orders_list_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        else:
            messages.error(request, "Ошибка при генерации PDF")
            return redirect("pickup_order_list")

    except Exception as e:
        print(f"❌ Ошибка при создании списка PDF: {e}")
        import traceback

        traceback.print_exc()
        messages.error(request, f"Ошибка при создании PDF: {str(e)[:100]}")
        return redirect("pickup_order_list")
