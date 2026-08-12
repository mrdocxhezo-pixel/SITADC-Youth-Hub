"""Domain exceptions for the Dynamic Report Builder module."""

from __future__ import annotations


class DynamicTemplateError(Exception):
    """Base class for all Dynamic Report Builder domain errors."""


class InvalidTemplateSchemaError(DynamicTemplateError):
    """The template schema is structurally invalid or semantically inconsistent."""


class CircularConditionalDependencyError(DynamicTemplateError):
    """Conditional logic rules form a circular dependency."""


class CircularFormulaDependencyError(DynamicTemplateError):
    """Calculated fields reference each other in a cycle."""


class InvalidFormulaError(DynamicTemplateError):
    """A formula expression is syntactically invalid or uses a forbidden element."""


class TemplateStatusTransitionError(DynamicTemplateError):
    """A requested status transition is not allowed for the template lifecycle."""


class TemplatePublishError(DynamicTemplateError):
    """A template could not be published because validation failed."""


class TemplateVersionError(DynamicTemplateError):
    """A version operation is not permitted (e.g. editing a published version)."""


class TemplateImportError(DynamicTemplateError):
    """A template could not be imported from the supplied payload."""


class UnsupportedFieldOperationError(DynamicTemplateError):
    """An operation was attempted on an unsupported field type."""
