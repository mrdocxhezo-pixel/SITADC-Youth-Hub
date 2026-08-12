"""Renderer package for the Export Engine.

Importing this package registers every renderer with the
:class:`~apps.exports.renderers.base.RendererRegistry`.  The ``apps.py``
``ready()`` hook imports this package so the registry is populated whenever
Django loads.
"""

# Import renderers so they self-register with the registry.
from apps.exports.renderers import csv, docx, pdf, print_html, xlsx  # noqa: F401
from apps.exports.renderers.base import (
    BaseRenderer,
    ExportColumn,
    ExportDataset,
    RendererRegistry,
    RenderResult,
    get_renderer,
)

__all__ = [
    "BaseRenderer",
    "ExportColumn",
    "ExportDataset",
    "RenderResult",
    "RendererRegistry",
    "get_renderer",
]
