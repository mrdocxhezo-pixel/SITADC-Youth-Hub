"""Views for the Notifications & Announcements module.

Every view is permission checked server side; the recipient's own inbox is
always available to authenticated users, while administration views require
the module management permissions.
"""

from __future__ import annotations

import json as _json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from .constants import (
    AnnouncementAudience,
    DeliveryChannel,
    NotificationCategory,
    NotificationPriority,
    NotificationStatus,
    ReadStatus,
)
from .forms import (
    AnnouncementForm,
    NotificationPreferenceForm,
    NotificationRuleForm,
    NotificationSearchForm,
    NotificationTemplateForm,
)
from .models import (
    Notification,
    NotificationAuditRecord,
    NotificationEvent,
    NotificationPreference,
    NotificationRule,
    NotificationTemplate,
    SystemAnnouncement,
)
from .permissions import (
    ANNOUNCEMENT_CREATE,
    ANNOUNCEMENT_MANAGE,
    NOTIFICATION_MANAGE_RULES,
    NOTIFICATION_MANAGE_TEMPLATES,
    user_can_manage_announcements,
    user_can_manage_notifications,
    user_can_manage_rules,
    user_can_manage_templates,
)
from .selectors import (
    action_required_notifications,
    active_notifications,
    announcement_queryset,
    announcement_summary_counts,
    category_breakdown,
    digest_summary_counts,
    expired_notifications,
    notification_preference_for,
    rule_queryset,
    template_queryset,
    unread_count,
)
from .services import (
    AcknowledgeNotificationService,
    AnnouncementService,
    ArchiveNotificationService,
    MarkAllNotificationsReadService,
    MarkNotificationReadService,
    NotificationEventService,
    NotificationPreferenceService,
    PublishAnnouncementService,
    RuleService,
    SendNotificationService,
    TemplateService,
    UnpublishAnnouncementService,
)

logger = logging.getLogger(__name__)


def _apply_service_errors(form, exc: Exception) -> None:
    if isinstance(exc, PermissionDenied):
        form.add_error(None, str(exc))
        return
    if hasattr(exc, "message_dict"):
        for field_name, field_messages in exc.message_dict.items():
            target = field_name if field_name in form.fields else None
            for message in field_messages:
                form.add_error(target, message)
        return
    for message in getattr(exc, "messages", [str(exc)]):
        form.add_error(None, message)


def _require_inbox_permission(user) -> bool:
    return bool(user and user.is_authenticated)


class NotificationPermissionMixin(LoginRequiredMixin):
    """Require authentication for all notification views."""

    request: object

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


# ── Dashboard ────────────────────────────────────────────────────────────


class DashboardView(NotificationPermissionMixin, TemplateView):
    template_name = "notifications/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update(
            {
                "summary": digest_summary_counts(user),
                "unread_count": unread_count(user),
                "action_required": action_required_notifications(user)[:8],
                "recent_notifications": active_notifications(user)[:10],
                "announcements": announcement_queryset(user)[:5],
                "announcement_counts": announcement_summary_counts(),
                "categories": category_breakdown(user),
                "can_manage": user_can_manage_notifications(user),
                "can_manage_templates": user_can_manage_templates(user),
                "can_manage_rules": user_can_manage_rules(user),
                "can_manage_announcements": user_can_manage_announcements(user),
            }
        )
        return context


# ── Inbox ────────────────────────────────────────────────────────────────


class InboxView(NotificationPermissionMixin, ListView):
    template_name = "notifications/inbox.html"
    context_object_name = "notifications"
    paginate_by = 25

    def get_queryset(self):
        user = self.request.user
        queryset = active_notifications(user)
        queryset = queryset.select_related("actor", "recipient", "template")
        queryset = queryset.prefetch_related("delivery_attempts")

        status = self.request.GET.get("status")
        if status == "unread":
            queryset = queryset.filter(read_status=ReadStatus.UNREAD)
        elif status == "read":
            queryset = queryset.filter(read_status=ReadStatus.READ)
        elif status == "action":
            queryset = queryset.action_required()
        elif status == "archived":
            queryset = Notification.all_objects.for_user(user).filter(
                is_archived=True
            ).recent_first()
            queryset = queryset.select_related("actor", "recipient", "template")

        search_form = NotificationSearchForm(self.request.GET)
        if search_form.is_valid():
            queryset = search_form.filter(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        search_form = NotificationSearchForm(self.request.GET)
        context.update(
            {
                "search_form": search_form,
                "unread_count": unread_count(user),
                "categories": category_breakdown(user),
                "status_filter": self.request.GET.get("status", ""),
            }
        )
        return context


class NotificationDetailView(NotificationPermissionMixin, DetailView):
    template_name = "notifications/notification_detail.html"
    context_object_name = "notification"
    model = Notification

    def get_queryset(self):
        return Notification.all_objects.for_user(self.request.user).select_related(
            "actor", "recipient", "template"
        ).prefetch_related("delivery_attempts")

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        notification = self.object
        if notification.read_status != ReadStatus.READ:
            try:
                MarkNotificationReadService(user=request.user).execute(notification)
            except PermissionDenied:
                pass
        return response


class NotificationMarkReadView(NotificationPermissionMixin, View):
    """Mark a single notification read (AJAX/JSON or form POST)."""

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification.objects.filter(recipient=request.user), pk=pk
        )
        try:
            MarkNotificationReadService(user=request.user).execute(notification)
            ok = True
        except PermissionDenied:
            ok = False
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": ok, "unread": unread_count(request.user)})
        messages.success(request, _("Notification marked as read."))
        return redirect(notification)

    def get(self, request, pk):
        notification = get_object_or_404(
            Notification.objects.filter(recipient=request.user), pk=pk
        )
        try:
            MarkNotificationReadService(user=request.user).execute(notification)
        except PermissionDenied:
            pass
        return redirect("notifications:notification_detail", pk=pk)


