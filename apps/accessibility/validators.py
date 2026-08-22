"""Validators for the Accessibility Review module."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_contrast_ratio(value: float) -> None:
    """Validate that contrast ratio is within valid range."""
    if value < 1.0 or value > 21.0:
        raise ValidationError(
            _('Contrast ratio must be between 1.0 and 21.0.'),
            code='invalid_contrast_ratio',
        )


def validate_wcag_level(value: str) -> None:
    """Validate WCAG conformance level."""
    valid_levels = ['A', 'AA', 'AAA']
    if value not in valid_levels:
        raise ValidationError(
            _('WCAG level must be one of: %(levels)s') % {'levels': ', '.join(valid_levels)},
            code='invalid_wcag_level',
        )


def validate_hex_color(value: str) -> None:
    """Validate hex color format."""
    import re
    if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
        raise ValidationError(
            _('Color must be a valid hex color (e.g., #FF0000).'),
            code='invalid_hex_color',
        )


def validate_cron_expression(value: str) -> None:
    """Basic validation for cron expression."""
    parts = value.split()
    if len(parts) != 5:
        raise ValidationError(
            _('Cron expression must have 5 fields (minute hour day month weekday).'),
            code='invalid_cron',
        )
    # Basic range validation
    try:
        minute, hour, day, month, weekday = parts
        # This is a simplified check - in production you'd use a proper cron library
    except ValueError:
        raise ValidationError(
            _('Invalid cron expression format.'),
            code='invalid_cron',
        )


def validate_font_size_px(value: int) -> None:
    """Validate custom font size in pixels."""
    if value < 10 or value > 48:
        raise ValidationError(
            _('Font size must be between 10 and 48 pixels.'),
            code='invalid_font_size',
        )


def validate_line_height(value: float) -> None:
    """Validate line height multiplier."""
    if value < 1.0 or value > 3.0:
        raise ValidationError(
            _('Line height must be between 1.0 and 3.0.'),
            code='invalid_line_height',
        )


def validate_spacing(value: float) -> None:
    """Validate letter/word spacing in em."""
    if value < 0 or value > 1.0:
        raise ValidationError(
            _('Spacing must be between 0 and 1.0 em.'),
            code='invalid_spacing',
        )


def validate_report_retention_days(value: int) -> None:
    """Validate report retention days."""
    if value < 30 or value > 3650:
        raise ValidationError(
            _('Report retention must be between 30 and 3650 days.'),
            code='invalid_retention',
        )


def validate_notification_timing(value: str) -> None:
    """Validate notification timing option."""
    valid = ['IMMEDIATE', 'DELAYED_3S', 'DELAYED_5S', 'DELAYED_10S', 'PERSISTENT']
    if value not in valid:
        raise ValidationError(
            _('Invalid notification timing option.'),
            code='invalid_notification_timing',
        )
