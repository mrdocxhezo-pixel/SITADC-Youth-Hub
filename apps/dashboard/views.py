import re
from typing import cast

from django.contrib import messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from apps.accounts.models import User
from apps.rbac.authorization import user_has_any_permission

from .forms import DashboardPreferencesForm
from .models import (
    DashboardConfiguration,
    DashboardWidget,
    DashboardWidgetConfiguration,
    UserDashboardPreference,
)
from .services import (
    ACTIVITY_LOG_PAGE_SIZE,
    ACTIVITY_LOG_WINDOW,
    can_view_audit_activity,
    get_announcements,
    get_audit_activity,
    get_default_configuration,
    get_document_activity,
    get_my_drafts,
    get_notification_summary,
    get_org_context,
    get_overdue_list,
    get_pending_approvals,
    get_personalized_widgets,
    get_profile_summary,
    get_program_progress,
    get_project_status_summary,
    get_recent_activity,
    get_recent_notifications,
    get_refresh_interval,
    get_reports_due,
    get_upcoming_events,
    get_welcome_context,
    resolve_statistic_card,
    resolve_widget_payload,
    set_widget_state,
)

# Bootstrap column classes for the widget grid (column_span is 1-4).
SPAN_CLASSES = {
    1: "col-12 col-md-6 col-xl-3",
    2: "col-12 col-lg-6",
    3: "col-12 col-lg-8",
    4: "col-12",
}

# Widget types whose information is rendered once in the welcome hero.
HERO_WIDGET_TYPES = frozenset({"welcome", "profile", "organizational_info"})


def visible_widget_configs(
    dashboard_config: DashboardConfiguration,
) -> list[DashboardWidgetConfiguration]:
    """Visible, enabled widget configurations in display order."""
    configs = (
        DashboardWidgetConfiguration.objects.filter(
            dashboard_configuration=dashboard_config,
            is_visible=True,
            widget__is_enabled=True,
        )
        .select_related("widget")
        .order_by("position")
    )
    return list(configs)


def _reporting_period_choices() -> list[tuple[str, str]]:
    """Reporting period choices declared on the preference model."""
    field = UserDashboardPreference._meta.get_field("default_reporting_period")
    return cast(list[tuple[str, str]], field.choices or [])


