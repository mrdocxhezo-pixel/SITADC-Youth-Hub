"""URL configuration for the Calendar & Meetings module."""

from django.urls import path, re_path

from . import views

app_name = "meetings"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    # Calendars
    path("calendars/", views.CalendarListView.as_view(), name="calendar_list"),
    path("calendars/new/", views.CalendarCreateView.as_view(), name="calendar_create"),
    path(
        "calendars/<uuid:pk>/",
        views.CalendarDetailView.as_view(),
        name="calendar_detail",
    ),
    path(
        "calendars/<uuid:pk>/edit/",
        views.CalendarUpdateView.as_view(),
        name="calendar_update",
    ),
    path(
        "calendars/<uuid:pk>/archive/",
        views.CalendarArchiveView.as_view(),
        name="calendar_archive",
    ),
    path(
        "calendars/<uuid:pk>/restore/",
        views.CalendarRestoreView.as_view(),
        name="calendar_restore",
    ),
    path(
        "calendars/<uuid:calendar_pk>/shares/new/",
        views.CalendarShareCreateView.as_view(),
        name="calendar_share_create",
    ),
    path(
        "calendars/<uuid:calendar_pk>/shares/<uuid:share_pk>/revoke/",
        views.CalendarShareRevokeView.as_view(),
        name="calendar_share_revoke",
    ),
    # Events
    path("events/", views.EventListView.as_view(), name="event_list"),
    re_path(
        r"^events/new/(?:calendars/(?P<calendar_pk>[0-9a-f\-]{36})/)?$",
        views.EventCreateView.as_view(),
        name="event_create",
    ),
    path(
        "calendars/<uuid:calendar_pk>/events/new/",
        views.EventCreateView.as_view(),
        name="calendar_event_create",
    ),
    path("events/<uuid:pk>/", views.EventDetailView.as_view(), name="event_detail"),
    path(
        "events/<uuid:pk>/edit/", views.EventUpdateView.as_view(), name="event_update"
    ),
    path(
        "events/<uuid:pk>/status/<str:status>/",
        views.EventTransitionView.as_view(),
        name="event_transition",
    ),
    path(
        "events/<uuid:pk>/archive/",
        views.EventArchiveView.as_view(),
        name="event_archive",
    ),
    path(
        "events/<uuid:pk>/restore/",
        views.EventRestoreView.as_view(),
        name="event_restore",
    ),
    # Meetings
    path("meetings/", views.MeetingListView.as_view(), name="meeting_list"),
    path("meetings/new/", views.MeetingCreateView.as_view(), name="meeting_create"),
    path(
        "events/<uuid:event_pk>/meetings/new/",
        views.MeetingCreateView.as_view(),
        name="event_meeting_create",
    ),
    path(
        "meetings/<uuid:pk>/", views.MeetingDetailView.as_view(), name="meeting_detail"
    ),
    path(
        "meetings/<uuid:pk>/edit/",
        views.MeetingUpdateView.as_view(),
        name="meeting_update",
    ),
    path(
        "meetings/<uuid:pk>/status/<str:status>/",
        views.MeetingTransitionView.as_view(),
        name="meeting_transition",
    ),
    path(
        "meetings/<uuid:pk>/confirm/",
        views.MeetingConfirmView.as_view(),
        name="meeting_confirm",
    ),
    path(
        "meetings/<uuid:pk>/start/",
        views.MeetingStartView.as_view(),
        name="meeting_start",
    ),
    path(
        "meetings/<uuid:pk>/complete/",
        views.MeetingCompleteView.as_view(),
        name="meeting_complete",
    ),
    path(
        "meetings/<uuid:pk>/reschedule/",
        views.MeetingRescheduleView.as_view(),
        name="meeting_reschedule",
    ),
    path(
        "meetings/<uuid:pk>/postpone/",
        views.MeetingPostponeView.as_view(),
        name="meeting_postpone",
    ),
    path(
        "meetings/<uuid:pk>/cancel/",
        views.MeetingCancelView.as_view(),
        name="meeting_cancel",
    ),
    path(
        "meetings/<uuid:pk>/archive/",
        views.MeetingArchiveView.as_view(),
        name="meeting_archive",
    ),
    path(
        "meetings/<uuid:pk>/restore/",
        views.MeetingRestoreView.as_view(),
        name="meeting_restore",
    ),
    path(
        "meetings/<uuid:pk>/send-invitations/",
        views.MeetingSendInvitationsView.as_view(),
        name="meeting_send_invitations",
    ),
    path(
        "meetings/<uuid:pk>/quorum/",
        views.QuorumEvaluateView.as_view(),
        name="meeting_quorum",
    ),
    # Participants
    path(
        "meetings/<uuid:meeting_pk>/participants/new/",
        views.ParticipantCreateView.as_view(),
        name="participant_create",
    ),
    path(
        "meetings/<uuid:meeting_pk>/participants/<uuid:pk>/edit/",
        views.ParticipantUpdateView.as_view(),
        name="participant_update",
    ),
    path(
        "meetings/<uuid:meeting_pk>/participants/<uuid:pk>/invite/",
        views.ParticipantInviteView.as_view(),
        name="participant_invite",
    ),
    path(
        "meetings/<uuid:meeting_pk>/participants/<uuid:pk>/rsvp/",
        views.ParticipantRSVPView.as_view(),
        name="participant_rsvp",
    ),
    path(
        "meetings/<uuid:meeting_pk>/participants/<uuid:pk>/remove/",
        views.ParticipantRemoveView.as_view(),
        name="participant_remove",
    ),
    # Attendance
    path(
        "meetings/<uuid:meeting_pk>/attendance/<uuid:participant_pk>/record/",
        views.AttendanceRecordView.as_view(),
        name="attendance_record",
    ),
    path(
        "meetings/<uuid:meeting_pk>/attendance/<uuid:pk>/check-in/",
        views.AttendanceCheckInView.as_view(),
        name="attendance_check_in",
    ),
    path(
        "meetings/<uuid:meeting_pk>/attendance/<uuid:pk>/check-out/",
        views.AttendanceCheckOutView.as_view(),
        name="attendance_check_out",
    ),
    path(
        "meetings/<uuid:meeting_pk>/attendance/<uuid:attendance_pk>/verify/",
        views.AttendanceVerifyView.as_view(),
        name="attendance_verify",
    ),
    # Agendas
    path(
        "meetings/<uuid:meeting_pk>/agendas/new/",
        views.AgendaCreateView.as_view(),
        name="agenda_create",
    ),
    path(
        "meetings/<uuid:meeting_pk>/agendas/<uuid:pk>/",
        views.AgendaDetailView.as_view(),
        name="agenda_detail",
    ),
    path(
        "meetings/<uuid:meeting_pk>/agendas/<uuid:pk>/edit/",
        views.AgendaUpdateView.as_view(),
        name="agenda_update",
    ),
    path(
        "meetings/<uuid:meeting_pk>/agendas/<uuid:pk>/approve/",
        views.AgendaApproveView.as_view(),
        name="agenda_approve",
    ),
    path(
        "meetings/<uuid:meeting_pk>/agendas/<uuid:pk>/publish/",
        views.AgendaPublishView.as_view(),
        name="agenda_publish",
    ),
    path(
        "meetings/<uuid:meeting_pk>/agendas/<uuid:pk>/items/new/",
        views.AgendaItemCreateView.as_view(),
        name="agenda_item_create",
    ),
    path(
        "meetings/<uuid:meeting_pk>/agendas/<uuid:pk>/items/<uuid:item_pk>/edit/",
        views.AgendaItemUpdateView.as_view(),
        name="agenda_item_update",
    ),
    path(
        "meetings/<uuid:meeting_pk>/agendas/<uuid:pk>/items/<uuid:item_pk>/delete/",
        views.AgendaItemDeleteView.as_view(),
        name="agenda_item_delete",
    ),
    # Minutes
    path(
        "meetings/<uuid:meeting_pk>/minutes/new/",
        views.MinutesCreateView.as_view(),
        name="minutes_create",
    ),
    path(
        "meetings/<uuid:meeting_pk>/minutes/<uuid:pk>/",
        views.MinutesDetailView.as_view(),
        name="minutes_detail",
    ),
    path(
        "meetings/<uuid:meeting_pk>/minutes/<uuid:pk>/edit/",
        views.MinutesUpdateView.as_view(),
        name="minutes_update",
    ),
    path(
        "meetings/<uuid:meeting_pk>/minutes/<uuid:pk>/submit/",
        views.MinutesSubmitView.as_view(),
        name="minutes_submit",
    ),
    path(
        "meetings/<uuid:meeting_pk>/minutes/<uuid:pk>/review/",
        views.MinutesReviewView.as_view(),
        name="minutes_review",
    ),
    path(
        "meetings/<uuid:meeting_pk>/minutes/<uuid:pk>/approve/",
        views.MinutesApproveView.as_view(),
        name="minutes_approve",
    ),
    path(
        "meetings/<uuid:meeting_pk>/minutes/<uuid:pk>/return/",
        views.MinutesReturnView.as_view(),
        name="minutes_return",
    ),
    path(
        "meetings/<uuid:meeting_pk>/minutes/<uuid:pk>/sections/new/",
        views.MinuteSectionCreateView.as_view(),
        name="minute_section_create",
    ),
    # Decisions
    path(
        "meetings/<uuid:meeting_pk>/decisions/new/",
        views.DecisionCreateView.as_view(),
        name="decision_create",
    ),
    path(
        "meetings/<uuid:meeting_pk>/decisions/<uuid:pk>/edit/",
        views.DecisionUpdateView.as_view(),
        name="decision_update",
    ),
    path(
        "meetings/<uuid:meeting_pk>/decisions/<uuid:pk>/approve/",
        views.DecisionApproveView.as_view(),
        name="decision_approve",
    ),
    path(
        "meetings/<uuid:meeting_pk>/decisions/<uuid:pk>/implement/",
        views.DecisionImplementView.as_view(),
        name="decision_implement",
    ),
    # Action items
    path(
        "meetings/<uuid:meeting_pk>/actions/new/",
        views.ActionItemCreateView.as_view(),
        name="action_item_create",
    ),
    path(
        "meetings/<uuid:meeting_pk>/actions/<uuid:pk>/edit/",
        views.ActionItemUpdateView.as_view(),
        name="action_item_update",
    ),
    path(
        "meetings/<uuid:meeting_pk>/actions/<uuid:pk>/progress/",
        views.ActionItemUpdateProgressView.as_view(),
        name="action_item_progress",
    ),
    path(
        "meetings/<uuid:meeting_pk>/actions/<uuid:pk>/complete/",
        views.ActionItemCompleteView.as_view(),
        name="action_item_complete",
    ),
    path(
        "meetings/<uuid:meeting_pk>/actions/<uuid:pk>/verify/",
        views.ActionItemVerifyView.as_view(),
        name="action_item_verify",
    ),
    path(
        "meetings/<uuid:meeting_pk>/actions/<uuid:pk>/escalate/",
        views.ActionItemEscalateView.as_view(),
        name="action_item_escalate",
    ),
    # Documents
    path(
        "meetings/<uuid:meeting_pk>/documents/new/",
        views.MeetingDocumentLinkView.as_view(),
        name="meeting_document_link",
    ),
    path(
        "meetings/<uuid:meeting_pk>/documents/<uuid:pk>/unlink/",
        views.MeetingDocumentUnlinkView.as_view(),
        name="meeting_document_unlink",
    ),
    # Templates & venues
    path("templates/", views.TemplateListView.as_view(), name="template_list"),
    path("templates/new/", views.TemplateCreateView.as_view(), name="template_create"),
    path(
        "templates/<uuid:pk>/edit/",
        views.TemplateUpdateView.as_view(),
        name="template_update",
    ),
    path("venues/", views.VenueListView.as_view(), name="venue_list"),
    path("venues/new/", views.VenueCreateView.as_view(), name="venue_create"),
    path(
        "venues/<uuid:pk>/edit/", views.VenueUpdateView.as_view(), name="venue_update"
    ),
    path(
        "venues/<uuid:pk>/archive/",
        views.VenueArchiveView.as_view(),
        name="venue_archive",
    ),
    # Export
    path("export/", views.MeetingExportView.as_view(), name="export"),
    path("export/<str:fmt>/", views.MeetingExportView.as_view(), name="export_format"),
    path("export/<uuid:pk>/", views.MeetingExportView.as_view(), name="export_meeting"),
    path(
        "export/<uuid:pk>/<str:fmt>/",
        views.MeetingExportView.as_view(),
        name="export_meeting_format",
    ),
]
