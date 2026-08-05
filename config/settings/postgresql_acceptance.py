"""Isolated PostgreSQL settings for compatibility and concurrency acceptance."""

import os

from django.core.exceptions import ImproperlyConfigured

from .development import *  # noqa: F403

POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
if not POSTGRES_PASSWORD:
    raise ImproperlyConfigured(
        "POSTGRES_PASSWORD must be set for PostgreSQL acceptance testing."
    )

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "sitadc_phase14_test"),
        "USER": os.getenv("POSTGRES_USER", "sitadc_phase14_test"),
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 0,
    }
}
