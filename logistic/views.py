from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages
from .models import DeliveryOrder
from .filters import DeliveryOrderFilter


class DeliveryOrderListView(LoginRequiredMixin, ListView):
    model = DeliveryOrder
    template_name = "logistic/delivery_order_list.html"
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

        self.filterset = DeliveryOrderFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = DeliveryOrderFilter(
            self.request.GET, queryset=self.get_queryset()
        )

        # Добавляем информацию о роли пользователя в контекст
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

        # Оператор видит только свои заявки
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
        """Перенаправление после успешного сохранения"""
        return reverse("delivery_order_detail", kwargs={"pk": self.object.pk})

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
        context["can_edit"] = self.object.status != "shipped"
        return context

    def form_valid(self, form):
        # Блокировка редактирования отправленных заявок
        if self.object.status == "shipped":
            form.add_error(None, "Заявка уже отправлена. Редактирование запрещено.")
            return self.form_invalid(form)

        # Если статус меняется на "отправлено", устанавливаем сообщение
        if form.cleaned_data.get("status") == "shipped":
            messages.success(
                self.request,
                "Заявка отмечена как отправленная. Дальнейшее редактирование будет ограничено.",
            )

        response = super().form_valid(form)
        messages.success(self.request, "Данные водителя успешно обновлены!")
        return response
