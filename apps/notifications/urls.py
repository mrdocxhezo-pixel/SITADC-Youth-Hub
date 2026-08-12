"""URL configuration for the Notifications & Announcements module."""

from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    # Inbox
    path("inbox/", views.InboxView.as_view(), name="inbox"),
    path("inbox/mark-all-read/", views.MarkAllReadView.as_view(), name="mark_all_read"),
    path(
        "notifications/<uuid:pk>/",
        views.NotificationDetailView.as_view(),
        name="notification_detail",
    ),
    path(
        "notifications/<uuid:pk>/read/",
        views.NotificationMarkReadView.as_view(),
        name="notification_mark_read",
    ),
    path(
        "notifications/<uuid:pk>/acknowledge/",
        views.NotificationAcknowledgeView.as_view(),
        name="notification_acknowledge",
    ),
    path(
        "notifications/<uuid:pk>/archive/",
        views.NotificationArchiveView.as_view(),
        name="notification_archive",
    ),
    path(
        "notifications/<uuid:pk>/open/",
        views.NotificationRedirectView.as_view(),
        name="notification_open",
    ),
    # Preferences
    path("preferences/", views.PreferenceUpdateView.as_view(), name="preferences"),
    # Templates (admin)
    path("templates/", views.TemplateListView.as_view(), name="template_list"),
    path("templates/new/", views.TemplateCreateView.as_view(), name="template_create"),
    path(
        "templates/<uuid:pk>/edit/",
        views.TemplateUpdateView.as_view(),
        name="template_update",
    ),
    # Rules (admin)
    path("rules/", views.RuleListView.as_view(), name="rule_list"),
    path("rules/new/", views.RuleCreateView.as_view(), name="rule_create"),
    path(
        "rules/<uuid:pk>/edit/",
        views.RuleUpdateView.as_view(),
        name="rule_update",
    ),
    # Announcements (admin)
    path(
        "announcements/",
        views.AnnouncementListView.as_view(),
        name="announcement_list",
    ),
    path(
        "announcements/new/",
        views.AnnouncementCreateView.as_view(),
        name="announcement_create",
    ),
    path(
        "announcements/<uuid:pk>/edit/",
        views.AnnouncementUpdateView.as_view(),
        name="announcement_update",
    ),
    path(
        "announcements/<uuid:pk>/publish/",
        views.AnnouncementPublishView.as_view(),
        name="announcement_publish",
    ),
    path(
        "announcements/<uuid:pk>/unpublish/",
        views.AnnouncementUnpublishView.as_view(),
        name="announcement_unpublish",
    ),
    path(
        "announcements/<uuid:pk>/dismiss/",
        views.AnnouncementDismissView.as_view(),
        name="announcement_dismiss",
    ),
    # Events & audit (admin)
    path("events/", views.EventListView.as_view(), name="event_list"),
    path("audit/", views.AuditLogListView.as_view(), name="audit_list"),
    # JSON endpoints
    path("api/unread-count/", views.UnreadCountView.as_view(), name="api_unread_count"),
    path(
        "api/recent-notifications/",
        views.RecentNotificationsView.as_view(),
        name="api_recent_notifications",
    ),
]
