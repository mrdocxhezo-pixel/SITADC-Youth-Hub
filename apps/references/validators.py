"""
Reusable validation helpers for the reference numbering module.

These validators are shared by model ``clean()`` methods, services, forms and
management commands so numbering invariants are enforced consistently.
"""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

TOKEN_RE = re.compile(r"\{([A-Z_]+)\}")

SUPPORTED_TOKENS: frozenset[str] = frozenset(
    {
        "PREFIX",
        "ORG",
        "MODULE",
        "TYPE",
        "UNIT",
        "DIRECTORATE",
        "REGION",
        "DISTRICT",
        "COMMUNITY",
        "TEAM",
        "PROGRAM",
        "PROJECT",
        "YEAR",
        "YEAR_SHORT",
        "MONTH",
        "DAY",
        "FY",
        "SEQUENCE",
    }
)

# Regex fragments used to validate a rendered reference against a scheme.
# ``SEQUENCE`` is handled separately because its width depends on the scheme.
_TOKEN_REGEX: dict[str, str] = {
    "PREFIX": r"[A-Z]{2,10}",
    "ORG": r"[A-Z0-9]{2,20}",
    "MODULE": r"[a-z]+",
    "TYPE": r"[A-Za-z0-9_-]*",
    "UNIT": r"[A-Za-z0-9_-]*",
    "DIRECTORATE": r"[A-Za-z0-9_-]*",
    "REGION": r"[A-Za-z0-9_-]*",
    "DISTRICT": r"[A-Za-z0-9_-]*",
    "COMMUNITY": r"[A-Za-z0-9_-]*",
    "TEAM": r"[A-Za-z0-9_-]*",
    "PROGRAM": r"[A-Za-z0-9_-]*",
    "PROJECT": r"[A-Za-z0-9_-]*",
    "YEAR": r"\d{4}",
    "YEAR_SHORT": r"\d{2}",
    "MONTH": r"\d{2}",
    "DAY": r"\d{2}",
    "FY": r"\d{4}-\d{2}",
}


def validate_prefix(value: str) -> None:
    """Raise unless the prefix is 2-10 uppercase letters."""
    if not re.fullmatch(r"[A-Z]{2,10}", value):
        raise ValidationError(
            _("Prefix must be 2-10 uppercase letters (A-Z)."),
            code="invalid_reference_prefix",
        )


def validate_organization_code(value: str) -> None:
    """Raise unless the organization code is 2-20 uppercase letters/digits."""
    if not re.fullmatch(r"[A-Z0-9]{2,20}", value):
        raise ValidationError(
            _("Organization code must be 2-20 uppercase letters or digits."),
            code="invalid_organization_code",
        )


def validate_sequence_length(value: int) -> None:
    """Raise unless the sequence width is between 1 and 12 digits."""
    if not 1 <= value <= 12:
        raise ValidationError(
            _("Sequence length must be between 1 and 12."),
            code="invalid_sequence_length",
        )


def validate_pattern(value: str) -> None:
    """Raise unless the pattern uses only supported tokens and has PREFIX+SEQUENCE."""
    tokens = TOKEN_RE.findall(value)
    unknown = set(tokens) - SUPPORTED_TOKENS
    if unknown:
        raise ValidationError(
            _("Pattern contains unsupported tokens: %(tokens)s.")
            % {"tokens": ", ".join(sorted(unknown))},
            code="unsupported_pattern_token",
        )
    if "PREFIX" not in tokens:
        raise ValidationError(
            _("Pattern must include the {PREFIX} token."),
            code="pattern_missing_prefix",
        )
    if "SEQUENCE" not in tokens:
        raise ValidationError(
            _("Pattern must include the {SEQUENCE} token."),
            code="pattern_missing_sequence",
        )


def build_format_regex(scheme) -> re.Pattern:
    """
    Build a compiled regex that fully matches a reference for the scheme.

    Literal pattern text is escaped; tokens expand to the appropriate value
    classes.  Used to validate generated numbers before they are committed.
    """
    sequence_length = scheme.sequence_length

    def replace(match: re.Match) -> str:
        token = match.group(1)
        if token == "SEQUENCE":  # nosec B105
            return rf"\d{{{sequence_length}}}"
        return _TOKEN_REGEX.get(token, re.escape(token))

    regex_source = TOKEN_RE.sub(replace, scheme.pattern)
    return re.compile(f"^{regex_source}$")


def validate_reference_format(reference: str, scheme) -> None:
    """Raise unless the reference conforms to the scheme's pattern."""
    regex = build_format_regex(scheme)
    if not regex.match(reference):
        raise ValidationError(
            _("Reference %(reference)s does not match the scheme format.")
            % {"reference": reference},
            code="invalid_reference_format",
        )
