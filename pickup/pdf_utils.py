from utils.pdf_generator import generate_pdf_from_template, DEFAULT_CSS
from datetime import datetime


def create_pickup_order_pdf(pickup_order):
    """Создание PDF для заявки на забор"""
    try:
        context = {
            "order": pickup_order,
            "title": f"ЗАЯВКА НА ЗАБОР ГРУЗА #{pickup_order.tracking_number or pickup_order.id}",
            "now": datetime.now(),
        }

        return generate_pdf_from_template(
            "pickup/pickup_pdf.html", context, DEFAULT_CSS
        )
    except Exception as e:
        print(f"❌ Ошибка в create_pickup_order_pdf для заявки {pickup_order.id}: {e}")
        import traceback

        traceback.print_exc()
        return None


def create_daily_pickup_report_pdf(date, orders):
    """Создание ежедневного отчета по заборам"""
    stats = {
        "total": len(orders),
        "ready": len([o for o in orders if o.status == "ready"]),
        "payment": len([o for o in orders if o.status == "payment"]),
        "accepted": len([o for o in orders if o.status == "accepted"]),
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


def create_pickup_orders_list_pdf(orders):
    """Создание PDF со списком заявок на забор в виде таблицы"""
    try:
        context = {
            "orders": orders,
            "title": "СПИСОК ЗАЯВОК НА ЗАБОР ГРУЗА",
            "now": datetime.now(),
            "total_count": len(orders),
            "total_quantity": sum(o.quantity for o in orders),
            "total_weight": sum(o.weight for o in orders if o.weight),
            "total_volume": sum(o.volume for o in orders if o.volume),
        }

        landscape_css = """
        @page {
            size: A4 landscape;
            margin: 1.5cm;
        }
        
        body {
            font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif;
            font-size: 9px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 8px;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 4px 6px;
            text-align: left;
        }
        
        th {
            background-color: #f2f2f2;
            font-weight: bold;
            white-space: nowrap;
        }
        
        h1 {
            text-align: center;
            font-size: 16px;
            margin-bottom: 10px;
        }
        
        .summary {
            margin-bottom: 15px;
            padding: 10px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }
        
        .summary-item {
            display: inline-block;
            margin-right: 20px;
        }
        
        .summary-label {
            font-weight: bold;
            color: #495057;
        }
        
        .summary-value {
            color: #2c3e50;
            font-weight: bold;
        }
        
        .status-ready { 
            color: #0dcaf0; 
            font-weight: bold;
        }
        
        .status-payment { 
            color: #ffc107; 
            font-weight: bold;
        }
        
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        .page-break {
            page-break-after: always;
        }
        """

        return generate_pdf_from_template(
            "pickup/pickup_orders_list_pdf.html", context, landscape_css
        )
    except Exception as e:
        print(f"❌ Ошибка в create_pickup_orders_list_pdf: {e}")
        import traceback

        traceback.print_exc()
        return None
