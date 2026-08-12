"""PDF renderer for the Export Engine.

Built on ``reportlab`` platypus.  Produces professional, branded documents
with a logo header, a footer (organization, generated timestamp, page X of Y),
confidentiality watermarks, draft markings, wrapped tables and PDF metadata.
"""

from __future__ import annotations

import io
import os
from typing import Any

from django.conf import settings

from ..constants import ExportFormat, PageOrientation, PageSize
from .base import BaseRenderer, ExportDataset, RendererRegistry, RenderResult


@RendererRegistry.register(ExportFormat.PDF)
class PDFRenderer(BaseRenderer):
    """Render an ExportDataset to a branded PDF."""

    format = ExportFormat.PDF

    def _resolve_pagesize(self, page_size: str, orientation: str):
        from reportlab.lib.pagesizes import A4, LETTER, landscape, portrait

        base = A4 if page_size == PageSize.A4 else LETTER
        if orientation == PageOrientation.LANDSCAPE:
            return landscape(base)
        return portrait(base)

    def _resolve_logo(self) -> Any | None:
        from reportlab.lib.utils import ImageReader

        logo_static = getattr(settings, "STATICFILES_DIRS", None)
        candidates = []
        if logo_static:
            candidates.append(
                os.path.join(str(logo_static[0]), "images", "app_logo.png")
            )
        candidates.append(
            os.path.join(str(settings.BASE_DIR), "static", "images", "app_logo.png")
        )
        for candidate in candidates:
            if os.path.exists(candidate):
                return ImageReader(candidate)
        return None

    def render(
        self, dataset: ExportDataset, configuration: Any
    ) -> RenderResult:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.platypus import SimpleDocTemplate

        buffer = io.BytesIO()
        page_size = self._resolve_pagesize(dataset.page_size, dataset.orientation)
        left_right_margin = 14 * mm
        top_bottom_margin = 22 * mm

        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            leftMargin=left_right_margin,
            rightMargin=left_right_margin,
            topMargin=top_bottom_margin,
            bottomMargin=top_bottom_margin,
            title=dataset.title,
            author=configuration.short_name,
            subject=dataset.subtitle or dataset.title,
            creator=dataset.creator,
            keywords=", ".join(
                part
                for part in (
                    "SITADC",
                    dataset.reference,
                    dataset.status,
                    dataset.confidentiality,
                )
                if part
            ),
        )

        logo = self._resolve_logo() if dataset.logo_enabled else None
        confidentiality = dataset.watermark_text
        short_name = configuration.short_name
        show_pages = dataset.show_page_numbers

        def _draw_header_footer(canv, doc_obj):
            canv.saveState()
            page_w, page_h = page_size

            # ---- header ----
            if dataset.header_enabled:
                header_y = page_h - 16 * mm
                if logo is not None:
                    try:
                        iw, ih = logo.getSize()
                        aspect = ih / iw if iw else 1.0
                        width = 9 * mm
                        height = width * aspect
                        if height > 12 * mm:
                            height = 12 * mm
                            width = height / aspect
                        canv.drawImage(
                            logo,
                            14 * mm,
                            header_y - height,
                            width=width,
                            height=height,
                            preserveAspectRatio=True,
                            mask="auto",
                        )
                        text_x = 14 * mm + width + 4 * mm
                    except Exception:
                        text_x = 14 * mm
                else:
                    text_x = 14 * mm

                canv.setFont("Helvetica-Bold", 10)
                canv.setFillColor(colors.HexColor("#003366"))
                canv.drawString(text_x, header_y, dataset.title[:120])
                canv.setFont("Helvetica", 8)
                canv.setFillColor(colors.HexColor("#444444"))
                canv.drawString(
                    text_x,
                    header_y - 10,
                    f"{short_name} — Reference: {dataset.reference or '—'}",
                )
                if dataset.report_period:
                    canv.drawString(
                        text_x,
                        header_y - 18,
                        f"Reporting Period: {dataset.report_period}",
                    )
                canv.setStrokeColor(colors.HexColor("#003366"))
                canv.setLineWidth(0.8)
                canv.line(
                    14 * mm, header_y - 21 * mm, page_w - 14 * mm, header_y - 21 * mm
                )

            # ---- footer ----
            if dataset.footer_enabled:
                footer_y = 12 * mm
                canv.setFont("Helvetica", 8)
                canv.setFillColor(colors.HexColor("#555555"))
                canv.drawCentredString(
                    page_w / 2,
                    footer_y + 6 * mm,
                    f"Generated through SITADC Youth Hub — "
                    f"{dataset.generated_at:%Y-%m-%d %H:%M}",
                )
                canv.setStrokeColor(colors.HexColor("#CCCCCC"))
                canv.setLineWidth(0.5)
                canv.line(
                    14 * mm, footer_y + 11 * mm, page_w - 14 * mm, footer_y + 11 * mm
                )

            # ---- watermark ----
            if confidentiality:
                canv.saveState()
                canv.translate(page_w / 2, page_h / 2)
                canv.rotate(45)
                canv.setFont("Helvetica-Bold", 42)
                canv.setFillColor(colors.Color(0.85, 0.2, 0.2, alpha=0.12))
                canv.drawCentredString(0, 0, confidentiality)
                canv.restoreState()

            canv.restoreState()

        class _NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                num_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    if dataset.footer_enabled:
                        self.setFont("Helvetica", 8)
                        self.setFillColor(colors.HexColor("#555555"))
                        self.drawString(
                            14 * mm, 12 * mm, f"Page {self._pageNumber} of {num_pages}"
                        )
                        if confidentiality and dataset.confidentiality_notice:
                            self.setFont("Helvetica-Bold", 8)
                            self.setFillColor(colors.HexColor("#8B0000"))
                            page_w2, _ph = page_size
                            self.drawCentredString(
                                page_w2 / 2, 10 * mm, confidentiality
                            )
                    super().showPage()
                super().save()

        canvas_factory = _NumberedCanvas if show_pages else canvas.Canvas

        doc.build(
            self._build_elements(dataset, configuration),
            onFirstPage=_draw_header_footer,
            onLaterPages=_draw_header_footer,
            canvasmaker=canvas_factory,
        )

        buffer.seek(0)
        return RenderResult(
            content=buffer.getvalue(),
            mime_type=self.content_type,
            filename=self.default_extension,
        )

    # ------------------------------------------------------------------
    # Content layout
    # ------------------------------------------------------------------

    def _build_elements(self, dataset: ExportDataset, configuration: Any):
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import (
            KeepTogether,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ExportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#003366"),
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "ExportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#555555"),
            spaceAfter=2,
        )
        heading2_style = ParagraphStyle(
            "ExportHeading2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#003366"),
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "ExportBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
        )
        cell_style = ParagraphStyle(
            "ExportCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
        )
        header_cell_style = ParagraphStyle(
            "ExportHeaderCell",
            parent=cell_style,
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )

        elements: list = [Spacer(1, 11)]

        # Title + subtitle
        elements.append(Paragraph(dataset.title, title_style))
        if dataset.subtitle:
            elements.append(Paragraph(dataset.subtitle, subtitle_style))
        elements.append(Spacer(1, 8))

        # Meta block
        meta_rows = list(dataset.meta_rows)
        if dataset.reference:
            meta_rows.append(("Reference", dataset.reference))
        if dataset.report_period:
            meta_rows.append(("Reporting Period", dataset.report_period))
        if dataset.status:
            meta_rows.append(("Status", dataset.status))
        if dataset.version:
            meta_rows.append(("Version", dataset.version))
        meta_rows.append(("Generated By", dataset.generated_by))
        meta_rows.append(("Generated At", f"{dataset.generated_at:%Y-%m-%d %H:%M}"))
        meta_rows.append(("Confidentiality", str(dataset.confidentiality)))
        if dataset.filters:
            filter_summary = "; ".join(
                f"{key}: {value}" for key, value in dataset.filters.items() if value
            )
            if filter_summary:
                meta_rows.append(("Filters", filter_summary))

        if meta_rows:
            meta_table = Table(
                [
                    [Paragraph(label, cell_style), Paragraph(value, cell_style)]
                    for label, value in meta_rows
                ],
                colWidths=[180, 560],
            )
            meta_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2F7")),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            elements.append(meta_table)
            elements.append(Spacer(1, 10))

        # Draft marking banner
        if dataset.draft:
            draft_style = ParagraphStyle(
                "ExportDraft",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=10,
                textColor=colors.white,
                alignment=1,
                backColor=colors.HexColor("#B22222"),
                borderPadding=4,
            )
            elements.append(
                KeepTogether(
                    [
                        Paragraph(
                            "DRAFT — UNCONTROLLED COPY, NOT FOR DISTRIBUTION",
                            draft_style,
                        )
                    ]
                )
            )
            elements.append(Spacer(1, 8))

        # Narrative sections (document exports)
        for heading, blocks in dataset.sections:
            elements.append(Paragraph(heading, heading2_style))
            for block in blocks:
                if isinstance(block, list):
                    elements.append(
                        self._render_table(block, header_cell_style, cell_style)
                    )
                else:
                    elements.append(Paragraph(str(block), body_style))
            elements.append(Spacer(1, 6))

        # Tabular data
        if dataset.columns and dataset.rows:
            elements.append(Paragraph("Data", heading2_style))
            elements.append(
                self._render_table(
                    [dataset.column_labels, *dataset.rows],
                    header_cell_style,
                    cell_style,
                )
            )

        # No records notice
        if not dataset.columns and not dataset.rows and not dataset.sections:
            elements.append(
                Paragraph(
                    "No records matched the requested export criteria.",
                    body_style,
                )
            )

        # Approval / signature block
        if dataset.approval:
            elements.append(Paragraph("Approval and Sign-off", heading2_style))
            approval_rows = [
                [label, dataset.approval.get(label, "—")]
                for label in ("Prepared By", "Reviewed By", "Approved By")
            ]
            approval_table = Table(
                [
                    [Paragraph(label, cell_style), Paragraph(value, cell_style)]
                    for label, value in approval_rows
                ],
                colWidths=[200, 540],
            )
            approval_table.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            elements.append(approval_table)

        return elements

    def _render_table(self, rows: list[list], header_cell_style, cell_style):
        """Build a wrapped, repeated-header table from header+row data.

        ``rows[0]`` is the header row; remaining rows are body cells.
        """
        from reportlab import platypus
        from reportlab.lib import colors
        from reportlab.platypus import Paragraph

        def _as_para(value, style):
            text = str(value if value is not None else "")
            text = text.replace("\n", "<br/>")
            return Paragraph(text, style)

        if not rows:
            return Paragraph("", cell_style)
        headers, body = rows[0], rows[1:]
        data = [[_as_para(cell, header_cell_style) for cell in headers]]
        for row in body:
            data.append([_as_para(cell, cell_style) for cell in row])

        col_count = max(len(headers), 1)
        width_pts = 595.0 - 56.0
        widths = [width_pts / col_count for _ in range(col_count)]
        table = platypus.Table(data, colWidths=widths, repeatRows=1)
        table.setStyle(
            platypus.TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CCCCCC")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#EEF2F7")],
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        return table
