# pickup/pdf_utils.py
from utils.pdf_generator import generate_pdf_from_template, DEFAULT_CSS
from datetime import datetime


def create_pickup_order_pdf(pickup_order):
    """Создание PDF для заявки на забор"""
    context = {
        "order": pickup_order,
        "title": f"ЗАЯВКА НА ЗАБОР ГРУЗА #{pickup_order.tracking_number or pickup_order.id}",
        "now": datetime.now(),
    }

    # Используем функцию из utils
    return generate_pdf_from_template("pickup/pickup_pdf.html", context, DEFAULT_CSS)


def create_daily_pickup_report_pdf(date, orders):
    """Создание ежедневного отчета по заборам"""
    # Собираем статистику
    stats = {
        "total": len(orders),
        "new": len([o for o in orders if o.status == "new"]),
        "confirmed": len([o for o in orders if o.status == "confirmed"]),
        "picked_up": len([o for o in orders if o.status == "picked_up"]),
        "cancelled": len([o for o in orders if o.status == "cancelled"]),
        "total_weight": sum(o.weight for o in orders if o.weight),
        "total_volume": sum(o.volume for o in orders if o.volume),
        "total_quantity": sum(o.quantity for o in orders),
    }

    context = {
        "date": date,
        "orders": orders,
        "stats": stats,
        "title": f'ЕЖЕДНЕВНЫЙ ОТЧЕТ ПО ЗАБОРАМ за {date.strftime("%d.%m.%Y")}',
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

    return generate_pdf_from_template(
        "pickup/daily_pickup_report_pdf.html", context, landscape_css
    )
