from django.urls import path
from . import views

urlpatterns = [
    path("", views.PickupOrderListView.as_view(), name="pickup_order_list"),
    path("create/", views.PickupOrderCreateView.as_view(), name="pickup_order_create"),
    path(
        "<int:pk>/", views.PickupOrderDetailView.as_view(), name="pickup_order_detail"
    ),
    path(
        "<int:pk>/edit/",
        views.PickupOrderUpdateView.as_view(),
        name="pickup_order_update",
    ),
    path(
        "<int:pk>/convert/",
        views.ConvertToDeliveryView.as_view(),
        name="convert_to_delivery",
    ),
    path("<int:pk>/pdf/", views.pickup_order_pdf, name="pickup_order_pdf"),
    path("bulk-pdf/", views.pickup_orders_bulk_pdf, name="pickup_orders_bulk_pdf"),
    # Добавлен новый путь для инлайн-редактирования
    path(
        "<int:pk>/update-field/",
        views.update_pickup_order_field,
        name="pickup_order_update_field",
    ),
    path("api/operators/", views.get_operators, name="get_operators"),
    path("<int:pk>/qr-pdf/", views.pickup_order_qr_pdf, name="pickup_order_qr_pdf"),
]
