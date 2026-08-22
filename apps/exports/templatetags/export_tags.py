"""Template tags for the Export Engine."""

from django import template

register = template.Library()


@register.filter
def sum_attr(queryset, attr_name):
    """Sum an attribute across a queryset."""
    return sum(getattr(obj, attr_name, 0) for obj in queryset)
