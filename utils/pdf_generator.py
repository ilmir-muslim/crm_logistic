# utils/pdf_generator.py
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML, CSS
from datetime import datetime
import os


def generate_pdf_from_template(template_name, context, css_string=None):
    """
    Универсальная функция для генерации PDF из HTML-шаблона

    Args:
        template_name: путь к HTML-шаблону
        context: контекст для шаблона
        css_string: дополнительный CSS (опционально)

    Returns:
        bytes: PDF-файл в бинарном виде
    """
    try:
        # Добавляем текущее время в контекст
        if "now" not in context:
            context["now"] = datetime.now()

        # Рендерим HTML
        html_string = render_to_string(template_name, context)

        # Создаем HTML объект с базовым URL
        base_url = getattr(settings, "SITE_URL", "http://localhost:8000")
        html = HTML(string=html_string, base_url=base_url)

        # Если есть CSS, добавляем его
        stylesheets = []
        if css_string:
            stylesheets.append(CSS(string=css_string))

        # Генерируем PDF
        pdf_bytes = html.write_pdf(stylesheets=stylesheets)

        return pdf_bytes

    except Exception as e:
        print(f"Ошибка при генерации PDF: {e}")
        import traceback

        traceback.print_exc()
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
