"""Export services for report instances.

Supports PDF, DOCX, XLSX, CSV, and HTML export formats.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from django.http import HttpResponse
from django.utils import timezone


def _build_export_data(report: Any) -> dict[str, Any]:
    """Build a flat data structure for export."""
    sections = {}
    for sr in report.section_responses.select_related("section").all():
        sections[sr.section.name] = sr.data

    fields = {}
    for fr in report.field_responses.select_related("field").all():
        fields[fr.field.label] = fr.value

    evidence = []
    for e in report.evidence_items.all():
        evidence.append(
            {
                "type": e.get_evidence_type_display(),
                "filename": e.original_filename,
                "description": e.description,
                "verified": e.is_verified,
            }
        )

    attachments = []
    for a in report.attachments.all():
        attachments.append(
            {
                "filename": a.original_filename,
                "size": a.file_size,
                "description": a.description,
            }
        )

    return {
        "reference_number": report.reference_number,
        "title": report.title,
        "template": report.template.title if report.template else "",
        "category": report.category.name if report.category else "",
        "status": report.get_status_display(),
        "validation_status": report.get_validation_status_display(),
        "confidentiality": report.get_confidentiality_display(),
        "owner": str(report.owner) if report.owner else "",
        "department": report.department or "",
        "due_date": str(report.due_date) if report.due_date else "",
        "submitted_at": str(report.submitted_at) if report.submitted_at else "",
        "approved_at": str(report.approved_at) if report.approved_at else "",
        "version_number": report.version_number,
        "notes": report.notes or "",
        "sections": sections,
        "fields": fields,
        "evidence": evidence,
        "attachments": attachments,
        "created_at": str(report.created_at),
        "updated_at": str(report.updated_at),
    }


# ---------------------------------------------------------------------------
# HTML Export
# ---------------------------------------------------------------------------


def export_html(report: Any) -> HttpResponse:
    """Export report as HTML."""
    data = _build_export_data(report)

    html_parts = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'>",
        f"<title>{data['title']}</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 40px; }",
        "h1 { color: #1a5276; border-bottom: 2px solid #1a5276; "
        "padding-bottom: 10px; }",
        "h2 { color: #2c3e50; margin-top: 30px; }",
        "table { border-collapse: collapse; width: 100%; margin: 15px 0; }",
        "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
        "th { background-color: #f2f2f2; }",
        ".badge { padding: 3px 8px; border-radius: 4px; font-size: 12px; }",
        ".badge-success { background: #28a745; color: white; }",
        ".badge-warning { background: #ffc107; color: black; }",
        ".section { margin: 20px 0; padding: 15px; border: 1px solid #eee; "
        "border-radius: 5px; }",
        "</style></head><body>",
        f"<h1>{data['title']}</h1>",
        f"<p><strong>Reference:</strong> {data['reference_number']}</p>",
        f"<p><strong>Template:</strong> {data['template']}</p>",
        f"<p><strong>Category:</strong> {data['category']}</p>",
        f"<p><strong>Status:</strong> <span class='badge "
        f"badge-success'>{data['status']}</span></p>",
        f"<p><strong>Confidentiality:</strong> {data['confidentiality']}</p>",
        f"<p><strong>Owner:</strong> {data['owner']}</p>",
        f"<p><strong>Department:</strong> {data['department']}</p>",
        f"<p><strong>Due Date:</strong> {data['due_date']}</p>",
        f"<p><strong>Version:</strong> {data['version_number']}</p>",
    ]

    if data["sections"]:
        html_parts.append("<h2>Section Responses</h2>")
        for section_name, section_data in data["sections"].items():
            html_parts.append(f"<div class='section'><h3>{section_name}</h3>")
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    html_parts.append(f"<p><strong>{key}:</strong> {value}</p>")
            else:
                html_parts.append(f"<p>{section_data}</p>")
            html_parts.append("</div>")

    if data["fields"]:
        html_parts.append("<h2>Field Responses</h2>")
        html_parts.append("<table><tr><th>Field</th><th>Value</th></tr>")
        for field_name, field_value in data["fields"].items():
            html_parts.append(f"<tr><td>{field_name}</td><td>{field_value}</td></tr>")
        html_parts.append("</table>")

    if data["evidence"]:
        html_parts.append("<h2>Evidence</h2>")
        html_parts.append(
            "<table><tr><th>Type</th><th>File</th><th>Description</th><th>Verified</th></tr>"
        )
        for e in data["evidence"]:
            verified = "Yes" if e["verified"] else "No"
            html_parts.append(
                f"<tr><td>{e['type']}</td><td>{e['filename']}</td><td>{e['description']}</td><td>{verified}</td></tr>"
            )
        html_parts.append("</table>")

    if data["attachments"]:
        html_parts.append("<h2>Attachments</h2>")
        html_parts.append(
            "<table><tr><th>File</th><th>Size</th><th>Description</th></tr>"
        )
        for a in data["attachments"]:
            html_parts.append(
                f"<tr><td>{a['filename']}</td><td>{a['size']}</td><td>{a['description']}</td></tr>"
            )
        html_parts.append("</table>")

    if data["notes"]:
        html_parts.append(f"<h2>Notes</h2><p>{data['notes']}</p>")

    html_parts.append(
        f"<hr><p><small>Generated on "
        f"{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>"
    )
    html_parts.append("</body></html>")

    html_content = "\n".join(html_parts)

    response = HttpResponse(html_content, content_type="text/html")
    response["Content-Disposition"] = (
        f'attachment; filename="{report.reference_number}.html"'
    )
    return response


# ---------------------------------------------------------------------------
# CSV Export
# ---------------------------------------------------------------------------


def export_csv(report: Any) -> HttpResponse:
    """Export report as CSV."""
    data = _build_export_data(report)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header info
    writer.writerow(["Report Information", ""])
    writer.writerow(["Reference Number", data["reference_number"]])
    writer.writerow(["Title", data["title"]])
    writer.writerow(["Template", data["template"]])
    writer.writerow(["Category", data["category"]])
    writer.writerow(["Status", data["status"]])
    writer.writerow(["Confidentiality", data["confidentiality"]])
    writer.writerow(["Owner", data["owner"]])
    writer.writerow(["Department", data["department"]])
    writer.writerow(["Due Date", data["due_date"]])
    writer.writerow(["Version", data["version_number"]])
    writer.writerow([])

    # Sections
    if data["sections"]:
        writer.writerow(["Section Responses", ""])
        for section_name, section_data in data["sections"].items():
            writer.writerow([section_name, ""])
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    writer.writerow(["", key, value])
        writer.writerow([])

    # Fields
    if data["fields"]:
        writer.writerow(["Field Responses", ""])
        writer.writerow(["Field", "Value"])
        for field_name, field_value in data["fields"].items():
            writer.writerow([field_name, field_value])
        writer.writerow([])

    # Evidence
    if data["evidence"]:
        writer.writerow(["Evidence", ""])
        writer.writerow(["Type", "File", "Description", "Verified"])
        for e in data["evidence"]:
            writer.writerow([e["type"], e["filename"], e["description"], e["verified"]])

    csv_content = output.getvalue()

    response = HttpResponse(csv_content, content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="{report.reference_number}.csv"'
    )
    return response


# ---------------------------------------------------------------------------
# JSON Export
# ---------------------------------------------------------------------------


def export_json(report: Any) -> HttpResponse:
    """Export report as JSON."""
    data = _build_export_data(report)

    json_content = json.dumps(data, indent=2, default=str)

    response = HttpResponse(json_content, content_type="application/json")
    response["Content-Disposition"] = (
        f'attachment; filename="{report.reference_number}.json"'
    )
    return response


# ---------------------------------------------------------------------------
# Excel Export (XLSX using openpyxl if available, else CSV fallback)
# ---------------------------------------------------------------------------


def export_xlsx(report: Any) -> HttpResponse:
    """Export report as XLSX. Falls back to CSV if openpyxl is not installed."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Report"

        data = _build_export_data(report)

        # Styles
        header_font = Font(bold=True, size=12)
        header_fill = PatternFill(
            start_color="1A5276", end_color="1A5276", fill_type="solid"
        )
        header_font_white = Font(bold=True, size=12, color="FFFFFF")

        # Title
        ws.merge_cells("A1:D1")
        ws["A1"] = data["title"]
        ws["A1"].font = Font(bold=True, size=16)

        row = 3
        info_fields = [
            ("Reference Number", data["reference_number"]),
            ("Template", data["template"]),
            ("Category", data["category"]),
            ("Status", data["status"]),
            ("Confidentiality", data["confidentiality"]),
            ("Owner", data["owner"]),
            ("Department", data["department"]),
            ("Due Date", data["due_date"]),
            ("Version", data["version_number"]),
        ]

        for label, value in info_fields:
            ws.cell(row=row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row, column=2, value=value)
            row += 1

        row += 1

        # Sections
        if data["sections"]:
            ws.cell(row=row, column=1, value="Section Responses").font = header_font
            row += 1
            for section_name, section_data in data["sections"].items():
                ws.cell(row=row, column=1, value=section_name).font = Font(bold=True)
                row += 1
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        ws.cell(row=row, column=2, value=key)
                        ws.cell(row=row, column=3, value=str(value))
                        row += 1
            row += 1

        # Fields
        if data["fields"]:
            ws.cell(row=row, column=1, value="Field Responses").font = header_font
            row += 1
            ws.cell(row=row, column=1, value="Field").font = header_font_white
            ws.cell(row=row, column=1).fill = header_fill
            ws.cell(row=row, column=2, value="Value").font = header_font_white
            ws.cell(row=row, column=2).fill = header_fill
            row += 1
            for field_name, field_value in data["fields"].items():
                ws.cell(row=row, column=1, value=field_name)
                ws.cell(row=row, column=2, value=str(field_value))
                row += 1

        # Adjust column widths
        for col in ws.columns:
            max_length = 0
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 50)

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{report.reference_number}.xlsx"'
        )

        wb.save(response)
        return response

    except ImportError:
        # Fallback to CSV
        return export_csv(report)


