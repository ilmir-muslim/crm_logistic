import base64
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
        if "now" not in context:
            context["now"] = datetime.now()

        html_string = render_to_string(template_name, context)

        if hasattr(settings, "SITE_URL") and settings.SITE_URL:
            base_url = settings.SITE_URL
        else:
            base_url = "https://crm.gulnar8f.beget.tech"

        print(f"📄 Генерация PDF из шаблона {template_name}, base_url: {base_url}")

        html = HTML(string=html_string, base_url=base_url)

        stylesheets = []
        if css_string:
            stylesheets.append(CSS(string=css_string))

        pdf_bytes = html.write_pdf(stylesheets=stylesheets)

        print(f"✅ PDF успешно сгенерирован, размер: {len(pdf_bytes)} байт")
        return pdf_bytes

    except Exception as e:
        print(f"❌ Ошибка при генерации PDF: {e}")
        import traceback

        traceback.print_exc()

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


def generate_qr_code_pdf(qr_code_path):
    """
    Генерация PDF с чистым QR-кодом (без текста)
    """
    try:
        with open(qr_code_path, "rb") as f:
            qr_image_data = base64.b64encode(f.read()).decode("utf-8")

        html_string = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>QR-код</title>
            <style>
                @page {{
                    size: 100mm 100mm;
                    margin: 0;
                }}
                body {{
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                }}
                img {{
                    max-width: 90mm;
                    max-height: 90mm;
                }}
            </style>
        </head>
        <body>
            <img src="data:image/png;base64,{qr_image_data}" />
        </body>
        </html>
        """

        html = HTML(string=html_string, base_url=settings.SITE_URL)

        pdf_bytes = html.write_pdf()

        return pdf_bytes

    except Exception as e:
        print(f"❌ Ошибка при генерации PDF с QR-кодом: {e}")
        import traceback

        traceback.print_exc()
        return None
