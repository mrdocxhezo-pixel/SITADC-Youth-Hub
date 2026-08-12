"""Renderer registry and the shared dataset contract.

Every output format is produced by a ``BaseRenderer`` subclass that consumes
a normalized ``ExportDataset`` and returns a ``RenderResult``.  Providers
build the dataset; renderers never talk to the database.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar

from ..constants import (
    FORMAT_EXTENSIONS,
    FORMAT_MIME_TYPES,
    ConfidentialityLevel,
    ExportFormat,
    PageOrientation,
)

logger = logging.getLogger(__name__)


@dataclass
class ExportColumn:
    """A single, authorization-screened column definition.

    ``accessor`` may be a callable (instance -> value) or an attribute path
    string resolved through ``getattr`` chains.  ``sensitive`` marks a column
    that must never be included unless the actor holds the module-level
    confidential-view permission.
    """

    key: str
    label: str
    sensitive: bool = False
    accessor: Any | None = None

    def value_for(self, instance: Any):
        if self.accessor is None:
            return None
        if callable(self.accessor):
            return self.accessor(instance)
        parts = self.accessor.split(".")
        value = instance
        for part in parts:
            value = getattr(value, part, None)
            if value is None:
                break
        return value


@dataclass
class ExportDataset:
    """Normalized dataset handed to a renderer.

    ``rows`` holds tabular data whose cell order matches ``columns``.  For
    narrative/document exports a provider may supply ``sections`` (headings
    with paragraphs and sub-tables) and ``meta_rows`` (key/value summary).
    """

    title: str = ""
    subtitle: str = ""
    reference: str = ""
    report_period: str = ""
    status: str = ""
    version: str = ""
    generated_by: str = ""
    generated_at: datetime | None = None
    confidentiality: str = ConfidentialityLevel.INTERNAL
    watermark: str = ""
    draft: bool = False
    creator: str = "SITADC Youth Hub"

    columns: list[ExportColumn] = field(default_factory=list)
    rows: list[list] = field(default_factory=list)
    sections: list[tuple[str, list[Any]]] = field(default_factory=list)
    meta_rows: list[tuple[str, str]] = field(default_factory=list)
    approval: dict[str, str] = field(default_factory=dict)
    filters: dict[str, str] = field(default_factory=dict)

    page_size: str = "A4"
    orientation: str = PageOrientation.PORTRAIT
    logo_enabled: bool = True
    header_enabled: bool = True
    footer_enabled: bool = True
    show_page_numbers: bool = True
    confidentiality_notice: bool = True

    @property
    def watermark_text(self) -> str:
        if self.watermark:
            return self.watermark
        if self.draft:
            return "DRAFT"
        if (
            self.confidentiality != ConfidentialityLevel.PUBLIC
            and self.confidentiality_notice
        ):
            return str(self.confidentiality)
        return ""

    @property
    def column_labels(self) -> list[str]:
        return [column.label for column in self.columns]


@dataclass
class RenderResult:
    """The bytes produced by a renderer plus delivery metadata."""

    content: bytes
    mime_type: str
    filename: str


class BaseRenderer:
    """Contract every output-format renderer must satisfy."""

    format: ClassVar[str] = ""
    extension: ClassVar[str] = ""

    @property
    def content_type(self) -> str:
        return FORMAT_MIME_TYPES.get(self.format, "application/octet-stream")

    @property
    def default_extension(self) -> str:
        return FORMAT_EXTENSIONS.get(self.format, "bin")

    def render(self, dataset: ExportDataset, configuration: Any) -> RenderResult:
        raise NotImplementedError("Renderers must implement render().")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class RendererRegistry:
    """Registry mapping format codes to renderer classes."""

    _renderers: ClassVar[dict[str, type[BaseRenderer]]] = {}

    @classmethod
    def register(cls, format_code: str) -> Any:
        def decorator(renderer_cls: type[BaseRenderer]) -> type[BaseRenderer]:
            cls._renderers[format_code] = renderer_cls
            return renderer_cls

        return decorator

    @classmethod
    def get(cls, format_code: str) -> type[BaseRenderer] | None:
        return cls._renderers.get(format_code)

    @classmethod
    def available_formats(cls) -> list[str]:
        return sorted(cls._renderers.keys())


def get_renderer(format_code: str) -> BaseRenderer:
    """Return a renderer instance for the given format."""
    if format_code == ExportFormat.PRINT_HTML:
        renderer_cls = RendererRegistry.get(ExportFormat.PRINT_HTML)
    else:
        renderer_cls = RendererRegistry.get(format_code)
    if renderer_cls is None:
        raise ValueError(f"Unsupported export format: {format_code}")
    return renderer_cls()
