from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from .models import PickupOrder
from .filters import PickupOrderFilter
from logistic.models import DeliveryOrder


class PickupOrderListView(LoginRequiredMixin, ListView):
    model = PickupOrder
    template_name = "pickup/pickup_order_list.html"
    context_object_name = "orders"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Определяем роль пользователя
        if hasattr(self.request.user, "profile"):
            user_profile = self.request.user.profile

            # Оператор видит только свои заявки
            if user_profile.is_operator:
                queryset = queryset.filter(operator=self.request.user)

        self.filterset = PickupOrderFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = PickupOrderFilter(
            self.request.GET, queryset=self.get_queryset()
        )

        # Добавляем информацию о роли пользователя
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

        # Оператор видит только свои заявки
        if (
            hasattr(self.request.user, "profile")
            and self.request.user.profile.is_operator
        ):
            queryset = queryset.filter(operator=self.request.user)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Добавляем информацию о роли пользователя
        if hasattr(self.request.user, "profile"):
            context["is_operator"] = self.request.user.profile.is_operator
            context["is_logistic"] = self.request.user.profile.is_logistic
            context["is_admin"] = self.request.user.profile.is_admin

        return context


class PickupOrderCreateView(LoginRequiredMixin, CreateView):
    model = PickupOrder
    template_name = "pickup/pickup_order_form.html"
    fields = [
        "pickup_date",
        "pickup_address",
        "client_name",
        "client_phone",
        "client_email",
        "quantity",
        "weight",
        "volume",
        "cargo_description",
        "special_requirements",
        "status",
    ]

    def form_valid(self, form):
        # Назначаем текущего пользователя оператором
        form.instance.operator = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Заявка на забор успешно создана!")
        return response

    def get_success_url(self):
        return reverse("pickup_order_detail", kwargs={"pk": self.object.pk})


class PickupOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = PickupOrder
    template_name = "pickup/pickup_order_form.html"
    fields = [
        "pickup_date",
        "pickup_address",
        "client_name",
        "client_phone",
        "client_email",
        "quantity",
        "weight",
        "volume",
        "cargo_description",
        "special_requirements",
        "status",
        "notes",
    ]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Оператор видит только свои заявки
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
    """Преобразование заявки на забор в заявку на доставку"""

    model = PickupOrder
    template_name = "pickup/convert_to_delivery.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Проверяем, можно ли преобразовать
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
                "Невозможно преобразовать заявку. Проверьте статус или наличие уже созданной доставки.",
            )
            return redirect("pickup_order_detail", pk=self.object.pk)

        # Создаём заявку на доставку
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
