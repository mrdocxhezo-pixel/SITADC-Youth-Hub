from datetime import datetime

from django.utils import timezone


def get_current_time():
    """Returns the current timezone-aware datetime."""
    return timezone.now()


def is_past_date(date_to_check: datetime) -> bool:
    """Checks if a given date is in the past."""
    return date_to_check < timezone.now()
