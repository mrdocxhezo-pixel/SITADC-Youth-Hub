"""Providers for organizational registers (source type REGISTER)."""

from __future__ import annotations

from apps.registers.models import Register, RegisterEntry
from apps.registers.permissions import REGISTER_MANAGE, REGISTER_VIEW
from apps.registers.selectors import visible_entries, visible_registers

from ..constants import ExportSourceType
from ..renderers.base import ExportColumn
from .base import BaseProvider, register


class RegisterProvider(BaseProvider):
    """Export the register catalogue."""

    key = "registers.register"
    source_type = ExportSourceType.REGISTER
    label = "Organizational Registers"
    model = Register
    view_permissions = (REGISTER_VIEW,)
    manage_permissions = (REGISTER_MANAGE,)
    reference_field = "reference_number"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn("name", "Register Name"),
        ExportColumn("code", "Code"),
        ExportColumn(
            "category",
            "Category",
            accessor=lambda obj: obj.category.name if obj.category_id else "",
        ),
        ExportColumn("responsible_department", "Responsible Department"),
        ExportColumn("status", "Status"),
        ExportColumn("confidentiality", "Confidentiality"),
        ExportColumn("retention_policy", "Retention Policy"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return visible_registers(user).select_related("category")


class RegisterEntryProvider(BaseProvider):
    """Export register entries."""

    key = "registers.entry"
    source_type = ExportSourceType.REGISTER
    label = "Register Entries"
    model = RegisterEntry
    view_permissions = (REGISTER_VIEW,)
    manage_permissions = (REGISTER_MANAGE,)
    reference_field = "reference_number"
    status_field = "approval_status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn(
            "register",
            "Register",
            accessor=lambda obj: obj.register.name if obj.register_id else "",
        ),
        ExportColumn("title", "Entry Title"),
        ExportColumn("keywords", "Keywords"),
        ExportColumn("approval_status", "Approval Status"),
        ExportColumn("status", "Status"),
        ExportColumn("confidentiality", "Confidentiality"),
        ExportColumn("reporting_period_start", "Period Start"),
        ExportColumn("reporting_period_end", "Period End"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return visible_entries(user).select_related("register")


register(RegisterProvider())
register(RegisterEntryProvider())
