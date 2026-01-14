from django.urls import path
from . import views

urlpatterns = [
    path(
        "api/counterparties/", views.get_counterparties_json, name="counterparties_json"
    ),
    path(
        "api/counterparties/create/",
        views.create_counterparty_api,
        name="create_counterparty_api",
    ),
    path(
        "api/counterparties/<int:pk>/",
        views.get_counterparty_details_json,
        name="counterparty_details_json",
    ),
]
