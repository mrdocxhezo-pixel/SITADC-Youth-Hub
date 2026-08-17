"""Finance Engine HTML print renderer."""

from __future__ import annotations

from django.http import HttpResponse
from django.template.loader import render_to_string

from .base import BaseFinanceRenderer


class FinancePrintHTMLRenderer(BaseFinanceRenderer):
    """Finance report HTML print renderer."""

    def render(self) -> bytes:
        """
        Render the data as HTML for printing.

        Returns:
            bytes: The rendered HTML data.
        """
        # Render HTML template
        html_string = render_to_string(
            "finance/report_print.html", self._get_template_context()
        )

        return html_string.encode("utf-8")

    def get_http_response(self, filename: str) -> HttpResponse:
        """
        Get an HTTP response for the rendered data.

        Args:
            filename: The filename for the download.

        Returns:
            HttpResponse: The HTTP response with the rendered data.
        """
        rendered_data = self.render()

        response = HttpResponse(rendered_data, content_type="text/html")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
