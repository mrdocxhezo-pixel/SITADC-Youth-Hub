"""CSV renderer for the Export Engine.

Writes UTF-8 with a BOM so Excel opens the file correctly, and applies
formula-injection hardening to every cell.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from ..constants import ExportFormat
from ..utils import neutralize_spreadsheet_value
from .base import BaseRenderer, ExportDataset, RendererRegistry, RenderResult


@RendererRegistry.register(ExportFormat.CSV)
class CSVRenderer(BaseRenderer):
    """Render an ExportDataset to a UTF-8 CSV stream."""

    format = ExportFormat.CSV

    def render(
        self, dataset: ExportDataset, configuration: Any
    ) -> RenderResult:
        buffer = io.StringIO()
        writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)

        writer.writerow(dataset.column_labels)
        for row in dataset.rows:
            writer.writerow(
                [neutralize_spreadsheet_value(value) for value in row]
            )

        content = "\ufeff" + buffer.getvalue()
        return RenderResult(
            content=content.encode("utf-8"),
            mime_type=self.content_type,
            filename=self.default_extension,
        )
