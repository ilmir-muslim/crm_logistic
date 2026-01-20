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
    path(
        "api/public/search/",
        views.search_counterparties_public,
        name="counterparties_public_search",
    ),
    path(
        "api/public/<int:pk>/",
        views.get_counterparty_details_public,
        name="counterparty_details_public",
    ),
    path(
        "api/public/create/",
        views.create_counterparty_public,
        name="counterparty_create_public",
    ),
]