class NotificationAcknowledgeView(NotificationPermissionMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(
            Notification.objects.filter(recipient=request.user), pk=pk
        )
        try:
            AcknowledgeNotificationService(user=request.user).execute(notification)
            ok = True
        except PermissionDenied:
            ok = False
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": ok, "unread": unread_count(request.user)})
        messages.success(request, _("Notification acknowledged."))
        return redirect("notifications:notification_detail", pk=pk)


class NotificationArchiveView(NotificationPermissionMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(
            Notification.objects.filter(recipient=request.user), pk=pk
        )
        try:
            ArchiveNotificationService(user=request.user).execute(notification)
            ok = True
        except PermissionDenied:
            ok = False
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": ok, "unread": unread_count(request.user)})
        messages.success(request, _("Notification archived."))
        return redirect("notifications:inbox")


class MarkAllReadView(NotificationPermissionMixin, View):
    def post(self, request):
        try:
            count = MarkAllNotificationsReadService(user=request.user).execute()
            messages.success(request, _("%(count)s notification(s) marked read.") % {"count": count})
        except PermissionDenied:
            pass
        return redirect("notifications:inbox")


class NotificationRedirectView(NotificationPermissionMixin, View):
    """Resolve a notification's deep link (validated internal URL)."""

    def get(self, request, pk):
        notification = get_object_or_404(
            Notification.objects.filter(recipient=request.user), pk=pk
        )
        if notification.read_status != ReadStatus.READ:
            try:
                MarkNotificationReadService(user=request.user).execute(notification)
            except PermissionDenied:
                pass
        deep_link = notification.deep_link
        if not deep_link:
            return redirect("notifications:notification_detail", pk=pk)
        # Only allow relative URLs to avoid open redirects.
        if deep_link.startswith(("http://", "https://")):
            return redirect("notifications:notification_detail", pk=pk)
        return redirect(deep_link)


# ── Preferences ──────────────────────────────────────────────────────────


class PreferenceUpdateView(NotificationPermissionMixin, FormView):
    template_name = "notifications/preference_form.html"
    form_class = NotificationPreferenceForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = notification_preference_for(self.request.user)
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        preference = form.save(commit=False)
        preference.user = user
        preference.save()
        NotificationPreferenceService(user=user).execute(user=user, instance=preference)
        messages.success(self.request, _("Notification preferences saved."))
        return redirect("notifications:preferences")


# ── Templates (admin) ─────────────────────────────────────────────────────


class TemplateListView(NotificationPermissionMixin, ListView):
    template_name = "notifications/template_directory.html"
    context_object_name = "templates"
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_templates(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return template_queryset(self.request.user).select_related("organization_unit")


class TemplateCreateView(NotificationPermissionMixin, FormView):
    template_name = "notifications/template_form.html"
    form_class = NotificationTemplateForm

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_templates(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            TemplateService(user=self.request.user).execute(
                code=data["code"],
                name=data["name"],
                description=data.get("description", ""),
                category=data["category"],
                event_type=data.get("event_type", ""),
                channel=data["channel"],
                subject_template=data.get("subject_template", ""),
                title_template=data["title_template"],
                message_template=data["message_template"],
                short_message_template=data.get("short_message_template", ""),
                action_label=data.get("action_label", ""),
                priority=data["priority"],
                required_variables=data.get("required_variables", []),
                is_active=data["is_active"],
                organization_unit=data.get("organization_unit"),
            )
        except PermissionDenied:
            raise
        except Exception as exc:  # noqa: BLE001
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Notification template created."))
        return redirect("notifications:template_list")


class TemplateUpdateView(NotificationPermissionMixin, FormView):
    template_name = "notifications/template_form.html"
    form_class = NotificationTemplateForm

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_templates(request.user):
            raise PermissionDenied
        self.object = get_object_or_404(NotificationTemplate, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            TemplateService(user=self.request.user).execute(
                code=data["code"],
                name=data["name"],
                description=data.get("description", ""),
                category=data["category"],
                event_type=data.get("event_type", ""),
                channel=data["channel"],
                subject_template=data.get("subject_template", ""),
                title_template=data["title_template"],
                message_template=data["message_template"],
                short_message_template=data.get("short_message_template", ""),
                action_label=data.get("action_label", ""),
                priority=data["priority"],
                required_variables=data.get("required_variables", []),
                is_active=data["is_active"],
                organization_unit=data.get("organization_unit"),
                instance=self.object,
            )
        except PermissionDenied:
            raise
        except Exception as exc:  # noqa: BLE001
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Notification template updated."))
        return redirect("notifications:template_list")


# ── Rules (admin) ─────────────────────────────────────────────────────────


class RuleListView(NotificationPermissionMixin, ListView):
    template_name = "notifications/rule_directory.html"
    context_object_name = "rules"
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_rules(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return rule_queryset(self.request.user).select_related("template", "recipient_role")


class RuleCreateView(NotificationPermissionMixin, FormView):
    template_name = "notifications/rule_form.html"
    form_class = NotificationRuleForm

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_rules(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            RuleService(user=self.request.user).execute(
                name=data["name"],
                event_type=data["event_type"],
                category=data["category"],
                notification_type=data["notification_type"],
                priority=data["priority"],
                template=data.get("template"),
                channels=data.get("channels"),
                recipient_user=data.get("recipient_user"),
                recipient_role=data.get("recipient_role"),
                recipient_type=data.get("recipient_type", "USER"),
                delay_minutes=data.get("delay_minutes", 0),
                reminder_enabled=data["reminder_enabled"],
                reminder_offsets=data.get("reminder_offsets", []),
                escalation_enabled=data["escalation_enabled"],
                escalation_level=data.get("escalation_level", ""),
                escalation_after_hours=data.get("escalation_after_hours", 24),
                digest_eligible=data["digest_eligible"],
                is_active=data["is_active"],
                organization_unit=data.get("organization_unit"),
                sort_order=data.get("sort_order", 0),
            )
        except PermissionDenied:
            raise
        except Exception as exc:  # noqa: BLE001
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Notification rule created."))
        return redirect("notifications:rule_list")


class RuleUpdateView(NotificationPermissionMixin, FormView):
    template_name = "notifications/rule_form.html"
    form_class = NotificationRuleForm

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_rules(request.user):
            raise PermissionDenied
        self.object = get_object_or_404(NotificationRule, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            RuleService(user=self.request.user).execute(
                name=data["name"],
                event_type=data["event_type"],
                category=data["category"],
                notification_type=data["notification_type"],
                priority=data["priority"],
                template=data.get("template"),
                channels=data.get("channels"),
                recipient_user=data.get("recipient_user"),
                recipient_role=data.get("recipient_role"),
                recipient_type=data.get("recipient_type", "USER"),
                delay_minutes=data.get("delay_minutes", 0),
                reminder_enabled=data["reminder_enabled"],
                reminder_offsets=data.get("reminder_offsets", []),
                escalation_enabled=data["escalation_enabled"],
                escalation_level=data.get("escalation_level", ""),
                escalation_after_hours=data.get("escalation_after_hours", 24),
                digest_eligible=data["digest_eligible"],
                is_active=data["is_active"],
                organization_unit=data.get("organization_unit"),
                sort_order=data.get("sort_order", 0),
                instance=self.object,
            )
        except PermissionDenied:
            raise
        except Exception as exc:  # noqa: BLE001
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Notification rule updated."))
        return redirect("notifications:rule_list")


# ── Announcements (admin) ─────────────────────────────────────────────────


class AnnouncementListView(NotificationPermissionMixin, ListView):
    template_name = "notifications/announcement_directory.html"
    context_object_name = "announcements"
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_announcements(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return SystemAnnouncement.objects.all().order_by("-publish_at")


class AnnouncementCreateView(NotificationPermissionMixin, FormView):
    template_name = "notifications/announcement_form.html"
    form_class = AnnouncementForm

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_announcements(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AnnouncementService(user=self.request.user).execute(
                title=data["title"],
                message=data["message"],
                announcement_type=data["announcement_type"],
                audience_type=data["audience_type"],
                audience_roles=data.get("audience_roles"),
                audience_units=data.get("audience_units"),
                priority=data["priority"],
                category=data["category"],
                publish_at=data.get("publish_at") or timezone.now(),
                expires_at=data.get("expires_at"),
                publish_now=data.get("publish_now", False),
                is_dismissible=data["is_dismissible"],
                acknowledgement_required=data["acknowledgement_required"],
                deep_link=data.get("deep_link", ""),
                organization_unit=data.get("organization_unit"),
            )
        except PermissionDenied:
            raise
        except Exception as exc:  # noqa: BLE001
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Announcement created."))
        return redirect("notifications:announcement_list")


class AnnouncementUpdateView(NotificationPermissionMixin, FormView):
    template_name = "notifications/announcement_form.html"
    form_class = AnnouncementForm

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_announcements(request.user):
            raise PermissionDenied
        self.object = get_object_or_404(SystemAnnouncement, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object
        return kwargs

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AnnouncementService(user=self.request.user).execute(
                title=data["title"],
                message=data["message"],
                announcement_type=data["announcement_type"],
                audience_type=data["audience_type"],
                audience_roles=data.get("audience_roles"),
                audience_units=data.get("audience_units"),
                priority=data["priority"],
                category=data["category"],
                publish_at=data.get("publish_at") or self.object.publish_at,
                expires_at=data.get("expires_at"),
                publish_now=data.get("publish_now", False),
                is_dismissible=data["is_dismissible"],
                acknowledgement_required=data["acknowledgement_required"],
                deep_link=data.get("deep_link", ""),
                organization_unit=data.get("organization_unit"),
                instance=self.object,
            )
        except PermissionDenied:
            raise
        except Exception as exc:  # noqa: BLE001
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Announcement updated."))
        return redirect("notifications:announcement_list")


class AnnouncementPublishView(NotificationPermissionMixin, View):
    def post(self, request, pk):
        announcement = get_object_or_404(SystemAnnouncement, pk=pk)
        try:
            PublishAnnouncementService(user=request.user).execute(announcement)
            messages.success(request, _("Announcement published and delivered to its audience."))
        except PermissionDenied:
            messages.error(request, _("You do not have permission to publish announcements."))
        return redirect("notifications:announcement_list")


class AnnouncementUnpublishView(NotificationPermissionMixin, View):
    def post(self, request, pk):
        announcement = get_object_or_404(SystemAnnouncement, pk=pk)
        try:
            UnpublishAnnouncementService(user=request.user).execute(announcement)
            messages.success(request, _("Announcement unpublished."))
        except PermissionDenied:
            messages.error(request, _("You do not have permission to unpublish announcements."))
        return redirect("notifications:announcement_list")


# ── Public announcement read / dismiss ───────────────────────────────────


class AnnouncementDismissView(NotificationPermissionMixin, View):
    """Dismiss a dismissible announcement (AJAX/JSON or form POST)."""

    def post(self, request, pk):
        announcement = get_object_or_404(SystemAnnouncement, pk=pk)
        if not announcement.is_dismissible:
            return JsonResponse({"ok": False}, status=403)
        from .models import AnnouncementDismissal

        AnnouncementDismissal.objects.get_or_create(
            announcement=announcement, user=request.user
        )
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True})
        return redirect(request.META.get("HTTP_REFERER", "/"))


# ── Events (admin / debug) ────────────────────────────────────────────────


class EventListView(NotificationPermissionMixin, ListView):
    template_name = "notifications/event_directory.html"
    context_object_name = "events"
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_notifications(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return NotificationEvent.objects.all().select_related("actor").order_by("-created_at")


class AuditLogListView(NotificationPermissionMixin, ListView):
    template_name = "notifications/audit_directory.html"
    context_object_name = "audit_records"
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_notifications(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return NotificationAuditRecord.objects.all().select_related("actor").order_by("-created_at")


# ── JSON endpoints (bell / polling) ───────────────────────────────────────


class UnreadCountView(NotificationPermissionMixin, View):
    """JSON endpoint returning the unread + action counts for the bell."""

    def get(self, request):
        return JsonResponse(
            {
                "unread": unread_count(request.user),
                "action_required": action_required_notifications(request.user).count(),
            }
        )


class RecentNotificationsView(NotificationPermissionMixin, View):
    """JSON endpoint returning recent notifications for the dropdown."""

    def get(self, request):
        items = active_notifications(request.user)[:8]
        data = [
            {
                "id": str(n.pk),
                "title": n.title,
                "short_message": n.short_message or n.title,
                "created_at": n.created_at.isoformat(),
                "notification_type": n.notification_type,
                "read_status": n.read_status,
                "priority": n.priority,
                "url": f"/notifications/{n.pk}/",
            }
            for n in items
        ]
        return JsonResponse(
            {"unread": unread_count(request.user), "items": data}
        )
