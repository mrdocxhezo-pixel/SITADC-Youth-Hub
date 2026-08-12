"""Admin configuration for the Calendar & Meetings module."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    ActionFollowUpRecord,
    AgendaItem,
    AttendanceCorrectionRecord,
    Calendar,
    CalendarEvent,
    CalendarShare,
    CalendarTypeConfig,
    ConfidentialAccessLog,
    DecisionVote,
    EventOccurrence,
    EventReminder,
    MattersArising,
    Meeting,
    MeetingActionItem,
    MeetingActivityRecord,
    MeetingAgenda,
    MeetingAttendance,
    MeetingDecision,
    MeetingDocument,
    MeetingInvitation,
    MeetingMinutes,
    MeetingParticipant,
    MeetingScheduleHistory,
    MeetingTemplate,
    MeetingVenue,
    MinuteSection,
)


class SoftDeleteAdminMixin:
    """Mixin to show soft-deleted objects in admin with filtering."""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        model = self.model
        if hasattr(model, "all_objects"):
            return model.all_objects.all()
        return qs


class IsActiveAdminMixin:
    """Mixin to add is_active to list_display and list_filter."""

    list_display = ("is_active", *getattr(admin.ModelAdmin, "list_display", ()))
    list_filter = ("is_active", *getattr(admin.ModelAdmin, "list_filter", ()))


@admin.register(CalendarTypeConfig)
class CalendarTypeConfigAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "default_visibility", "is_active", "created_at")
    list_filter = ("is_active", "default_visibility")
    search_fields = ("code", "name")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")


@admin.register(Calendar)
class CalendarAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "reference",
        "name",
        "calendar_type",
        "visibility",
        "owner",
        "organization_unit",
        "is_default",
        "is_active",
        "is_archived",
        "created_at",
    )
    list_filter = (
        "calendar_type",
        "visibility",
        "is_default",
        "is_active",
        "is_archived",
        "organization_unit",
        "access_scope",
    )
    search_fields = ("reference", "name", "description")
    readonly_fields = (
        "reference",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "deleted_at",
        "deleted_by",
        "archived_at",
        "archived_by",
    )
    autocomplete_fields = ("owner", "organization_unit", "access_scope")
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return Calendar.all_objects.select_related(
            "owner", "organization_unit", "access_scope"
        ).all()


@admin.register(CalendarShare)
class CalendarShareAdmin(admin.ModelAdmin):
    list_display = (
        "calendar",
        "permission_level",
        "user",
        "organization_unit",
        "access_scope",
        "expires_at",
        "created_at",
    )
    list_filter = ("permission_level", "calendar", "organization_unit", "access_scope")
    search_fields = ("calendar__name", "user__username", "organization_unit__name")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    autocomplete_fields = ("calendar", "user", "organization_unit", "access_scope")


@admin.register(CalendarEvent)
class CalendarEventAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "reference",
        "title",
        "calendar",
        "event_type",
        "status",
        "start_at",
        "end_at",
        "organizer",
        "is_recurring",
        "is_archived",
    )
    list_filter = (
        "event_type",
        "status",
        "priority",
        "confidentiality_level",
        "is_recurring",
        "is_archived",
        "calendar",
        "organizer",
    )
    search_fields = ("reference", "title", "description")
    readonly_fields = (
        "reference",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "deleted_at",
        "deleted_by",
        "archived_at",
        "archived_by",
        "cancelled_at",
    )
    autocomplete_fields = ("calendar", "venue", "organizer", "host")
    date_hierarchy = "start_at"

    def get_queryset(self, request):
        return CalendarEvent.all_objects.select_related(
            "calendar", "venue", "organizer", "host"
        ).all()


@admin.register(EventOccurrence)
class EventOccurrenceAdmin(admin.ModelAdmin):
    list_display = ("event", "occurrence_start", "occurrence_end", "is_cancelled")
    list_filter = ("is_cancelled",)
    search_fields = ("event__title",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    autocomplete_fields = ("event",)


@admin.register(EventReminder)
class EventReminderAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "meeting",
        "reminder_type",
        "lead_minutes",
        "channel",
        "status",
    )
    list_filter = ("reminder_type", "channel", "status", "recipient_type")
    search_fields = ("event__title", "meeting__title")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    autocomplete_fields = ("event", "meeting")


@admin.register(MeetingVenue)
class MeetingVenueAdmin(SoftDeleteAdminMixin, IsActiveAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "venue_type",
        "capacity",
        "organization_unit",
        "is_active",
        "is_archived",
    )
    list_filter = ("venue_type", "is_active", "is_archived", "organization_unit")
    search_fields = ("id", "name", "address", "description")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "deleted_at",
        "deleted_by",
        "archived_at",
        "archived_by",
    )
    autocomplete_fields = ("organization_unit", "access_scope")

    def get_queryset(self, request):
        return MeetingVenue.all_objects.select_related(
            "organization_unit", "access_scope"
        ).all()


@admin.register(MeetingTemplate)
class MeetingTemplateAdmin(SoftDeleteAdminMixin, IsActiveAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "code",
        "meeting_type",
        "is_active",
    )
    list_filter = ("meeting_type", "is_active")
    search_fields = ("id", "name", "code", "description")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "deleted_at",
        "deleted_by",
    )

    def get_queryset(self, request):
        return MeetingTemplate.all_objects.all()


@admin.register(Meeting)
class MeetingAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "reference",
        "title",
        "meeting_type",
        "status",
        "start_at",
        "end_at",
        "organizer",
        "venue",
        "mode",
        "is_archived",
    )
    list_filter = (
        "meeting_type",
        "status",
        "mode",
        "is_archived",
        "venue",
        "organizer",
        "template",
    )
    search_fields = ("reference", "title", "purpose", "objectives")
    readonly_fields = (
        "reference",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "deleted_at",
        "deleted_by",
        "archived_at",
        "archived_by",
    )
    autocomplete_fields = (
        "event",
        "venue",
        "organizer",
        "template",
        "program",
        "project",
        "organization_unit",
        "access_scope",
    )
    date_hierarchy = "start_at"

    def get_queryset(self, request):
        return Meeting.all_objects.select_related(
            "event", "venue", "organizer", "template", "program", "project"
        ).all()


@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "meeting",
        "user",
        "name_snapshot",
        "participant_type",
        "participant_status",
        "rsvp_status",
    )
    list_filter = ("participant_type", "participant_status", "rsvp_status", "meeting")
    search_fields = ("name_snapshot", "email_snapshot", "user__username")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    autocomplete_fields = ("meeting", "user", "invitation")


@admin.register(MeetingInvitation)
class MeetingInvitationAdmin(admin.ModelAdmin):
    list_display = ("meeting", "status", "sent_at", "rsvp_at", "delivery_channel")
    list_filter = ("status", "meeting", "delivery_channel")
    search_fields = ("meeting__title", "participant__email_snapshot")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "sent_at",
        "delivered_at",
        "rsvp_at",
    )
    autocomplete_fields = ("meeting",)


@admin.register(MeetingAgenda)
class MeetingAgendaAdmin(admin.ModelAdmin):
    list_display = (
        "meeting",
        "title",
        "status",
        "version",
        "prepared_by",
        "approved_by",
        "publication_date",
    )
    list_filter = ("status", "meeting")
    search_fields = ("title", "meeting__title")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "approved_at",
        "publication_date",
    )
    autocomplete_fields = ("meeting", "prepared_by", "reviewed_by", "approved_by")


@admin.register(AgendaItem)
class AgendaItemAdmin(admin.ModelAdmin):
    list_display = (
        "agenda",
        "item_number",
        "title",
        "item_type",
        "presenter",
        "display_order",
    )
    list_filter = ("item_type", "agenda")
    search_fields = ("title", "description", "agenda__title")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    autocomplete_fields = ("agenda", "presenter", "related_document")


@admin.register(MeetingAttendance)
class MeetingAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "meeting",
        "participant",
        "attendance_status",
        "attendance_mode",
        "verification_status",
        "check_in_at",
        "check_out_at",
    )
    list_filter = (
        "attendance_status",
        "attendance_mode",
        "verification_status",
        "meeting",
    )
    search_fields = ("participant__name_snapshot", "meeting__title")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "check_in_at",
        "check_out_at",
    )
    autocomplete_fields = ("meeting", "participant", "verified_by")


@admin.register(AttendanceCorrectionRecord)
class AttendanceCorrectionRecordAdmin(admin.ModelAdmin):
    list_display = (
        "attendance",
        "corrected_by",
        "previous_status",
        "new_status",
        "corrected_at",
    )
    list_filter = ("previous_status", "new_status")
    search_fields = ("attendance__meeting__title", "corrected_by__username")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "corrected_at",
    )
    autocomplete_fields = ("attendance", "corrected_by")


@admin.register(MeetingMinutes)
class MeetingMinutesAdmin(admin.ModelAdmin):
    list_display = (
        "meeting",
        "title",
        "status",
        "version",
        "prepared_by",
        "reviewed_by",
        "approved_by",
        "submitted_at",
    )
    list_filter = ("status", "meeting", "publication_status")
    search_fields = ("title", "summary", "meeting__title")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "approved_at",
        "submitted_at",
    )
    autocomplete_fields = (
        "meeting",
        "prepared_by",
        "reviewed_by",
        "approved_by",
    )


@admin.register(MinuteSection)
class MinuteSectionAdmin(admin.ModelAdmin):
    list_display = ("minutes", "section_type", "title", "display_order", "agenda_item")
    list_filter = ("section_type", "minutes")
    search_fields = ("title", "content", "minutes__title")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    autocomplete_fields = ("minutes", "agenda_item")


@admin.register(MeetingDecision)
class MeetingDecisionAdmin(admin.ModelAdmin):
    list_display = (
        "meeting",
        "reference",
        "decision_text",
        "decision_type",
        "status",
        "proposed_by",
        "voting_method",
    )
    list_filter = ("decision_type", "status", "voting_method", "meeting")
    search_fields = ("decision_text", "description", "meeting__title")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    autocomplete_fields = (
        "meeting",
        "proposed_by",
        "seconded_by",
        "agenda_item",
        "responsible_officer",
    )


@admin.register(DecisionVote)
class DecisionVoteAdmin(admin.ModelAdmin):
    list_display = ("decision", "participant", "vote_type", "voted_at")
    list_filter = ("vote_type", "decision")
    search_fields = ("participant__username", "decision__title")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    autocomplete_fields = ("decision", "participant")


@admin.register(MeetingActionItem)
class MeetingActionItemAdmin(admin.ModelAdmin):
    list_display = (
        "meeting",
        "reference",
        "description",
        "status",
        "priority",
        "owner",
        "due_date",
        "completion_date",
    )
    list_filter = ("status", "priority", "meeting", "owner")
    search_fields = ("reference", "description", "meeting__title")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "completion_date",
        "verified_at",
    )
    autocomplete_fields = ("meeting", "owner", "agenda_item", "decision")


@admin.register(ActionFollowUpRecord)
class ActionFollowUpRecordAdmin(admin.ModelAdmin):
    list_display = ("action_item", "update_type", "acted_by", "acted_at")
    list_filter = ("update_type",)
    search_fields = ("action_item__reference", "acted_by__username")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    autocomplete_fields = ("action_item", "acted_by")


@admin.register(MattersArising)
class MattersArisingAdmin(admin.ModelAdmin):
    list_display = ("source_meeting", "current_meeting", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("source_meeting__title", "current_meeting__title")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    autocomplete_fields = ("source_meeting", "current_meeting", "responsible_officer")


@admin.register(MeetingScheduleHistory)
class MeetingScheduleHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "meeting",
        "changed_by",
        "previous_start",
        "new_start",
        "reason",
        "changed_at",
    )
    list_filter = ("meeting",)
    search_fields = ("meeting__title", "reason", "changed_by__username")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "changed_at",
    )
    autocomplete_fields = ("meeting", "changed_by")


@admin.register(MeetingDocument)
class MeetingDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "meeting",
        "document_type",
        "is_public_to_participants",
        "published_at",
        "created_at",
    )
    list_filter = ("document_type", "is_public_to_participants", "meeting")
    search_fields = ("meeting__title", "notes")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    autocomplete_fields = ("meeting", "document")


@admin.register(MeetingActivityRecord)
class MeetingActivityRecordAdmin(admin.ModelAdmin):
    list_display = ("meeting", "action", "actor", "created_at")
    list_filter = ("action", "meeting")
    search_fields = ("details", "meeting__title", "actor__username")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    autocomplete_fields = ("meeting", "actor")


@admin.register(ConfidentialAccessLog)
class ConfidentialAccessLogAdmin(admin.ModelAdmin):
    list_display = ("meeting", "actor", "access_type", "target_model", "accessed_at")
    list_filter = ("access_type", "target_model", "meeting")
    search_fields = ("meeting__title", "actor__username", "target_reference")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    autocomplete_fields = ("meeting", "actor")


admin.site.site_header = _("SITADC Youth Hub Administration")
admin.site.site_title = _("SITADC Youth Hub")
admin.site.index_title = _("Calendar & Meetings Administration")
