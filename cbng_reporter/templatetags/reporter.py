from django import template
from django.utils import dateformat, timezone

register = template.Library()


@register.filter
def report_date(value):
    if not value:
        return ""
    return dateformat.format(timezone.localtime(value), r"l, \t\h\e jS \o\f F Y \a\t h:i:s A")
