# [file name]: order_form/urls.py
from django.urls import path
from .views import ClientOrderFormView, order_success_view

urlpatterns = [
    path("", ClientOrderFormView.as_view(), name="client_order_form"),
    path("success/", order_success_view, name="order_form_success"),
    
]
