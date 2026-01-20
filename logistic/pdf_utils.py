from datetime import datetime
from weasyprint import HTML
from django.conf import settings
from django.template.loader import render_to_string
from utils.pdf_generator import generate_pdf_from_template, DEFAULT_CSS


def create_delivery_order_pdf(delivery_order):
    """Создание PDF для заявки на доставку"""
    context = {
        "order": delivery_order,
        "title": f"НАКЛАДНАЯ НА ДОСТАВКУ #{delivery_order.tracking_number or delivery_order.id}",
        "now": datetime.now(),
    }

    return generate_pdf_from_template(
        "logistic/delivery_pdf.html", context, DEFAULT_CSS
    )


def create_daily_report_pdf(date, orders):
    """Создание ежедневного отчета по доставкам"""
    stats = {
        "total": len(orders),
        "submitted": len([o for o in orders if o.status == "submitted"]),
        "driver_assigned": len([o for o in orders if o.status == "driver_assigned"]),
        "shipped": len([o for o in orders if o.status == "shipped"]),
        "total_weight": sum(o.weight for o in orders),
        "total_volume": sum(o.volume for o in orders),
        "total_quantity": sum(o.quantity for o in orders),
    }

    context = {
        "date": date,
        "orders": orders,
        "stats": stats,
        "title": f'ЕЖЕДНЕВНЫЙ ОТЧЕТ ПО ДОСТАВКАМ за {date.strftime("%d.%m.%Y")}',
        "now": datetime.now(),
    }

    landscape_css = """
    @page {
        size: A4 landscape;
        margin: 1.5cm;
    }
    
    body {
        font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif;
        font-size: 11px;
    }
    
    table {
        font-size: 10px;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }
    
    .stat-item {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 10px;
        text-align: center;
    }
    
    .stat-label {
        font-size: 11px;
        color: #666;
    }
    
    .stat-value {
        font-size: 16px;
        font-weight: bold;
        color: #2c3e50;
    }
    """

    return generate_pdf_from_template(
        "logistic/daily_report_pdf.html", context, landscape_css
    )


def create_delivery_orders_list_pdf(orders):
    """Создание PDF со списком заявок на доставку"""
    context = {
        "orders": orders,
        "total_count": len(orders),
        "total_quantity": sum(o.quantity for o in orders),
        "total_weight": sum(o.weight for o in orders),
        "total_volume": sum(o.volume for o in orders),
        "title": f"СПИСОК ЗАЯВОК НА ДОСТАВКУ ({len(orders)} шт.)",
        "now": datetime.now(),
    }

    landscape_css = """
    @page {
        size: A4 landscape;
        margin: 1.5cm;
    }
    
    body {
        font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif;
        font-size: 10px;
    }
    
    .header {
        text-align: center;
        margin-bottom: 20px;
    }
    
    .title {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .subtitle {
        font-size: 12px;
        color: #666;
        margin-bottom: 15px;
    }
    
    .stats {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin-bottom: 20px;
        padding: 10px;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
    }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-label {
        font-size: 10px;
        color: #666;
    }
    
    .stat-value {
        font-size: 14px;
        font-weight: bold;
        color: #2c3e50;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 9px;
        margin-top: 10px;
    }
    
    table th {
        background-color: #343a40;
        color: white;
        font-weight: bold;
        padding: 6px 4px;
        text-align: left;
        border: 1px solid #dee2e6;
    }
    
    table td {
        padding: 5px 4px;
        border: 1px solid #dee2e6;
        vertical-align: top;
    }
    
    table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .status-badge {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 8px;
        font-weight: bold;
    }
    
    .status-submitted { background-color: #fff3cd; color: #856404; }
    .status-driver_assigned { background-color: #cce5ff; color: #004085; }
    .status-shipped { background-color: #d4edda; color: #155724; }
    
    .address-cell {
        max-width: 150px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .footer {
        margin-top: 30px;
        font-size: 9px;
        color: #666;
        text-align: center;
        border-top: 1px solid #dee2e6;
        padding-top: 10px;
    }
    """

    return generate_pdf_from_template(
        "logistic/delivery_list_pdf.html", context, landscape_css
    )


def generate_delivery_pdf(order):
    """Генерация PDF для заявки на доставку"""
    try:
        context = {
            "order": order,
            "now": datetime.now(),
            "MEDIA_URL": settings.MEDIA_URL,
        }

        html_string = render_to_string("logistic/delivery_pdf.html", context)

        html = HTML(string=html_string, base_url=settings.SITE_URL)

        pdf_bytes = html.write_pdf()

        return pdf_bytes

    except Exception as e:
        print(f"Ошибка при генерации PDF для доставки #{order.id}: {e}")
        return None


def generate_pickup_pdf(order):
    """Генерация PDF для заявки на забор"""
    try:
        context = {
            "order": order,
            "now": datetime.now(),
            "MEDIA_URL": settings.MEDIA_URL,
        }

        html_string = render_to_string("pickup/pickup_pdf.html", context)

        html = HTML(string=html_string, base_url=settings.SITE_URL)

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
