from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
from datetime import datetime
import os


def generate_delivery_pdf(order):
    """Генерация PDF для заявки на доставку"""
    try:
        # Рендерим HTML
        context = {
            "order": order,
            "now": datetime.now(),
            "MEDIA_URL": settings.MEDIA_URL,
        }

        html_string = render_to_string("logistic/delivery_pdf.html", context)

        # Создаем HTML объект
        html = HTML(string=html_string, base_url=settings.SITE_URL)

        # Генерируем PDF
        pdf_bytes = html.write_pdf()

        return pdf_bytes

    except Exception as e:
        print(f"Ошибка при генерации PDF для доставки #{order.id}: {e}")
        return None


def generate_pickup_pdf(order):
    """Генерация PDF для заявки на забор"""
    try:
        # Рендерим HTML
        context = {
            "order": order,
            "now": datetime.now(),
            "MEDIA_URL": settings.MEDIA_URL,
        }

        html_string = render_to_string("pickup/pickup_pdf.html", context)

        # Создаем HTML объект
        html = HTML(string=html_string, base_url=settings.SITE_URL)

        # Генерируем PDF
        pdf_bytes = html.write_pdf()

        return pdf_bytes

    except Exception as e:
        print(f"Ошибка при генерации PDF для забора #{order.id}: {e}")
        return None


def generate_daily_report_pdf(date, orders, report_type="delivery"):
    """Генерация ежедневного отчета"""
    try:
        if report_type == "delivery":
            template = "logistic/daily_report_pdf.html"
        else:
            template = "pickup/daily_report_pdf.html"

        # Статистика
        stats = {
            "total": len(orders),
            "submitted": len([o for o in orders if o.status == "submitted"]),
            "driver_assigned": len(
                [o for o in orders if o.status == "driver_assigned"]
            ),
            "shipped": len([o for o in orders if o.status == "shipped"]),
            "total_weight": sum(o.weight for o in orders),
            "total_volume": sum(o.volume for o in orders),
            "total_quantity": sum(o.quantity for o in orders),
        }

        context = {
            "date": date,
            "orders": orders,
            "stats": stats,
            "now": datetime.now(),
            "report_type": report_type,
        }

        html_string = render_to_string(template, context)
        html = HTML(string=html_string, base_url=settings.SITE_URL)
        pdf_bytes = html.write_pdf()

        return pdf_bytes

    except Exception as e:
        print(f"Ошибка при генерации отчета: {e}")
        return None
