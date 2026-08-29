from django import template

register = template.Library()


@register.filter
def add_class(field, css_class):
    """Add CSS class to a form field widget."""
    widget = field.field.widget if hasattr(field, "field") else field.widget
    existing_classes = widget.attrs.get("class", "")
    new_classes = f"{existing_classes} {css_class}" if existing_classes else css_class
    widget.attrs["class"] = new_classes
    return field
