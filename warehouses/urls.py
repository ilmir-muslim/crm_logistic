from django.urls import path
from . import views

urlpatterns = [
    path("api/cities/", views.get_cities_json, name="cities_json"),
    path(
        "api/warehouses/city/<int:city_id>/",
        views.get_warehouses_by_city_json,
        name="warehouses_by_city_json",
    ),
    path(
        "api/warehouses/<int:warehouse_id>/",
        views.get_warehouse_details_json,
        name="warehouse_details_json",
    ),
    path(
        "api/warehouses/<int:warehouse_id>/containers/",
        views.get_available_containers_json,
        name="available_containers_json",
    ),
    path("api/warehouses/", views.get_warehouses_json, name="warehouses_json"),
]
