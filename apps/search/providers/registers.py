"""Providers indexing registers and their entries."""

from __future__ import annotations

from apps.registers.models import Register, RegisterEntry
from apps.registers.selectors import visible_entries, visible_registers

from .base import SearchProvider, register


class RegisterProvider(SearchProvider):
    key = "registers.register"
    label = "Registers"
    model = Register
    detail_url_name = "registers:register_detail"
    view_permissions = ("registers.view", "registers.manage")
    search_fields = (
        "reference_number",
        "name",
        "code",
        "description",
    )
    title_field = "name"
    subtitle_fields = ("code",)
    reference_field = "reference_number"
    status_field = "status"

    def queryset(self, user):
        return visible_registers(user).select_related("category")


class RegisterEntryProvider(SearchProvider):
    key = "registers.entry"
    label = "Register Entries"
    model = RegisterEntry
    detail_url_name = "registers:entry_detail"
    view_permissions = ("registers.view", "registers.manage")
    search_fields = (
        "reference_number",
        "title",
        "description",
        "keywords",
    )
    title_field = "title"
    subtitle_fields = ("register__name", "reference_number")
    reference_field = "reference_number"
    status_field = "approval_status"

    def status_label(self, instance):
        value = getattr(instance, "approval_status", "") or ""
        if value and hasattr(instance, "get_approval_status_display"):
            return str(instance.get_approval_status_display())
        return value

    def queryset(self, user):
        return visible_entries(user).select_related("register")


register(RegisterProvider())
register(RegisterEntryProvider())
