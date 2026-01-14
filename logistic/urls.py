from django.urls import path
from . import views

urlpatterns = [
    path("", views.DeliveryOrderListView.as_view(), name="delivery_order_list"),
    path(
        "create/", views.DeliveryOrderCreateView.as_view(), name="delivery_order_create"
    ),
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
    path("<int:pk>/pdf/", views.delivery_order_pdf, name="delivery_order_pdf"),
    path("daily-report/pdf/", views.daily_report_pdf, name="daily_report_pdf"),
    path("bulk-pdf/", views.delivery_orders_bulk_pdf, name="delivery_orders_bulk_pdf"),
    path("email-settings/", views.email_settings_view, name="email_settings"),
    path(
        "test-email-connection/",
        views.test_email_connection,
        name="test_email_connection",
    ),
    path(
        "<int:pk>/update-field/",
        views.update_delivery_order_field,
        name="delivery_order_update_field",
    ),
    path("reports/", views.reports_dashboard, name="reports_dashboard"),
    path("reports/daily/", views.generate_daily_report, name="generate_daily_report"),
    path("reports/statistics/", views.statistics_report, name="statistics_report"),
    path("get-operators/", views.get_operators, name="get_operators"),
    path(
        "delivery/<int:pk>/update-field/",
        views.update_delivery_order_field,
        name="delivery_order_update_field",
    ),
    path("<int:pk>/qr-pdf/", views.delivery_order_qr_pdf, name="delivery_order_qr_pdf"),
]
