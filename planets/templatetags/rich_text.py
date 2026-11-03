from django import template

from solarWorld.security import sanitize_rich_text


register = template.Library()


@register.filter(name='rich_text')
def rich_text(value):
    return sanitize_rich_text(value)
