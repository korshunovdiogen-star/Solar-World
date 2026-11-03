def parse_page_number(value, default=1):
    """Возвращает номер страницы, не падая на некорректном значении."""
    try:
        page = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, page)
