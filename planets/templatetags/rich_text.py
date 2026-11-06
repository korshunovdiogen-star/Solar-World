import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

from solarWorld.security import sanitize_rich_text

register = template.Library()


@register.filter(name="rich_text")
def rich_text(value):
    return sanitize_rich_text(value)


@register.simple_tag(name="versioned_static")
def versioned_static(path):
    """
    Ссылка на статический файл с автоматической версией.

    Версия — время последнего изменения файла. Браузер не держит
    старую копию после правок, а цифру в шаблоне менять не нужно.
    """
    url = static(path)
    absolute_path = finders.find(path)
    if not absolute_path:
        return url

    try:
        version = int(os.path.getmtime(absolute_path))
    except OSError:
        return url

    return f"{url}?v={version}"
