"""Template tags and filters for the settings app."""

from django import template

register = template.Library()

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


@register.filter
def weekday_name(value):
    """Return the weekday name for an integer index (0 = Monday)."""
    try:
        return WEEKDAYS[int(value)]
    except (TypeError, ValueError, IndexError):
        return WEEKDAYS[0]


@register.filter
def exclude(sessions, session_key):
    """Return sessions whose ``session_key`` differs from the given key."""
    return [s for s in sessions if s.session_key != session_key]