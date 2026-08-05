import re
from datetime import datetime, timedelta

from django.utils import timezone

from apps.core.utils.date_utils import get_current_time, is_past_date
from apps.core.utils.formatting_utils import format_currency
from apps.core.utils.reference_utils import generate_unique_reference


def test_get_current_time():
    now = get_current_time()
    assert isinstance(now, datetime)
    assert now.tzinfo is not None


def test_is_past_date():
    past = timezone.now() - timedelta(days=1)
    future = timezone.now() + timedelta(days=1)
    assert is_past_date(past) is True
    assert is_past_date(future) is False


def test_format_currency():
    assert format_currency(1234.56, "USD") == "1,234.56 USD"
    assert format_currency(1000, "ZMW") == "1,000.00 ZMW"


def test_generate_unique_reference():
    ref = generate_unique_reference("TEST")
    assert ref.startswith("TEST-")
    assert len(ref) == 13  # TEST- (5) + 8 chars

    # Should be uppercase alphanumeric after hyphen
    suffix = ref.split("-")[1]
    assert re.match(r"^[A-F0-9]{8}$", suffix)
