from django.urls import path
from . import views

urlpatterns = [
    path("", views.DeliveryOrderListView.as_view(), name="delivery_order_list"),
    path(
        "<int:pk>/",
        views.DeliveryOrderDetailView.as_view(),
        name="delivery_order_detail",
    ),
    path(
        "<int:pk>/update/",
        views.DeliveryOrderUpdateView.as_view(),
        name="delivery_order_update",
    ),
]
