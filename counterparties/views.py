import json
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
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


@require_GET
def search_counterparties_public(request):
    """Поиск контрагентов для публичных форм (без авторизации)"""
    search_term = request.GET.get("search", "")
    limit = request.GET.get("limit", 10)

    if not search_term or len(search_term) < 2:
        return JsonResponse([], safe=False)

    try:
        limit = int(limit)
    except ValueError:
        limit = 10

    # Ищем по всем полям
    queryset = Counterparty.objects.filter(is_active=True).filter(
        Q(name__icontains=search_term)
        | Q(full_name__icontains=search_term)
        | Q(inn__icontains=search_term)
        | Q(phone__icontains=search_term)
        | Q(email__icontains=search_term)
    )[:limit]

    results = []
    for counterparty in queryset:
        results.append(
            {
                "id": counterparty.id,
                "name": counterparty.name,
                "full_name": counterparty.full_name or "",
                "type": counterparty.type,
                "inn": counterparty.inn or "",
                "kpp": counterparty.kpp or "",
                "address": counterparty.address,
                "actual_address": counterparty.actual_address or "",
                "phone": counterparty.phone or "",
                "email": counterparty.email or "",
                "contact_person": counterparty.contact_person or "",
                "director_name": counterparty.director_name or "",
                "short_info": counterparty.get_short_info(),
            }
        )

    return JsonResponse(results, safe=False)


@require_GET
def get_counterparty_details_public(request, pk):
    """Получение детальной информации о контрагенте для публичных форм"""
    try:
        counterparty = Counterparty.objects.get(pk=pk, is_active=True)

        data = {
            "id": counterparty.id,
            "name": counterparty.name,
            "full_name": counterparty.full_name or "",
            "type": counterparty.type,
            "inn": counterparty.inn or "",
            "kpp": counterparty.kpp or "",
            "ogrn": counterparty.ogrn or "",
            "address": counterparty.address,
            "actual_address": counterparty.actual_address or "",
            "phone": counterparty.phone or "",
            "email": counterparty.email or "",
            "contact_person": counterparty.contact_person or "",
            "director_name": counterparty.director_name or "",
            "passport_series": counterparty.passport_series or "",
            "passport_number": counterparty.passport_number or "",
            "passport_issued_by": counterparty.passport_issued_by or "",
            "passport_issued_date": counterparty.passport_issued_date or "",
            "bank_name": counterparty.bank_name or "",
            "bank_account": counterparty.bank_account or "",
        }

        return JsonResponse(data)

    except Counterparty.DoesNotExist:
        return JsonResponse({"error": "Контрагент не найден"}, status=404)


@require_POST
@csrf_exempt
def create_counterparty_public(request):
    """Создание нового контрагента из публичной формы"""
    try:
        data = json.loads(request.body)

        # Создаем контрагента
        counterparty = Counterparty.objects.create(
            type=data.get("type", "legal"),
            name=data.get("name", ""),
            full_name=data.get("full_name", ""),
            address=data.get("address", ""),
            actual_address=data.get("actual_address", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            inn=data.get("inn", ""),
            kpp=data.get("kpp", ""),
            ogrn=data.get("ogrn", ""),
            contact_person=data.get("contact_person", ""),
            director_name=data.get("director_name", ""),
            passport_series=data.get("passport_series", ""),
            passport_number=data.get("passport_number", ""),
            passport_issued_by=data.get("passport_issued_by", ""),
            passport_issued_date=data.get("passport_issued_date", ""),
            bank_name=data.get("bank_name", ""),
            bank_account=data.get("bank_account", ""),
            is_customer=True,  # Помечаем как покупателя
            notes="Создано через веб-форму заявки",
            created_by=None,  # Для публичных форм создатель не указывается
        )

        return JsonResponse(
            {
                "success": True,
                "id": counterparty.id,
                "name": counterparty.name,
                "short_info": counterparty.get_short_info(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
