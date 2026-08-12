"""Permission constants and helpers for the Export Engine.

The ``exports.*`` catalogue supplements (never replaces) source-module
permissions.  Every export must satisfy the export permission AND the source
module permission AND object/scope checks before data is included.
"""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

EXPORTS_VIEW = "exports.view"
EXPORTS_CREATE = "exports.create"
EXPORTS_DOWNLOAD = "exports.download"
EXPORTS_PRINT = "exports.print"
EXPORTS_EXPORT_PDF = "exports.export_pdf"
EXPORTS_EXPORT_DOCX = "exports.export_docx"
EXPORTS_EXPORT_XLSX = "exports.export_xlsx"
EXPORTS_EXPORT_CSV = "exports.export_csv"
EXPORTS_EXPORT_REPORTS = "exports.export_reports"
EXPORTS_EXPORT_DOCUMENTS = "exports.export_documents"
EXPORTS_EXPORT_REGISTERS = "exports.export_registers"
EXPORTS_EXPORT_DIRECTORIES = "exports.export_directories"
EXPORTS_EXPORT_PROGRAMS = "exports.export_programs"
EXPORTS_EXPORT_PROJECTS = "exports.export_projects"
EXPORTS_EXPORT_MEAL = "exports.export_meal"
EXPORTS_EXPORT_MEETINGS = "exports.export_meetings"
EXPORTS_EXPORT_BENEFICIARIES = "exports.export_beneficiaries"
EXPORTS_EXPORT_SENSITIVE = "exports.export_sensitive"
EXPORTS_EXPORT_BULK = "exports.export_bulk"
EXPORTS_VIEW_HISTORY = "exports.view_history"
EXPORTS_VIEW_ALL_HISTORY = "exports.view_all_history"
EXPORTS_CANCEL = "exports.cancel"
EXPORTS_REGENERATE = "exports.regenerate"
EXPORTS_MANAGE_TEMPLATES = "exports.manage_templates"
EXPORTS_MANAGE_SETTINGS = "exports.manage_settings"
EXPORTS_MANAGE = "exports.manage"

# Format-level export permissions.
FORMAT_PERMISSIONS = {
    "PDF": EXPORTS_EXPORT_PDF,
    "DOCX": EXPORTS_EXPORT_DOCX,
    "XLSX": EXPORTS_EXPORT_XLSX,
    "CSV": EXPORTS_EXPORT_CSV,
    "PRINT_HTML": EXPORTS_PRINT,
}

# Source-type-level export permissions.
SOURCE_PERMISSIONS = {
    "REPORT": EXPORTS_EXPORT_REPORTS,
    "REGISTER": EXPORTS_EXPORT_REGISTERS,
    "DIRECTORY": EXPORTS_EXPORT_DIRECTORIES,
    "BENEFICIARY": EXPORTS_EXPORT_BENEFICIARIES,
    "PROGRAM": EXPORTS_EXPORT_PROGRAMS,
    "PROJECT": EXPORTS_EXPORT_PROJECTS,
    "MEAL": EXPORTS_EXPORT_MEAL,
    "MEETING": EXPORTS_EXPORT_MEETINGS,
    "DOCUMENT": EXPORTS_EXPORT_DOCUMENTS,
    "SEARCH": EXPORTS_EXPORT_DIRECTORIES,
}


def _has(user, *codes: str) -> bool:
    """Fail-closed check for any of the given permission codes."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return any(user_has_permission(user, code) for code in codes)


def user_can_view_exports(user) -> bool:
    """Whether the actor may open the Export Engine workspace."""
    return _has(user, EXPORTS_VIEW, EXPORTS_MANAGE)


def user_can_create_export(user) -> bool:
    """Whether the actor may request an export."""
    return _has(user, EXPORTS_CREATE, EXPORTS_MANAGE)


def user_can_download(user) -> bool:
    """Whether the actor may download a generated export."""
    return _has(user, EXPORTS_DOWNLOAD, EXPORTS_MANAGE)


def user_can_use_format(user, format_code: str) -> bool:
    """Whether the actor may generate the given output format."""
    code = FORMAT_PERMISSIONS.get(format_code)
    if not code:
        return False
    return _has(user, code, EXPORTS_MANAGE)


def user_can_export_source(user, source_type: str) -> bool:
    """Whether the actor may export the given source module."""
    code = SOURCE_PERMISSIONS.get(source_type)
    if not code:
        return False
    return _has(user, code, EXPORTS_MANAGE)


def user_can_export_sensitive(user) -> bool:
    """Whether the actor may export sensitive/confidential datasets."""
    return _has(user, EXPORTS_EXPORT_SENSITIVE, EXPORTS_MANAGE)


def user_can_export_bulk(user) -> bool:
    """Whether the actor may run bulk exports above the synchronous limit."""
    return _has(user, EXPORTS_EXPORT_BULK, EXPORTS_MANAGE)


def user_can_view_history(user) -> bool:
    """Whether the actor may view their own export history."""
    return _has(user, EXPORTS_VIEW_HISTORY, EXPORTS_MANAGE)


def user_can_view_all_history(user) -> bool:
    """Whether the actor may view the operational export history."""
    return _has(user, EXPORTS_VIEW_ALL_HISTORY, EXPORTS_MANAGE)


def user_can_cancel(user) -> bool:
    """Whether the actor may cancel an export request."""
    return _has(user, EXPORTS_CANCEL, EXPORTS_MANAGE)


def user_can_regenerate(user) -> bool:
    """Whether the actor may regenerate an export."""
    return _has(user, EXPORTS_REGENERATE, EXPORTS_MANAGE)


def user_can_manage_templates(user) -> bool:
    """Whether the actor may manage export templates."""
    return _has(user, EXPORTS_MANAGE_TEMPLATES, EXPORTS_MANAGE)


def user_can_manage_settings(user) -> bool:
    """Whether the actor may change export configuration."""
    return _has(user, EXPORTS_MANAGE_SETTINGS, EXPORTS_MANAGE)


def user_can_manage_exports(user) -> bool:
    """Whether the actor holds the master export-management permission."""
    return _has(user, EXPORTS_MANAGE)
