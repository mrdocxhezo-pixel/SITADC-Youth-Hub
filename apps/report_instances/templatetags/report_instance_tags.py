"""Template tags for the ``report_instances`` app."""

from django import template

register = template.Library()


@register.filter(name="split")
def split(value, delimiter=" "):
    """Split a string into a list using ``delimiter``.

    Enables membership tests such as::

        {% if report.status in "DRAFT IN_PROGRESS"|split:" " %}
    """
    if not value:
        return []
    return str(value).split(delimiter)


@register.filter(name="replace")
def replace(value, args):
    """Replace occurrences of a substring.

    Accepts either ``replace:"old,new"`` or ``replace:"old","new"`` (the
    comma-separated form is parsed by the template engine as a tuple).
    Falls back to replacing with a space when no replacement is given.
    """
    if isinstance(args, tuple):
        old, new = (args + ("",))[:2]
    else:
        old, _, new = str(args).partition(",")
    return str(value).replace(old, new)
