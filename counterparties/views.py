from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Counterparty
from counterparties import models


@require_GET
@login_required
def get_counterparties_json(request):
    """Возвращает список контрагентов в формате JSON"""
    search = request.GET.get("search", "")
    counterparty_type = request.GET.get("type", "")

    queryset = Counterparty.objects.filter(is_active=True)

    if search:
        queryset = queryset.filter(
            models.Q(name__icontains=search)
            | models.Q(full_name__icontains=search)
            | models.Q(inn__icontains=search)
            | models.Q(address__icontains=search)
        )

    if counterparty_type:
        queryset = queryset.filter(type=counterparty_type)

    data = []
    for counterparty in queryset.order_by("name")[
        :50
    ]:  # Ограничиваем количество для производительности
        data.append(
            {
                "id": counterparty.id,
                "name": counterparty.name,
                "full_name": counterparty.full_name or "",
                "type": counterparty.type,
                "type_display": counterparty.get_type_display(),
                "inn": counterparty.inn or "",
                "address": counterparty.address,
                "phone": counterparty.phone or "",
                "email": counterparty.email or "",
                "contact_person": counterparty.contact_person or "",
                "short_info": counterparty.get_short_info(),
                "full_info": counterparty.get_full_info(),
            }
        )

    return JsonResponse(data, safe=False)


@require_POST
@csrf_exempt
@login_required
def create_counterparty_api(request):
    """API для быстрого создания контрагента"""
    try:
        data = json.loads(request.body)

        counterparty = Counterparty.objects.create(
            type=data.get("type", "legal"),
            name=data.get("name", ""),
            full_name=data.get("full_name", ""),
            address=data.get("address", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            inn=data.get("inn", ""),
            kpp=data.get("kpp", ""),
            contact_person=data.get("contact_person", ""),
            created_by=request.user,
        )

        return JsonResponse(
            {
                "success": True,
                "id": counterparty.id,
                "name": counterparty.name,
                "short_info": counterparty.get_short_info(),
                "full_info": counterparty.get_full_info(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@require_GET
@login_required
def get_counterparty_details_json(request, pk):
    """Возвращает детальную информацию о контрагенте"""
    try:
        counterparty = Counterparty.objects.get(pk=pk, is_active=True)

        data = {
            "id": counterparty.id,
            "name": counterparty.name,
            "full_name": counterparty.full_name or "",
            "type": counterparty.type,
            "type_display": counterparty.get_type_display(),
            "address": counterparty.address,
            "actual_address": counterparty.actual_address or "",
            "phone": counterparty.phone or "",
            "email": counterparty.email or "",
            "inn": counterparty.inn or "",
            "kpp": counterparty.kpp or "",
            "ogrn": counterparty.ogrn or "",
            "contact_person": counterparty.contact_person or "",
            "director_name": counterparty.director_name or "",
            "bank_name": counterparty.bank_name or "",
            "bank_account": counterparty.bank_account or "",
            "full_info": counterparty.get_full_info(),
        }

        return JsonResponse(data)

    except Counterparty.DoesNotExist:
        return JsonResponse({"error": "Контрагент не найден"}, status=404)