def _resolve_period(request, user: User) -> str:
    """Persist the reporting-period filter selection to user preferences."""
    pref, _created = UserDashboardPreference.objects.get_or_create(user=user)
    requested = request.GET.get("period")
    valid_choices = {value for value, _label in _reporting_period_choices()}
    if requested in valid_choices:
        if pref.default_reporting_period != requested:
            pref.default_reporting_period = requested
            pref.save(update_fields=["default_reporting_period"])
        return requested
    return pref.default_reporting_period


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """Central command center: role-aware, permission-filtered home page."""

    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # LoginRequiredMixin guarantees an authenticated user here.
        user = cast(User, self.request.user)

        user_pref, _created = UserDashboardPreference.objects.get_or_create(user=user)
        current_period = _resolve_period(self.request, user)
        user_pref.default_reporting_period = current_period
        dashboard_config = get_default_configuration()
        configs = get_personalized_widgets(
            user, visible_widget_configs(dashboard_config)
        )

        stat_cards: list[dict] = []
        main_widgets: list[dict] = []
        for widget_config in configs:
            widget = widget_config.widget

            if widget.widget_type == "statistic":
                card = resolve_statistic_card(widget_config, user)
                if card is not None:
                    stat_cards.append(card)

            elif widget.widget_type in HERO_WIDGET_TYPES:
                continue

            else:
                main_widgets.append(
                    {
                        "id": widget_config.id,
                        "title": widget.title,
                        "widget_type": widget.widget_type,
                        "span_class": SPAN_CLASSES.get(
                            widget_config.column_span, "col-12"
                        ),
                        "payload": resolve_widget_payload(widget_config, user),
                    }
                )

        show_audit = can_view_audit_activity(user)
        context.update(
            {
                "user_pref": user_pref,
                "dashboard_config": dashboard_config,
                "welcome": get_welcome_context(user),
                "profile_summary": get_profile_summary(user),
                "org_context": get_org_context(user),
                "stat_cards": stat_cards,
                "main_widgets": main_widgets,
                "reports_due": get_reports_due(user),
                "my_drafts": get_my_drafts(user),
                "pending_approvals": (
                    get_pending_approvals(user)
                    if user_has_any_permission(user, ["reviews.view", "reviews.manage"])
                    else []
                ),
                "overdue_reports": get_overdue_list(user),
                "program_progress": (
                    get_program_progress()
                    if user_has_any_permission(
                        user, ["programmes.view", "programmes.manage"]
                    )
                    else []
                ),
                "project_status": (
                    get_project_status_summary()
                    if user_has_any_permission(
                        user, ["projects.view", "projects.manage", "programmes.view"]
                    )
                    else None
                ),
                "document_activity": (
                    get_document_activity(user)
                    if user_has_any_permission(
                        user, ["documents.view", "documents.manage"]
                    )
                    else None
                ),
                "audit_activity": get_audit_activity() if show_audit else None,
                "upcoming_events": (
                    get_upcoming_events(user)
                    if user_has_any_permission(
                        user, ["meetings.view", "calendars.view", "meetings.manage"]
                    )
                    else []
                ),
                "announcements": get_announcements(),
                "recent_notifications": get_recent_notifications(user),
                "notification_summary": get_notification_summary(user),
                "refresh_interval": get_refresh_interval(),
                "current_period": current_period,
                "current_period_label": dict(_reporting_period_choices()).get(
                    current_period
                ),
                "period_choices": _reporting_period_choices(),
            }
        )
        return context


class DashboardActivityLogView(LoginRequiredMixin, TemplateView):
    """Full activity feed backing the dashboard "Read more" link."""

    template_name = "dashboard/activity_log.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = cast(User, self.request.user)
        entries = get_recent_activity(
            user, limit=ACTIVITY_LOG_WINDOW, per_source=ACTIVITY_LOG_PAGE_SIZE
        )
        paginator = Paginator(entries, ACTIVITY_LOG_PAGE_SIZE)
        page = paginator.get_page(self.request.GET.get("page"))
        context["page_obj"] = page
        return context


@login_required
def dashboard_personalize_view(request):
    """Personalize widget visibility/order and dashboard preferences."""
    user = cast(User, request.user)
    pref, _created = UserDashboardPreference.objects.get_or_create(user=user)
    config = get_default_configuration()
    configs = visible_widget_configs(config)
    states = {state.widget_id: state for state in user.dashboard_widget_states.all()}

    if request.method == "POST":
        action = request.POST.get("action", "layout")

        if action == "preferences":
            form = DashboardPreferencesForm(request.POST, instance=pref)
            if form.is_valid():
                form.save()
                messages.success(request, "Dashboard preferences updated.")
            else:
                messages.error(request, "Please correct the highlighted errors.")
            return redirect("dashboard:personalize")

        if action == "reset":
            user.dashboard_widget_states.all().delete()
            messages.success(request, "Dashboard layout reset to default.")
            return redirect("dashboard:home")

        # Detect which widgets were rendered by scanning posted field names
        # like "widget_<id>_visible" / "widget_<id>_position". Unchecked
        # checkboxes are omitted by browsers, so presence must be inferred
        # from any sibling field.
        posted_widget_ids = {
            int(match.group(1))
            for key in request.POST
            if (match := re.match(r"^widget_(\d+)_", key))
        }
        config_by_widget_id = {
            widget_config.widget_id: widget_config for widget_config in configs
        }
        for widget_id in posted_widget_ids:
            widget_config = config_by_widget_id.get(widget_id)
            if widget_config is None:
                continue
            prefix = f"widget_{widget_id}"
            # Checkbox is labelled "Visible": checked means the widget stays.
            is_visible = request.POST.get(f"{prefix}_visible") == "on"
            raw_position = request.POST.get(f"{prefix}_position", "")
            position = int(raw_position) if raw_position.isdigit() else None
            set_widget_state(
                user,
                widget_id,
                is_hidden=not is_visible,
                position=position,
            )
        messages.success(request, "Dashboard layout saved.")
        return redirect("dashboard:home")

    preference_form = DashboardPreferencesForm(instance=pref)
    rows = [
        {
            "config": widget_config,
            "state": states.get(widget_config.widget_id),
        }
        for widget_config in configs
    ]
    return render(
        request,
        "dashboard/personalize.html",
        {"rows": rows, "preference_form": preference_form},
    )


