"""Image renderers for the Export Engine (PNG/JPEG).

Renders the ExportDataset to a branded PNG or JPEG image using a headless
browser approach via ``playwright`` or a fallback to HTML-to-image conversion.
"""

from __future__ import annotations

import io
import logging
import tempfile
from typing import Any

from django.template.loader import render_to_string

from ..constants import ExportFormat
from .base import BaseRenderer, ExportDataset, RendererRegistry, RenderResult

logger = logging.getLogger(__name__)


def _render_html_to_image(html: str, format: str) -> bytes:
    """Render HTML to PNG/JPEG using playwright (preferred) or fallback."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1200, "height": 1600})
            page.set_content(html, wait_until="networkidle")
            if format == "PNG":
                image_bytes = page.screenshot(full_page=True, type="png")
            else:
                image_bytes = page.screenshot(full_page=True, type="jpeg", quality=90)
            browser.close()
            return image_bytes
    except ImportError:
        logger.warning("Playwright not available; falling back to imgkit")
        return _render_with_imgkit(html, format)
    except Exception as exc:
        logger.warning("Playwright rendering failed: %s; falling back to imgkit", exc)
        return _render_with_imgkit(html, format)


def _render_with_imgkit(html: str, format: str) -> bytes:
    """Fallback: render HTML to image using imgkit (wkhtmltoimage)."""
    try:
        import imgkit

        options = {
            "format": format.lower(),
            "width": 1200,
            "height": 1600,
            "disable-smart-width": "",
            "encoding": "UTF-8",
        }
        suffix = f".{format.lower()}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
        try:
            imgkit.from_string(html, tmp_path, options=options)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            import os

            os.unlink(tmp_path)
    except Exception as exc:
        logger.error("imgkit rendering failed: %s", exc)
        return _render_placeholder_image(format)


def _render_placeholder_image(format: str) -> bytes:
    """Last-resort placeholder image."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = 1200, 1600
    img = Image.new("RGB", (width, height), color=(245, 248, 252))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text(
        (600, 700),
        "SITADC Youth Hub",
        fill=(0, 51, 102),
        font=font,
        anchor="mm",
    )
    draw.text(
        (600, 750),
        f"Export Preview ({format})",
        fill=(85, 85, 85),
        font=font_small,
        anchor="mm",
    )
    draw.text(
        (600, 800),
        "Image renderer not fully configured",
        fill=(178, 34, 34),
        font=font_small,
        anchor="mm",
    )

    buffer = io.BytesIO()
    if format == "PNG":
        img.save(buffer, format="PNG")
    else:
        img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    return buffer.getvalue()


@RendererRegistry.register(ExportFormat.PNG)
class PNGRenderer(BaseRenderer):
    """Render an ExportDataset to a PNG image."""

    format = ExportFormat.PNG

    def render(self, dataset: ExportDataset, configuration: Any) -> RenderResult:
        html = self._build_html(dataset, configuration)
        content = _render_html_to_image(html, "PNG")
        return RenderResult(
            content=content,
            mime_type=self.content_type,
            filename=self.default_extension,
        )

    def _build_html(self, dataset: ExportDataset, configuration: Any) -> str:
        context = {
            "dataset": dataset,
            "organization_name": configuration.organization_name,
            "short_name": configuration.short_name,
            "headers": dataset.column_labels,
            "rows": dataset.rows,
            "meta_rows": list(dataset.meta_rows),
            "sections": dataset.sections,
            "watermark": dataset.watermark_text,
        }
        return render_to_string("exports/partials/print_export.html", context)


@RendererRegistry.register(ExportFormat.JPEG)
class JPEGRenderer(BaseRenderer):
    """Render an ExportDataset to a JPEG image."""

    format = ExportFormat.JPEG

    def render(self, dataset: ExportDataset, configuration: Any) -> RenderResult:
        html = self._build_html(dataset, configuration)
        content = _render_html_to_image(html, "JPEG")
        return RenderResult(
            content=content,
            mime_type=self.content_type,
            filename=self.default_extension,
        )

    def _build_html(self, dataset: ExportDataset, configuration: Any) -> str:
        context = {
            "dataset": dataset,
            "organization_name": configuration.organization_name,
            "short_name": configuration.short_name,
            "headers": dataset.column_labels,
            "rows": dataset.rows,
            "meta_rows": list(dataset.meta_rows),
            "sections": dataset.sections,
            "watermark": dataset.watermark_text,
        }
        return render_to_string("exports/partials/print_export.html", context)
