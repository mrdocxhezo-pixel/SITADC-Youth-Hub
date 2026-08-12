"""Provider indexing the actor's own notifications."""

from __future__ import annotations

from apps.notifications.models import Notification
from apps.notifications.selectors import notification_queryset

from .base import SearchProvider, register


class NotificationProvider(SearchProvider):
    key = "notifications.notification"
    label = "Notifications"
    model = Notification
    detail_url_name = "notifications:notification_detail"
    view_permissions = ()
    search_fields = (
        "reference",
        "title",
        "message",
        "short_message",
    )
    title_field = "title"
    subtitle_fields = ("reference", "category")
    reference_field = "reference"
    status_field = "status"

    def queryset(self, user):
        return notification_queryset(user)


register(NotificationProvider())
