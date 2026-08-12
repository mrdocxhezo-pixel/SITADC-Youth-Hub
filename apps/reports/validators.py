"""Validation helpers for the Dynamic Report Builder module.

Structural schema validation lives here so both the designer services and the
import engine share a single definition of what a valid template schema looks
like.
"""

from __future__ import annotations

import re
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .constants import (
    ConditionOperator,
    FieldDataType,
    FieldType,
    SectionVisibilityMode,
    ValidationRuleType,
)

FIELD_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{1,62}[a-z0-9]$")


def validate_field_code(value: str) -> None:
    """Validate an internal field/section/group code (snake_case identifier)."""
    if not FIELD_CODE_RE.fullmatch(value):
        raise ValidationError(
            _(
                "Code must start with a letter and contain only lowercase "
                "letters, digits and underscores (2-64 characters)."
            ),
            code="invalid_field_code",
        )


def validate_value_type(value: Any, data_type: str) -> None:
    """Validate that a submitted value is compatible with a field data type."""
    if value is None:
        return
    if data_type == FieldDataType.INTEGER:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError(
                _("Expected an integer value."), code="invalid_integer"
            )
    elif data_type == FieldDataType.DECIMAL:
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValidationError(
                _("Expected a numeric value."), code="invalid_decimal"
            )
    elif data_type == FieldDataType.BOOLEAN:
        if not isinstance(value, bool):
            raise ValidationError(
                _("Expected a boolean value."), code="invalid_boolean"
            )
    elif data_type == FieldDataType.STRING and not isinstance(value, str):
        raise ValidationError(_("Expected a text value."), code="invalid_string")


def validate_condition_structure(condition: Any) -> None:
    """Validate a section visibility condition structure.

    A condition is a JSON object of the form ``{"all": [...]}`` or
    ``{"any": [...]}`` where each leaf is ``{"field": ..., "operator": ...,
    "value": ...}``.
    """
    if not isinstance(condition, dict):
        raise ValidationError(
            _("A condition must be a JSON object."), code="condition_type"
        )
    clauses = [key for key in ("all", "any") if key in condition]
    if not clauses or len(clauses) > 1:
        raise ValidationError(
            _("A condition must contain exactly one of 'all' or 'any'."),
            code="condition_clause",
        )
    for leaf in condition.get(clauses[0], []):
        _validate_condition_leaf(leaf)


def _validate_condition_leaf(leaf: Any) -> None:
    if isinstance(leaf, dict) and ("all" in leaf or "any" in leaf):
        validate_condition_structure(leaf)
        return
    if not isinstance(leaf, dict):
        raise ValidationError(
            _("Condition clauses must be objects."), code="condition_leaf"
        )
    if not leaf.get("field"):
        raise ValidationError(
            _("Condition leaves require a field code."), code="condition_field"
        )
    operator = leaf.get("operator")
    if operator not in ConditionOperator.values:
        raise ValidationError(
            _("Unknown condition operator."), code="condition_operator"
        )


def validate_rule_params(rule_type: str, params: Any) -> None:
    """Validate the parameter payload for a validation rule type."""
    if not isinstance(params, dict):
        raise ValidationError(
            _("Rule parameters must be a JSON object."), code="rule_params"
        )
    if rule_type in (ValidationRuleType.MIN_LENGTH, ValidationRuleType.MAX_LENGTH):
        if not isinstance(params.get("value"), int) or params["value"] < 0:
            raise ValidationError(
                _("Length rules require a non-negative integer value."),
                code="rule_length",
            )
    elif rule_type in (ValidationRuleType.MIN_VALUE, ValidationRuleType.MAX_VALUE):
        value = params.get("value")
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValidationError(
                _("Range rules require a numeric value."), code="rule_range"
            )
    elif rule_type == ValidationRuleType.REGEX:
        try:
            re.compile(params.get("pattern", ""))
        except re.error as exc:
            raise ValidationError(
                _("Invalid regular expression: %(detail)s") % {"detail": exc},
                code="rule_regex",
            ) from exc
    elif rule_type == ValidationRuleType.FILE_SIZE_MAX:
        if not isinstance(params.get("max_bytes"), int) or params["max_bytes"] <= 0:
            raise ValidationError(
                _("File size rules require a positive max_bytes value."),
                code="rule_file_size",
            )
    elif rule_type == ValidationRuleType.CROSS_FIELD and not params.get("other_field"):
        raise ValidationError(
            _("Cross-field rules require an other_field code."),
            code="rule_cross_field",
        )


def validate_schema_structure(schema: Any) -> None:
    """Validate the top-level structure of a template schema snapshot."""
    if not isinstance(schema, dict):
        raise ValidationError(_("A schema must be a JSON object."), code="schema_type")
    sections = schema.get("sections", [])
    if not isinstance(sections, list):
        raise ValidationError(
            _("Schema sections must be a list."), code="schema_sections"
        )
    seen_codes: set[str] = set()
    for section in sections:
        _validate_schema_section(section, seen_codes)


def _validate_schema_section(section: Any, seen_codes: set[str]) -> None:
    if not isinstance(section, dict):
        raise ValidationError(_("Each section must be an object."), code="section_type")
    code = section.get("code")
    if not code:
        raise ValidationError(_("Each section requires a code."), code="section_code")
    if code in seen_codes:
        raise ValidationError(
            _("Duplicate section code '%(code)s'.") % {"code": code},
            code="section_duplicate",
        )
    seen_codes.add(code)
    visibility = section.get("visibility_mode", SectionVisibilityMode.ALWAYS)
    if visibility not in SectionVisibilityMode.values:
        raise ValidationError(
            _("Unknown section visibility mode."), code="section_visibility"
        )
    if visibility == SectionVisibilityMode.CONDITIONAL:
        validate_condition_structure(section.get("condition", {}))
    for group in section.get("groups", []):
        _validate_schema_group(group, seen_codes)


def _validate_schema_group(group: Any, seen_codes: set[str]) -> None:
    if not isinstance(group, dict):
        raise ValidationError(
            _("Each field group must be an object."), code="group_type"
        )
    code = group.get("code")
    if not code:
        raise ValidationError(_("Each field group requires a code."), code="group_code")
    if code in seen_codes:
        raise ValidationError(
            _("Duplicate field group code '%(code)s'.") % {"code": code},
            code="group_duplicate",
        )
    seen_codes.add(code)
    for field in group.get("fields", []):
        _validate_schema_field(field, seen_codes)


def _validate_schema_field(field: Any, seen_codes: set[str]) -> None:
    if not isinstance(field, dict):
        raise ValidationError(
            _("Each dynamic field must be an object."), code="field_type"
        )
    code = field.get("code")
    if not code:
        raise ValidationError(
            _("Each dynamic field requires a code."), code="field_code"
        )
    if code in seen_codes:
        raise ValidationError(
            _("Duplicate field code '%(code)s'.") % {"code": code},
            code="field_duplicate",
        )
    seen_codes.add(code)
    field_type = field.get("field_type")
    if field_type not in FieldType.values:
        raise ValidationError(
            _("Unknown field type '%(value)s'.") % {"value": field_type},
            code="field_type_value",
        )
    data_type = field.get("data_type")
    if data_type not in FieldDataType.values:
        raise ValidationError(_("Unknown field data type."), code="field_data_type")
    for option in field.get("options", []):
        if not isinstance(option, dict) or not option.get("value"):
            raise ValidationError(
                _("Field options require a value."), code="field_option"
            )
