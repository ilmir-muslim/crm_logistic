# utils/text_utils.py


def normalize_search_text(text):
    """
    Нормализация текста для поиска:
    - Приводит к нижнему регистру
    - Убирает лишние пробелы
    - Заменяет ё на е (для русского языка)
    """
    if not text:
        return ""

    # Приводим к нижнему регистру
    text = text.lower().strip()

    # Заменяем ё на е
    text = text.replace("ё", "е")

    # Убираем множественные пробелы
    text = " ".join(text.split())

    return text


def normalize_phone(phone):
    """
    Нормализация номера телефона для поиска
    """
    if not phone:
        return ""

    # Убираем все нецифровые символы
    digits = "".join(filter(str.isdigit, phone))

    # Если номер начинается с 8, заменяем на 7
    if digits.startswith("8"):
        digits = "7" + digits[1:]

    return digits
