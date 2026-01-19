from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from logistic.views import (
    dashboard,
    reports_dashboard,
    generate_daily_report,
    statistics_report,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard, name="dashboard"),
    path("delivery/", include("logistic.urls")),
    path("pickup/", include("pickup.urls")),
    path("order/", include("order_form.urls")),
    path("reports/", reports_dashboard, name="reports_dashboard"),
    path("reports/daily/", generate_daily_report, name="generate_daily_report"),
    path("reports/statistics/", statistics_report, name="statistics_report"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="admin/login.html"),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(next_page="/accounts/login/"),
        name="logout",
    ),
    path("warehouses/", include("warehouses.urls")),
    path("counterparties/", include("counterparties.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


