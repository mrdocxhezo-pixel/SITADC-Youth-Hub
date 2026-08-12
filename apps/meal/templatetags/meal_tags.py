"""Template filters for rendering MEAL record fields safely."""

from django import template

register = template.Library()


@register.filter
def fields_with_labels(instance):
    """Return ``(verbose_name, field_name)`` pairs for a record's fields."""
    return [(field.verbose_name, field.name) for field in instance._meta.fields]


@register.filter
def record_history(instance, limit=8):
    """Return recent immutable status history rows for a record."""
    from apps.meal.models import MEALStatusHistory

    return MEALStatusHistory.objects.filter(
        entity_type=type(instance).__name__, entity_id=str(instance.pk)
    )[:limit]


@register.filter
def field_value(instance, name):
    """Return a human-friendly value for a record field."""
    display = getattr(instance, f"get_{name}_display", None)
    if callable(display):
        return display()
    value = getattr(instance, name, None)
    if value is None:
        return ""
    if hasattr(value, "url"):
        return "File attached"
    if hasattr(value, "full_name") and callable(value.full_name):
        return value.full_name
    return value
