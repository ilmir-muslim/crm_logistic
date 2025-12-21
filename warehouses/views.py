from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from .models import City, Warehouse, WarehouseContainer


@require_GET
def get_cities_json(request):
    """Возвращает список городов в формате JSON"""
    cities = City.objects.all().order_by("name")
    data = [{"id": city.id, "name": str(city)} for city in cities]
    return JsonResponse(data, safe=False)


@require_GET
def get_warehouses_by_city_json(request, city_id):
    """Возвращает список складов для указанного города"""
    warehouses = Warehouse.objects.filter(city_id=city_id).order_by("name")
    data = [{"id": wh.id, "name": f"{wh.name} ({wh.city.name})"} for wh in warehouses]
    return JsonResponse(data, safe=False)


@require_GET
def get_warehouse_details_json(request, warehouse_id):
    """Возвращает детальную информацию о складе"""
    try:
        warehouse = Warehouse.objects.get(id=warehouse_id)
        data = {
            "id": warehouse.id,
            "name": warehouse.name,
            "city": warehouse.city.name,
            "address": warehouse.address,
            "phone": warehouse.phone,
            "email": warehouse.email or "",
            "working_hours": warehouse.get_working_hours(),
            "available_area": warehouse.available_area or 0,
            "total_area": warehouse.total_area or 0,
            "is_open_now": warehouse.is_open_now,
            "manager": (
                warehouse.manager.get_full_name()
                if warehouse.manager
                else "Не назначен"
            ),
        }
        return JsonResponse(data)
    except Warehouse.DoesNotExist:
        return JsonResponse({"error": "Склад не найден"}, status=404)


@require_GET
def get_available_containers_json(request, warehouse_id):
    """Возвращает доступные типы тары на складе"""
    try:
        containers = WarehouseContainer.objects.filter(
            warehouse_id=warehouse_id, available_quantity__gt=0
        ).select_related("container_type")

        data = [
            {
                "type_id": container.container_type.id,
                "name": container.container_type.name,
                "code": container.container_type.code,
                "category": container.container_type.category,
                "available": container.available_quantity,
                "volume": container.container_type.volume,
                "weight_capacity": container.container_type.weight_capacity,
                "is_reusable": container.container_type.is_reusable,
            }
            for container in containers
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
