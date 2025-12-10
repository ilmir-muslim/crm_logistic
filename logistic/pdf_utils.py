# logistic/pdf_utils.py
from utils.pdf_generator import generate_pdf_from_template, DEFAULT_CSS
from datetime import datetime


def create_delivery_order_pdf(delivery_order):
    """Создание PDF для заявки на доставку"""
    context = {
        "order": delivery_order,
        "title": f"НАКЛАДНАЯ НА ДОСТАВКУ #{delivery_order.tracking_number or delivery_order.id}",
        "now": datetime.now(),
    }

    # Используем функцию из utils
    return generate_pdf_from_template(
        "logistic/delivery_pdf.html", context, DEFAULT_CSS
    )


def create_daily_report_pdf(date, orders):
    """Создание ежедневного отчета по доставкам"""
    # Собираем статистику
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

    # CSS для ландшафтной ориентации
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

    # Используем функцию из utils
    return generate_pdf_from_template(
        "logistic/daily_report_pdf.html", context, landscape_css
    )
