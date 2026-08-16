"""Finance Engine CSV renderer."""

from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, Union

from django.http import HttpResponse
from django.utils import timezone

from .base import BaseFinanceRenderer


class FinanceCSVRenderer(BaseFinanceRenderer):
    """Finance report CSV renderer."""

    def render(self) -> bytes:
        """
        Render the data as CSV.

        Returns:
            bytes: The rendered CSV data.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Add title and metadata
        writer.writerow([self.data.get('title', 'Financial Report')])
        writer.writerow([f"Generated on: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"])
        writer.writerow([])  # Empty row
        
        # Flatten and write data
        self._write_data_to_csv(writer, self.data)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content.encode('utf-8')

    def _write_data_to_csv(self, writer: csv.writer, data: Any, path: str = "") -> None:
        """
        Write data to CSV writer recursively.

        Args:
            writer: The CSV writer.
            data: The data to write.
            path: The current path in the data structure (for nested keys).
        """
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                if isinstance(value, dict) and value:
                    # Write section header
                    writer.writerow([new_path.replace('_', ' ').title() + ":"])
                    self._write_data_to_csv(writer, value, new_path)
                elif isinstance(value, list) and value:
                    # Write list header
                    writer.writerow([new_path.replace('_', ' ').title() + ":"])
                    self._write_data_to_csv(writer, value, new_path)
                else:
                    # Write key-value pair
                    writer.writerow([new_path.replace('_', ' ').title(), str(value)])
        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                # List of dictionaries - write as table with headers
                if data:
                    headers = list(data[0].keys())
                    writer.writerow([h.replace('_', ' ').title() for h in headers])
                    for item in data:
                        writer.writerow([str(item.get(h, '')) for h in headers])
            else:
                # Simple list
                for item in data:
                    writer.writerow([str(item)])
        else:
            # Simple value
            writer.writerow([str(data)])