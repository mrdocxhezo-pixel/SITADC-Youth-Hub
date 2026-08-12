"""Shared utilities for the Export Engine.

Formula-injection hardening is applied to every cell in tabular renderers so
that values entered by users can never be executed by the target spreadsheet
or word processor.
"""

from __future__ import annotations

from typing import Any

from .constants import FORMULA_INJECTION_PREFIXES


def neutralize_spreadsheet_value(value: Any) -> Any:
    """Neutralize cells that could be interpreted as a spreadsheet formula.

    Excel and LibreOffice evaluate cells beginning with ``=``, ``+``, ``-``,
    ``@``, tabs or carriage returns.  Such values are prefixed with a single
    quote so they are rendered as literal text.
    """
    if not isinstance(value, str) or not value:
        return value
    if value[0] in FORMULA_INJECTION_PREFIXES:
        return "'" + value
    return value


def cell_to_text(value: Any) -> str:
    """Render a cell value to plain text for text/html renderers."""
    if value is None:
        return ""
    return str(value)


def sanitize_sheet_name(name: str, default: str = "Sheet") -> str:
    """Trim invalid characters from an Excel worksheet name."""
    name = (name or default).strip()
    for char in ("[", "]", ":", "*", "?", "/", "\\"):
        name = name.replace(char, "_")
    name = name[:31] or default
    return name
