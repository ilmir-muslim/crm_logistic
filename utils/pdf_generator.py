# utils/pdf_generator.py
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML, CSS
from datetime import datetime
import os


def generate_pdf_from_template(template_name, context, css_string=None):
    """
    Универсальная функция для генерации PDF из HTML-шаблона
    """
    try:
        # Добавляем текущее время в контекст
        if "now" not in context:
            context["now"] = datetime.now()

        # Рендерим HTML
        html_string = render_to_string(template_name, context)

        # На продакшене важно указать правильный base_url
        if hasattr(settings, "SITE_URL") and settings.SITE_URL:
            base_url = settings.SITE_URL
        else:
            # Для продакшена указываем домен
            base_url = "https://crm.gulnar8f.beget.tech"

        print(f"📄 Генерация PDF из шаблона {template_name}, base_url: {base_url}")

        html = HTML(string=html_string, base_url=base_url)

        # Если есть CSS, добавляем его
        stylesheets = []
        if css_string:
            stylesheets.append(CSS(string=css_string))

        # Генерируем PDF
        pdf_bytes = html.write_pdf(stylesheets=stylesheets)

        print(f"✅ PDF успешно сгенерирован, размер: {len(pdf_bytes)} байт")
        return pdf_bytes

    except Exception as e:
        print(f"❌ Ошибка при генерации PDF: {e}")
        import traceback

        traceback.print_exc()

        # Пробуем альтернативный способ без base_url
        try:
            print("🔄 Пробуем альтернативный способ генерации...")
            html_string = render_to_string(template_name, context)
            html = HTML(string=html_string)
            pdf_bytes = html.write_pdf()
            print(
                f"✅ PDF создан альтернативным способом, размер: {len(pdf_bytes)} байт"
            )
            return pdf_bytes
        except Exception as e2:
            print(f"❌ Альтернативный способ тоже не сработал: {e2}")
            return None


# Стили по умолчанию для PDF
DEFAULT_CSS = """
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif;
    font-size: 12px;
    line-height: 1.4;
    color: #000000;
}

h1 {
    font-size: 24px;
    color: #2c3e50;
    margin-bottom: 20px;
    text-align: center;
}

h2 {
    font-size: 18px;
    color: #34495e;
    margin: 15px 0 10px 0;
    border-bottom: 1px solid #ddd;
    padding-bottom: 5px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 11px;
}

table th {
    background-color: #f8f9fa;
    font-weight: bold;
    text-align: left;
    padding: 8px;
    border: 1px solid #dee2e6;
}

table td {
    padding: 8px;
    border: 1px solid #dee2e6;
}

.header {
    text-align: center;
    margin-bottom: 20px;
}

.footer {
    text-align: center;
    font-size: 10px;
    color: #666;
    margin-top: 20px;
}

.signature-block {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #000;
}

.signature-row {
    display: flex;
    justify-content: space-between;
    margin-top: 40px;
}

.signature-item {
    width: 45%;
    text-align: center;
}

.signature-line {
    border-top: 1px solid #000;
    width: 100%;
    margin: 10px 0;
}

.qr-code {
    text-align: center;
    margin: 20px 0;
}

.qr-code img {
    max-width: 150px;
    height: auto;
}

.text-bold {
    font-weight: bold;
}

.text-center {
    text-align: center;
}

.mb-3 {
    margin-bottom: 15px;
}

.page-break {
    page-break-before: always;
}

.no-print {
    display: none;
}

.company-info {
    text-align: center;
    margin-bottom: 20px;
    font-size: 14px;
}
"""


def generate_qr_code_pdf(order, order_type="pickup"):
    """
    Генерация PDF с QR-кодом для заявки
    """
    try:
        # Определяем заголовок в зависимости от типа заявки
        if order_type == "pickup":
            title = f"QR-код для заявки на забор #{order.tracking_number}"
            template_name = "qr_code_pdf.html"
        else:
            title = f"QR-код для заявки на доставку #{order.tracking_number}"
            template_name = "qr_code_pdf.html"

        # Получаем абсолютный URL QR-кода
        if order.qr_code and hasattr(order.qr_code, "url"):
            qr_code_url = order.qr_code.url
            if not qr_code_url.startswith("http"):
                # Если относительный URL, добавляем домен
                qr_code_url = f"{settings.SITE_URL}{qr_code_url}"
        else:
            qr_code_url = None

        context = {
            "order": order,
            "title": title,
            "now": datetime.now(),
            "qr_code_url": qr_code_url,
            "order_type": order_type,
            "MEDIA_URL": settings.MEDIA_URL,
        }

        # Используем специальный CSS для QR-кода
        qr_css = """
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #000000;
            text-align: center;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .qr-container {
            margin: 30px auto;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 10px;
            display: inline-block;
            background-color: #fff;
        }
        
        .qr-image {
            width: 300px;
            height: 300px;
            margin: 0 auto 20px;
        }
        
        .qr-image img {
            width: 100%;
            height: auto;
        }
        
        .order-info {
            margin-top: 30px;
            text-align: center;
            font-size: 14px;
        }
        
        .order-info table {
            width: 100%;
            max-width: 400px;
            margin: 20px auto;
            border-collapse: collapse;
        }
        
        .order-info th,
        .order-info td {
            padding: 8px;
            border: 1px solid #ddd;
            text-align: left;
        }
        
        .order-info th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        
        .footer {
            margin-top: 40px;
            font-size: 10px;
            color: #666;
            text-align: center;
        }
        
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 20px;
        }
        
        h2 {
            color: #34495e;
            margin: 20px 0 10px 0;
            font-size: 16px;
            text-align: center;
        }
        """

        # Генерируем PDF
        return generate_pdf_from_template(template_name, context, qr_css)

    except Exception as e:
        print(f"❌ Ошибка при генерации QR-кода PDF: {e}")
        import traceback

        traceback.print_exc()
        return None
