from django.urls import path
from .views import PickupOrderFormView, DeliveryOrderFormView, order_success_view

urlpatterns = [
    path("pickup/", PickupOrderFormView.as_view(), name="pickup_order_form"),
    path("delivery/", DeliveryOrderFormView.as_view(), name="delivery_order_form"),
    path("success/", order_success_view, name="order_form_success"),
]
