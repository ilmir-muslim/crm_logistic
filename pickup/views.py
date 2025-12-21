import json
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


from .models import PickupOrder
from .filters import PickupOrderFilter
from .forms import PickupOrderForm
from .pdf_utils import create_pickup_order_pdf


class PickupOrderListView(LoginRequiredMixin, ListView):
    model = PickupOrder
    template_name = "pickup/pickup_order_list.html"
    context_object_name = "orders"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        if hasattr(self.request.user, "profile"):
            user_profile = self.request.user.profile

            if user_profile.is_operator:
                queryset = queryset.filter(operator=self.request.user)

        # Применяем фильтр - ИСПРАВЛЕНО: было DeliveryOrderFilter
        self.filterset = PickupOrderFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = PickupOrderFilter(
            self.request.GET, queryset=self.get_queryset()
        )

        # Статистика
        queryset = self.get_queryset()
        context["total_orders"] = queryset.count()
        context["ready_orders"] = queryset.filter(status="ready").count()
        context["payment_orders"] = queryset.filter(status="payment").count()


        if hasattr(self.request.user, "profile"):
            context["user_role"] = self.request.user.profile.get_role_display()
            context["is_operator"] = self.request.user.profile.is_operator
            context["is_logistic"] = self.request.user.profile.is_logistic
            context["is_admin"] = self.request.user.profile.is_admin

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

    allowed_fields = [
        "invoice_number",
        "pickup_date",
        "pickup_time",
        "pickup_address",
        "contact_person",
        "client_name",
        "desired_delivery_date",
        "quantity",
        "status",
        "operator",  
    ]

    if field not in allowed_fields:
        return JsonResponse(
            {"success": False, "error": "Поле не доступно для редактирования"}
        )

    try:
        # Преобразование типов
        if field == "quantity":
            value = int(value)
        elif field == "pickup_date" and value:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        elif field == "pickup_time" and value:
            value = datetime.strptime(value, "%H:%M").time()
        elif field == "desired_delivery_date" and value:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        elif field == "operator":
            # Обработка поля operator (ForeignKey)
            if value:
                # Получаем объект User по ID
                from django.contrib.auth.models import User

                try:
                    value = User.objects.get(id=value)
                except User.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "error": "Пользователь не найден"}
                    )
            else:
                value = None  # Если значение пустое, устанавливаем None

        setattr(order, field, value)
        order.save()

        if field == "status":
            display_value = order.get_status_display()
            return JsonResponse({"success": True, "display_value": display_value})
        elif field == "operator":
            # Для оператора возвращаем имя для отображения
            display_value = ""
            if order.operator:
                display_value = (
                    order.operator.get_full_name() or order.operator.username
                )
            return JsonResponse({"success": True, "display_value": display_value})

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
    order_ids = request.GET.getlist("order_ids")

    if not order_ids:
        messages.error(request, "Не выбраны заявки для экспорта")
        return redirect("pickup_order_list")

    orders = PickupOrder.objects.filter(id__in=order_ids)

    if hasattr(request.user, "profile") and request.user.profile.is_operator:
        orders = orders.filter(operator=request.user)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for order in orders:
            pdf = create_pickup_order_pdf(order)
            if pdf:
                filename = f"pickup_{order.tracking_number or order.id}.pdf"
                zip_file.writestr(filename, pdf)

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="pickup_orders.zip"'
    return response


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
