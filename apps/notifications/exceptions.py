"""Exceptions for the Notifications module."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


class NotificationError(Exception):
    """Base exception for notification errors."""

    def __init__(self, message: str | None = None, code: str | None = None):
        self.code = code
        super().__init__(message or self.default_message)

    @property
    def default_message(self) -> str:
        return _("A notification error occurred.")


class NotificationPermissionDenied(PermissionDenied, NotificationError):
    """Raised when a user lacks permission for a notification action.

    Subclasses Django's ``PermissionDenied`` so middleware, views and tests
    can treat it as a standard permission failure while still carrying a
    module error ``code``.
    """

    @property
    def default_message(self) -> str:
        return _("You do not have permission to perform this notification action.")


class InvalidNotificationTemplateError(NotificationError):
    """Raised when a notification template is invalid."""

    @property
    def default_message(self) -> str:
        return _("The notification template is invalid.")


class NotificationRecipientError(NotificationError):
    """Raised when recipient resolution fails."""

    @property
    def default_message(self) -> str:
        return _("Failed to resolve notification recipients.")


class NotificationSchedulingError(NotificationError):
    """Raised when notification scheduling fails."""

    @property
    def default_message(self) -> str:
        return _("Failed to schedule the notification.")


class NotificationDeliveryError(NotificationError):
    """Raised when notification delivery fails."""

    @property
    def default_message(self) -> str:
        return _("Failed to deliver the notification.")


class NotificationChannelUnavailableError(NotificationError):
    """Raised when a notification channel is not available."""

    @property
    def default_message(self) -> str:
        return _("The requested notification channel is not available.")


class NotificationPreferenceError(NotificationError):
    """Raised when notification preference operations fail."""

    @property
    def default_message(self) -> str:
        return _("Failed to process notification preferences.")


class NotificationRuleError(NotificationError):
    """Raised when notification rule operations fail."""

    @property
    def default_message(self) -> str:
        return _("Failed to process the notification rule.")


class NotificationEscalationError(NotificationError):
    """Raised when notification escalation fails."""

    @property
    def default_message(self) -> str:
        return _("Failed to escalate the notification.")


class BulkNotificationError(NotificationError):
    """Raised when bulk notification operations fail."""

    @property
    def default_message(self) -> str:
        return _("Failed to process bulk notifications.")


class AnnouncementError(NotificationError):
    """Raised when announcement operations fail."""

    @property
    def default_message(self) -> str:
        return _("An announcement error occurred.")


class TemplateRenderError(NotificationError):
    """Raised when template rendering fails."""

    @property
    def default_message(self) -> str:
        return _("Failed to render the notification template.")


class NotificationDeduplicationError(NotificationError):
    """Raised when deduplication logic fails."""

    @property
    def default_message(self) -> str:
        return _("Failed to process notification deduplication.")