# ---------------------------------------------------------------------------
# PDF Export (using reportlab if available, else HTML fallback)
# ---------------------------------------------------------------------------


def export_pdf(report: Any) -> HttpResponse:
    """Export report as PDF. Falls back to HTML if reportlab is not installed."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        data = _build_export_data(report)

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            spaceAfter=20,
        )
        elements.append(Paragraph(data["title"], title_style))
        elements.append(Spacer(1, 12))

        # Info table
        info_data = [
            ["Reference", data["reference_number"]],
            ["Template", data["template"]],
            ["Category", data["category"]],
            ["Status", data["status"]],
            ["Confidentiality", data["confidentiality"]],
            ["Owner", data["owner"]],
            ["Department", data["department"]],
            ["Due Date", data["due_date"]],
            ["Version", str(data["version_number"])],
        ]

        info_table = Table(info_data, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.grey),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(info_table)
        elements.append(Spacer(1, 20))

        # Sections
        if data["sections"]:
            elements.append(Paragraph("Section Responses", styles["Heading2"]))
            for section_name, section_data in data["sections"].items():
                elements.append(Paragraph(f"<b>{section_name}</b>", styles["Normal"]))
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        elements.append(
                            Paragraph(f"  {key}: {value}", styles["Normal"])
                        )
                elements.append(Spacer(1, 8))

        # Fields
        if data["fields"]:
            elements.append(Paragraph("Field Responses", styles["Heading2"]))
            field_data = [["Field", "Value"]]
            for field_name, field_value in data["fields"].items():
                field_data.append([field_name, str(field_value)])

            field_table = Table(field_data, colWidths=[3 * inch, 3 * inch])
            field_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            elements.append(field_table)

        # Footer
        elements.append(Spacer(1, 30))
        elements.append(
            Paragraph(
                f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"],
            )
        )

        doc.build(elements)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="{report.reference_number}.pdf"'
        )
        return response

    except ImportError:
        # Fallback to HTML
        return export_html(report)
