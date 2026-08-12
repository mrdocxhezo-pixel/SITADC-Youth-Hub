"""Validation helpers for the MEAL module.

Document and image uploads reuse the proven Phase 15 validators so the
allowed-file policy stays in a single place.
"""

from __future__ import annotations

from apps.programs.validators import (  # noqa: F401  (re-exported)
    validate_date_range,
    validate_percentage,
)
