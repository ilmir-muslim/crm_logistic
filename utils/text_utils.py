def normalize_search_text(text):
    """
    Нормализация текста для поиска:
    - Приводит к нижнему регистру
    - Убирает лишние пробелы
    - Заменяет ё на е (для русского языка)
    """
    if not text:
        return ""

    text = text.lower().strip()

    text = text.replace("ё", "е")

    text = " ".join(text.split())

    return text


def normalize_phone(phone):
    """
    Нормализация номера телефона для поиска
    """
    if not phone:
        return ""

    digits = "".join(filter(str.isdigit, phone))

    if digits.startswith("8"):
        digits = "7" + digits[1:]

    return digits
