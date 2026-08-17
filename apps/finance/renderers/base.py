"""Finance Engine base renderer."""

from __future__ import annotations

import abc
from typing import Any

from django.http import HttpResponse
from django.utils import timezone


class BaseFinanceRenderer(abc.ABC):
    """Base class for finance report renderers."""

    def __init__(self, data: dict[str, Any], options: dict[str, Any] | None = None):
        """
        Initialize the renderer.

        Args:
            data: The data to render.
            options: Rendering options (optional).
        """
        self.data = data
        self.options = options or {}
        self.timestamp = timezone.now()

    @abc.abstractmethod
    def render(self) -> bytes:
        """
        Render the data to the specific format.

        Returns:
            bytes: The rendered data.
        """

    def get_http_response(self, filename: str) -> HttpResponse:
        """
        Get an HTTP response for the rendered data.

        Args:
            filename: The filename for the download.

        Returns:
            HttpResponse: The HTTP response with the rendered data.
        """
        rendered_data = self.render()

        # Determine content type based on file extension
        content_type = self._get_content_type(filename)

        response = HttpResponse(rendered_data, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def _get_content_type(self, filename: str) -> str:
        """
        Get content type based on file extension.

        Args:
            filename: The filename.

        Returns:
            str: The content type.
        """
        extension = filename.lower().split(".")[-1] if "." in filename else ""

        content_types = {
            "pdf": "application/pdf",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xls": "application/vnd.ms-excel",
            "csv": "text/csv",
            "docx": (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            "doc": "application/msword",
            "html": "text/html",
            "txt": "text/plain",
        }

        return content_types.get(extension, "application/octet-stream")

    def _get_template_context(self) -> dict[str, Any]:
        """
        Get template context for HTML-based renderers.

        Returns:
            Dict: The template context.
        """
        return {
            "data": self.data,
            "timestamp": self.timestamp,
            "options": self.options,
        }
