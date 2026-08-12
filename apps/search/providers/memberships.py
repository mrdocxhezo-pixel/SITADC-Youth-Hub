"""Provider indexing member profiles."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.memberships.models import MemberProfile
from apps.memberships.permissions import user_can_view_members

from .base import SearchProvider, register


class MemberProfileProvider(SearchProvider):
    key = "memberships.profile"
    label = "Members"
    model = MemberProfile
    detail_url_name = "memberships:detail"
    view_permissions = ("membership.view", "membership.manage")
    search_fields = (
        "membership_id",
        "user__first_name",
        "user__last_name",
        "phone_primary",
        "email_personal",
        "district",
        "community",
        "category__name",
    )
    title_field = "user__full_name"
    subtitle_fields = ("membership_id", "status__name")
    reference_field = "membership_id"
    status_field = "status__name"

    def status_label(self, instance) -> str:
        status = getattr(instance, "status", None)
        if status is not None and getattr(status, "name", None):
            return status.name
        return ""

    def queryset(self, user) -> QuerySet:
        base = MemberProfile.objects.filter(is_deleted=False).select_related(
            "user", "category", "status"
        )
        if getattr(user, "is_superuser", False) or user_can_view_members(user):
            return base
        return base.none()


register(MemberProfileProvider())
