"""Providers for people-directory datasets (source type DIRECTORY).

One provider per directory kind.  Each delegates its queryset to the source
module's fail-closed selector so a user can only ever see the people they are
authorized to know about.
"""

from __future__ import annotations

from apps.leadership.models import LeadershipProfile
from apps.leadership.permissions import LEADERSHIP_VIEW
from apps.memberships.models import MemberProfile
from apps.memberships.permissions import MEMBERSHIP_VIEW
from apps.stakeholders.models import Stakeholder
from apps.stakeholders.permissions import PARTNERS_VIEW, PARTNERS_VIEW_DIRECTORY
from apps.stakeholders.selectors import visible_stakeholders
from apps.volunteers.models import VolunteerProfile
from apps.volunteers.permissions import VOLUNTEERS_VIEW
from apps.volunteers.selectors import visible_volunteer_profiles

from ..constants import ExportSourceType
from ..renderers.base import ExportColumn
from .base import BaseProvider, register


class VolunteerDirectoryProvider(BaseProvider):
    """Export the volunteer directory."""

    key = "directory.volunteers"
    source_type = ExportSourceType.DIRECTORY
    label = "Volunteer Directory"
    model = VolunteerProfile
    view_permissions = (VOLUNTEERS_VIEW,)
    manage_permissions = (VOLUNTEERS_VIEW,)
    reference_field = "reference_number"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn("full_name", "Name", accessor=lambda obj: obj.user.full_name),
        ExportColumn("membership_number", "Membership Number"),
        ExportColumn(
            "category",
            "Category",
            accessor=lambda obj: obj.category.name if obj.category_id else "",
        ),
        ExportColumn(
            "volunteer_type",
            "Type",
            accessor=lambda obj: (
                obj.volunteer_type.name if obj.volunteer_type_id else ""
            ),
        ),
        ExportColumn("availability", "Availability"),
        ExportColumn("region", "Region"),
        ExportColumn("district", "District"),
        ExportColumn("status", "Status"),
        ExportColumn("start_date", "Start Date"),
        ExportColumn("end_date", "End Date"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return visible_volunteer_profiles(user)


class MemberDirectoryProvider(BaseProvider):
    """Export the member directory."""

    key = "directory.members"
    source_type = ExportSourceType.DIRECTORY
    label = "Member Directory"
    model = MemberProfile
    view_permissions = (MEMBERSHIP_VIEW,)
    manage_permissions = (MEMBERSHIP_VIEW,)
    reference_field = "membership_id"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("membership_id", "Membership ID"),
        ExportColumn("full_name", "Name", accessor=lambda obj: obj.full_name),
        ExportColumn(
            "category",
            "Category",
            accessor=lambda obj: obj.category.name if obj.category_id else "",
        ),
        ExportColumn(
            "membership_type",
            "Type",
            accessor=lambda obj: (
                obj.membership_type.name if obj.membership_type_id else ""
            ),
        ),
        ExportColumn(
            "level",
            "Level",
            accessor=lambda obj: obj.level.name if obj.level_id else "",
        ),
        ExportColumn("province", "Province"),
        ExportColumn("district", "District"),
        ExportColumn("community", "Community"),
        ExportColumn("date_joined", "Date Joined"),
        ExportColumn("expiry_date", "Expiry Date"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return MemberProfile.objects.filter(is_deleted=False).select_related(
            "category", "membership_type", "level"
        )


class LeadershipDirectoryProvider(BaseProvider):
    """Export the leadership directory."""

    key = "directory.leadership"
    source_type = ExportSourceType.DIRECTORY
    label = "Leadership Directory"
    model = LeadershipProfile
    view_permissions = (LEADERSHIP_VIEW,)
    manage_permissions = (LEADERSHIP_VIEW,)
    reference_field = "reference_number"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn("full_name", "Name", accessor=lambda obj: obj.user.full_name),
        ExportColumn("leadership_level", "Leadership Level"),
        ExportColumn(
            "position",
            "Position",
            accessor=lambda obj: obj.position.title if obj.position_id else "",
        ),
        ExportColumn(
            "organizational_unit",
            "Unit",
            accessor=lambda obj: (
                obj.organizational_unit.name if obj.organizational_unit_id else ""
            ),
        ),
        ExportColumn("term_status", "Term Status"),
        ExportColumn("appointment_date", "Appointment Date"),
        ExportColumn("term_expiry_date", "Term Expiry"),
        ExportColumn("status", "Status"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return LeadershipProfile.objects.filter(is_deleted=False).select_related(
            "position", "organizational_unit"
        )


class StakeholderDirectoryProvider(BaseProvider):
    """Export the stakeholder / partner directory."""

    key = "directory.stakeholders"
    source_type = ExportSourceType.DIRECTORY
    label = "Stakeholder Directory"
    model = Stakeholder
    view_permissions = (PARTNERS_VIEW, PARTNERS_VIEW_DIRECTORY)
    manage_permissions = (PARTNERS_VIEW,)
    reference_field = "reference_number"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn("legal_name", "Legal Name"),
        ExportColumn("trading_name", "Trading Name"),
        ExportColumn("acronym", "Acronym"),
        ExportColumn("entity_type", "Entity Type"),
        ExportColumn(
            "relationship_type",
            "Relationship",
            accessor=lambda obj: (
                obj.relationship_type.name if obj.relationship_type_id else ""
            ),
        ),
        ExportColumn(
            "classification",
            "Classification",
            accessor=lambda obj: (
                obj.classification.name if obj.classification_id else ""
            ),
        ),
        ExportColumn("province_or_region", "Region"),
        ExportColumn("district", "District"),
        ExportColumn("country", "Country"),
        ExportColumn("general_email", "Email", sensitive=True),
        ExportColumn("general_phone", "Phone", sensitive=True),
        ExportColumn("status", "Status"),
        ExportColumn("confidentiality", "Confidentiality"),
        ExportColumn("last_engagement_date", "Last Engagement"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return visible_stakeholders(user)


register(VolunteerDirectoryProvider())
register(MemberDirectoryProvider())
register(LeadershipDirectoryProvider())
register(StakeholderDirectoryProvider())
