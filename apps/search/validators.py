"""Validators and normalization helpers for Enterprise Search inputs."""

from __future__ import annotations

from django.utils.translation import gettext as _

from .constants import (
    ENTITY_TYPE_KEYS,
    MAX_QUERY_LENGTH,
    MIN_QUERY_LENGTH,
    TERM_SEQUENCE_RESERVED,
)
from .exceptions import SearchValidationError


def _is_authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def normalize_query(value: str | None) -> str:
    """Trim and collapse whitespace in a raw search term."""
    if value is None:
        return ""
    return " ".join(value.split())


def validate_query(value: str) -> str:
    """Validate a search query against length and content rules."""
    cleaned = normalize_query(value)
    if not cleaned:
        raise SearchValidationError(_("Enter a search term."))
    if len(cleaned) < MIN_QUERY_LENGTH:
        raise SearchValidationError(
            _("Search terms must be at least %s characters long.") % MIN_QUERY_LENGTH
        )
    if len(cleaned) > MAX_QUERY_LENGTH:
        raise SearchValidationError(
            _("Search terms may not exceed %s characters.") % MAX_QUERY_LENGTH
        )
    if any(ch in cleaned for ch in TERM_SEQUENCE_RESERVED):
        raise SearchValidationError(_("Search terms may not contain special symbols."))
    return cleaned


def validate_entity_type_keys(value) -> list[str]:
    """Validate and deduplicate entity type keys, raising for unknown keys."""
    keys = list(value or [])
    normalized: list[str] = []
    seen: set[str] = set()
    for key in keys:
        if not isinstance(key, str) or not key:
            raise SearchValidationError(_("Invalid entity type key."))
        if key not in ENTITY_TYPE_KEYS:
            raise SearchValidationError(
                _("Unknown entity type: %(key)s.") % {"key": key}
            )
        if key not in seen:
            seen.add(key)
            normalized.append(key)
    return normalized


def coerce_entity_type_keys(value) -> list[str]:
    """Coerce raw request input into validated entity type keys.

    Unknown keys are dropped rather than rejected so a single shared form can
    be driven by ``data`` coming from GET query strings or POST bodies.
    """
    if value is None:
        return []
    if isinstance(value, str):
        raw = [part.strip() for part in value.split(",") if part.strip()]
    else:
        raw = [str(item).strip() for item in value if str(item).strip()]
    return [key for key in raw if key in ENTITY_TYPE_KEYS]