@login_required
def dashboard_widget_data(request, widget_id: int):
    """AJAX endpoint returning resolved data for a single configured widget."""
    try:
        widget_config = DashboardWidgetConfiguration.objects.select_related(
            "widget"
        ).get(id=widget_id, is_visible=True)
    except DashboardWidgetConfiguration.DoesNotExist:
        return JsonResponse({"error": "Widget not found"}, status=404)

    payload = resolve_widget_payload(widget_config, cast(User, request.user))
    if not payload:
        return JsonResponse({"error": "No data available for this widget"}, status=404)
    return JsonResponse(payload)


@login_required
def dashboard_widget_config(request, config_type: str):
    """AJAX endpoint listing widget metadata for ``stats`` or ``main`` sections."""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    dashboard_config = get_default_configuration()
    widget_configs = visible_widget_configs(dashboard_config)

    if config_type == "stats":
        widget_configs = [
            wc for wc in widget_configs if wc.widget.widget_type == "statistic"
        ]
    elif config_type == "main":
        widget_configs = [
            wc for wc in widget_configs if wc.widget.widget_type != "statistic"
        ]

    widgets = []
    for widget_config in widget_configs:
        widget = widget_config.widget
        widgets.append(
            {
                "id": widget.id,
                "title": widget.title,
                "widget_type": widget.widget_type,
                "configuration": widget.configuration,
                "column_span": widget_config.column_span,
                "row_span": widget_config.row_span,
            }
        )

    return JsonResponse({"widgets": widgets})


class StaffAdminMixin(UserPassesTestMixin):
    """Only superusers may administer dashboard configuration."""

    request: HttpRequest
    login_url = reverse_lazy("core:login")

    def test_func(self) -> bool:
        user = self.request.user
        return bool(user.is_authenticated and user.is_superuser)


class DashboardConfigurationView(StaffAdminMixin, TemplateView):
    """Centralized dashboard configuration overview."""

    template_name = "dashboard/configuration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["configurations"] = DashboardConfiguration.objects.prefetch_related(
            "widget_configurations__widget"
        )
        return context


class DashboardWidgetManagementView(StaffAdminMixin, TemplateView):
    """Centrally manage widgets: enable/disable with audited changes."""

    template_name = "dashboard/widget_management.html"

    def post(self, request, *args, **kwargs):
        widget_id = request.POST.get("widget_id")
        enable = request.POST.get("enable") == "true"
        widget = DashboardWidget.objects.filter(id=widget_id).first()
        if widget is not None:
            widget.is_enabled = enable
            widget.save(update_fields=["is_enabled"])
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(widget).id,
                object_id=widget.id,
                object_repr=str(widget),
                action_flag=CHANGE,
                change_message=f"Widget {'enabled' if enable else 'disabled'} "
                "via dashboard widget management.",
            )
            state = "enabled" if enable else "disabled"
            messages.success(request, f"Widget '{widget.name}' {state}.")
        return redirect("dashboard:widget_management")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["widgets"] = DashboardWidget.objects.order_by("widget_type", "name")
        return context
