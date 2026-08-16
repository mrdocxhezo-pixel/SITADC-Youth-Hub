from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.rbac.authorization import (
    get_active_role_assignments,
    get_effective_scopes_for_user,
    user_has_any_permission,
    user_has_permission,
    user_has_scope,
)
from apps.report_instances.models import ReportStatus
from apps.report_instances.selectors import (
    get_all_reports,
    get_approved_reports,
    get_draft_reports,
    get_overdue_reports,
    get_reports_pending_review,
    get_submitted_reports,
)
from apps.volunteers.selectors import visible_volunteer_profiles

from .models import (
    DashboardConfiguration,
    DashboardWidget,
    DashboardWidgetConfiguration,
    UserDashboardPreference,
)


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """Main dashboard view that displays role-based dashboard."""

    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get or create user dashboard preference
        user_pref, created = UserDashboardPreference.objects.get_or_create(user=user)

        # Get dashboard configuration based on user role/permissions
        # For now, we'll use the default configuration
        try:
            dashboard_config = DashboardConfiguration.objects.get(is_default=True)
        except DashboardConfiguration.DoesNotExist:
            # Create a default configuration if none exists
            dashboard_config = DashboardConfiguration.objects.create(
                name="Default Dashboard", is_default=True
            )

        # Get widget configurations for this dashboard
        widget_configs = (
            DashboardWidgetConfiguration.objects.filter(
                dashboard_configuration=dashboard_config, is_visible=True
            )
            .select_related("widget")
            .order_by("position")
        )

        # Prepare widgets data for template
        widgets = []
        for widget_config in widget_configs:
            widget_data = {
                "id": widget_config.id,
                "widget": widget_config.widget,
                "position": widget_config.position,
                "column_span": widget_config.column_span,
                "row_span": widget_config.row_span,
                "configuration": widget_config.configuration,
                "is_visible": widget_config.is_visible,
            }
            widgets.append(widget_data)

        context.update(
            {
                "user_pref": user_pref,
                "dashboard_config": dashboard_config,
                "widgets": widgets,
            }
        )

        return context


@login_required
def dashboard_widget_data(request, widget_id):
    """AJAX endpoint to get data for a specific widget."""
    try:
        widget_config = DashboardWidgetConfiguration.objects.get(
            id=widget_id, is_visible=True
        )
    except DashboardWidgetConfiguration.DoesNotExist:
        return JsonResponse({"error": "Widget not found"}, status=404)

    widget = widget_config.widget
    user = request.user

    # Get data based on widget type
    data = {}

    if widget.widget_type == "statistic":
        data = get_statistic_data(widget, user, widget_config.configuration)
    elif widget.widget_type == "chart":
        data = get_chart_data(widget, user, widget_config.configuration)
    elif widget.widget_type == "table":
        data = get_table_data(widget, user, widget_config.configuration)
    elif widget.widget_type == "list":
        data = get_list_data(widget, user, widget_config.configuration)
    elif widget.widget_type == "activity":
        data = get_activity_data(widget, user, widget_config.configuration)
    elif widget.widget_type == "notification":
        data = get_notification_data(widget, user, widget_config.configuration)
    elif widget.widget_type == "quick_actions":
        data = get_quick_actions_data(widget, user, widget_config.configuration)
    elif widget.widget_type == "welcome":
        data = get_welcome_data(widget, user, widget_config.configuration)
    elif widget.widget_type == "profile":
        data = get_profile_data(widget, user, widget_config.configuration)
    elif widget.widget_type == "organizational_info":
        data = get_organizational_info_data(widget, user, widget_config.configuration)

    return JsonResponse(data)


def get_statistic_data(widget, user, config):
    """Get data for statistic widget."""
    widget_type = widget.widget_type
    widget_title = widget.title

    if widget_type == "statistic":
        # Determine which statistic to show based on widget title
        title_lower = widget_title.lower()

        if "report" in title_lower and "submitted" in title_lower:
            # Reports submitted
            reports = get_submitted_reports(user).count()
            return {
                "title": widget_title,
                "value": str(reports),
                "trend": "neutral",
                "percentage": 0,
            }
        elif "report" in title_lower and "due" in title_lower:
            # Reports due
            reports = get_overdue_reports().count()
            # Count reports due soon (within 7 days)
            from datetime import timedelta

            from apps.report_instances.models import Report

            today = timezone.now().date()
            soon = today + timedelta(days=7)
            reports_due_soon = Report.objects.filter(
                due_date__gte=today,
                due_date__lt=soon,
                status__in={
                    ReportStatus.DRAFT,
                    ReportStatus.IN_PROGRESS,
                    ReportStatus.SUBMITTED,
                    ReportStatus.UNDER_REVIEW,
                    ReportStatus.RETURNED_FOR_CORRECTION,
                },
                is_deleted=False,
            ).count()
            total = reports + reports_due_soon
            return {
                "title": widget_title,
                "value": str(total),
                "trend": "neutral" if total == 0 else "info",
                "percentage": 0,
            }
        elif "report" in title_lower and "draft" in title_lower:
            # Draft reports
            reports = get_draft_reports(user).count()
            return {
                "title": widget_title,
                "value": str(reports),
                "trend": "neutral",
                "percentage": 0,
            }
        elif (
            "report" in title_lower
            and "pending" in title_lower
            and "review" in title_lower
        ):
            # Reports pending review
            reports = get_reports_pending_review(user).count()
            return {
                "title": widget_title,
                "value": str(reports),
                "trend": "neutral",
                "percentage": 0,
            }
        elif "report" in title_lower and "approved" in title_lower:
            # Approved reports
            reports = get_approved_reports(user).count()
            return {
                "title": widget_title,
                "value": str(reports),
                "trend": "up" if reports > 0 else "neutral",
                "percentage": 0,
            }
        elif "report" in title_lower and "overdue" in title_lower:
            # Overdue reports
            reports = get_overdue_reports().count()
            return {
                "title": widget_title,
                "value": str(reports),
                "trend": "down" if reports > 0 else "neutral",
                "percentage": 0,
            }
        elif "active" in title_lower and "volunteer" in title_lower:
            # Active volunteers
            if user_is_superuser_or_manager(user):
                profiles = visible_volunteer_profiles(user)
                count = profiles.count()
            else:
                # Count only volunteers assigned to user's scope
                profiles = visible_volunteer_profiles(user)
                count = profiles.count()
            return {
                "title": widget_title,
                "value": str(count),
                "trend": "up" if count > 0 else "neutral",
                "percentage": 0,
            }
        elif "active" in title_lower and "member" in title_lower:
            # Active members - we'll need to check the memberships app
            # For now, return 0 with note
            return {
                "title": widget_title,
                "value": "0",
                "trend": "neutral",
                "percentage": 0,
            }
        else:
            # Default statistic
            return {
                "title": widget_title,
                "value": "--",
                "trend": "neutral",
                "percentage": 0,
            }

    return {
        "title": widget_title,
        "value": "--",
        "trend": "neutral",
        "percentage": 0,
    }


def user_is_superuser_or_manager(user):
    """Check if user is superuser or has manager role."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    # Check if user has a role that includes management permissions
    role_assignments = get_active_role_assignments(user)
    if role_assignments.exists():
        for _assignment in role_assignments:
            # Check for management-related permissions
            if user_has_permission(user, "management.view") or user_has_permission(
                user, "staff.manage"
            ):
                return True
    return False


def get_chart_data(widget, user, config):
    """Get data for chart widget."""
    widget_type = widget.widget_type
    widget_title = widget.title

    if widget_type == "chart":
        title_lower = widget_title.lower()

        if "report status" in title_lower or "report status chart" in title_lower:
            # Chart showing report status distribution
            from apps.report_instances.constants import ReportStatus

            # Get reports visible to user
            reports = get_all_reports()
            if (
                user is not None
                and not user.is_superuser
                and not user_has_permission(user, "reports.view")
            ):
                reports = reports.none()

            # Count reports by status
            status_data = {}
            for status_code, status_name in ReportStatus.choices:
                count = reports.filter(status=status_code).count()
                if count > 0:
                    status_data[status_name] = count

            labels = list(status_data.keys())
            data = list(status_data.values())

            return {
                "title": widget_title,
                "labels": labels,
                "datasets": [
                    {
                        "label": "Reports",
                        "data": data,
                        "backgroundColor": [
                            "#4e73df",
                            "#1cc88a",
                            "#36b9cc",
                            "#f6c23e",
                            "#e74a3b",
                            "#858796",
                        ][: len(labels)],
                    }
                ],
            }

        elif "volunteer" in title_lower and "status" in title_lower:
            # Chart showing volunteer status distribution
            if user_is_superuser_or_manager(user):
                profiles = visible_volunteer_profiles(user)
            else:
                profiles = visible_volunteer_profiles(user)

            # Count by status
            from apps.volunteers.models import VolunteerStatus

            status_data = {}
            for status_code, status_name in VolunteerStatus.choices:
                count = profiles.filter(status=status_code).count()
                if count > 0:
                    status_data[status_name] = count

            labels = list(status_data.keys())
            data = list(status_data.values())

            return {
                "title": widget_title,
                "labels": labels,
                "datasets": [
                    {
                        "label": "Volunteers",
                        "data": data,
                        "backgroundColor": [
                            "#4e73df",
                            "#1cc88a",
                            "#36b9cc",
                            "#f6c23e",
                            "#e74a3b",
                            "#858796",
                        ][: len(labels)],
                    }
                ],
            }

        elif "program" in title_lower or "project" in title_lower:
            # Chart showing program/project progress
            # We'll use a simple placeholder for now
            # In a full implementation, this would query the programs/projects apps
            labels = ["Active", "Completed", "Delayed"]
            data = [5, 3, 2]  # Placeholder values

            return {
                "title": widget_title,
                "labels": labels,
                "datasets": [
                    {
                        "label": "Progress",
                        "data": data,
                        "backgroundColor": ["#1cc88a", "#36b9cc", "#f6c23e"],
                    }
                ],
            }

        else:
            # Default chart
            return {
                "title": widget_title,
                "labels": [],
                "datasets": [],
            }

    return {
        "title": widget_title,
        "labels": [],
        "datasets": [],
    }


def get_table_data(widget, user, config):
    """Get data for table widget."""
    widget_type = widget.widget_type
    widget_title = widget.title

    if widget_type == "table":
        title_lower = widget_title.lower()

        if (
            "report" in title_lower
            and "pending" in title_lower
            and "review" in title_lower
        ):
            # Reports pending review table
            from apps.report_instances.selectors import get_reports_pending_review

            reports = get_reports_pending_review(user)

            # Get limited fields for display
            rows = []
            for report in reports[:10]:  # Limit to 10 for table
                rows.append(
                    {
                        "title": report.title,
                        "submitted_by": (
                            report.owner.get_full_name() if report.owner else "Unknown"
                        ),
                        "submitted_date": (
                            str(report.submitted_at)[:10]
                            if report.submitted_at
                            else "N/A"
                        ),
                        "category": report.category.name if report.category else "N/A",
                        "status": report.status,
                        "deadline": str(report.due_date) if report.due_date else "N/A",
                    }
                )

            return {
                "title": widget_title,
                "headers": [
                    "Report Title",
                    "Submitted By",
                    "Date",
                    "Category",
                    "Status",
                    "Deadline",
                ],
                "rows": rows,
            }

        elif "report" in title_lower and "approved" in title_lower:
            # Approved reports table
            from apps.report_instances.selectors import get_approved_reports

            reports = get_approved_reports(user)

            rows = []
            for report in reports[:10]:
                rows.append(
                    {
                        "title": report.title,
                        "submitted_by": (
                            report.owner.get_full_name() if report.owner else "Unknown"
                        ),
                        "submitted_date": (
                            str(report.submitted_at)[:10]
                            if report.submitted_at
                            else "N/A"
                        ),
                        "category": report.category.name if report.category else "N/A",
                        "status": report.status,
                        "approved_date": (
                            str(report.approved_at)[:10]
                            if report.approved_at
                            else "N/A"
                        ),
                    }
                )

            return {
                "title": widget_title,
                "headers": [
                    "Report Title",
                    "Submitted By",
                    "Date",
                    "Category",
                    "Status",
                    "Approved Date",
                ],
                "rows": rows,
            }

        elif "overdue" in title_lower:
            # Overdue reports table
            from django.utils import timezone

            from apps.report_instances.selectors import get_overdue_reports

            reports = get_overdue_reports()

            rows = []
            for report in reports[:10]:
                # Calculate days overdue
                days_overdue = 0
                if report.due_date:
                    today = timezone.now().date()
                    if report.due_date < today:
                        days_overdue = (today - report.due_date).days

                rows.append(
                    {
                        "title": report.title,
                        "submitted_by": (
                            report.owner.get_full_name() if report.owner else "Unknown"
                        ),
                        "due_date": str(report.due_date) if report.due_date else "N/A",
                        "days_overdue": days_overdue,
                        "priority": (
                            report.category.color if report.category else "#e74a3b"
                        ),
                        "status": report.status,
                    }
                )

            return {
                "title": widget_title,
                "headers": [
                    "Report Title",
                    "Submitted By",
                    "Due Date",
                    "Days Overdue",
                    "Priority",
                    "Status",
                ],
                "rows": rows,
            }

        elif "volunteer" in title_lower:
            # Volunteer profiles table
            if user_is_superuser_or_manager(user):
                profiles = visible_volunteer_profiles(user)
            else:
                profiles = visible_volunteer_profiles(user)

            rows = []
            for profile in profiles[:10]:
                rows.append(
                    {
                        "full_name": (
                            profile.user.get_full_name() if profile.user else "Unknown"
                        ),
                        "reference_number": profile.reference_number,
                        "status": profile.status,
                        "team": profile.team.name if profile.team else "N/A",
                        "region": profile.region or "N/A",
                        "email": profile.user.email if profile.user else "N/A",
                    }
                )

            return {
                "title": widget_title,
                "headers": [
                    "Full Name",
                    "Reference Number",
                    "Status",
                    "Team",
                    "Region",
                    "Email",
                ],
                "rows": rows,
            }

        else:
            # Default table
            return {
                "title": widget_title,
                "headers": [],
                "rows": [],
            }

    return {
        "title": widget_title,
        "headers": [],
        "rows": [],
    }


def get_list_data(widget, user, config):
    """Get data for list widget."""
    widget_type = widget.widget_type
    widget_title = widget.title

    if widget_type == "list":
        title_lower = widget_title.lower()

        if "recent" in title_lower and "report" in title_lower:
            # Recent reports list
            from apps.report_instances.selectors import get_submitted_reports

            reports = get_submitted_reports(user)[:10]

            items = []
            for report in reports:
                items.append(
                    {
                        "title": report.title,
                        "status": report.status,
                        "submitted": (
                            str(report.submitted_at)[:16]
                            if report.submitted_at
                            else "N/A"
                        ),
                        "category": report.category.name if report.category else "N/A",
                        "link": f"/reports/{report.reference_number}/",
                    }
                )

            return {
                "title": widget_title,
                "items": items,
            }

        elif "recent" in title_lower and "volunteer" in title_lower:
            # Recent volunteer activity
            if user_is_superuser_or_manager(user):
                profiles = visible_volunteer_profiles(user)
            else:
                profiles = visible_volunteer_profiles(user)

            # Get recent activity from activity logs

            from apps.volunteers.models import VolunteerActivityLog

            activity = (
                VolunteerActivityLog.objects.filter(profile__in=profiles)
                .select_related("profile__user")
                .order_by("-activity_date")[:10]
            )

            items = []
            for log in activity:
                items.append(
                    {
                        "title": log.activity_title,
                        "date": str(log.activity_date),
                        "hours": str(log.hours_served) if log.hours_served else "0",
                        "beneficiaries": log.beneficiaries_reached,
                    }
                )

            return {
                "title": widget_title,
                "items": items,
            }

        elif "notification" in title_lower:
            # Notifications list - will be handled separately
            return {
                "title": widget_title,
                "items": [],
            }

        else:
            # Default list
            return {
                "title": widget_title,
                "items": [],
            }

    return {
        "title": widget_title,
        "items": [],
    }


def get_activity_data(widget, user, config):
    """Get data for activity feed widget."""
    widget_type = widget.widget_type
    widget_title = widget.title

    if widget_type == "activity":
        title_lower = widget_title.lower()

        if "organizational" in title_lower or "recent" in title_lower:
            # Recent organizational activity

            # Get recent reports submissions
            from apps.report_instances.selectors import get_submitted_reports

            # Get recent submitted reports
            reports = get_submitted_reports(user)[:5]

            activities = []

            for report in reports:
                submitter_name = (
                    report.owner.get_full_name() if report.owner else "Unknown"
                )
                activities.append(
                    {
                        "title": f"Report submitted: {report.title}",
                        "description": f"Submitted by {submitter_name}",
                        "time": (
                            str(report.submitted_at)[:16]
                            if report.submitted_at
                            else "Just now"
                        ),
                        "icon": "bi bi-file-text",
                        "link": f"/reports/{report.reference_number}/",
                    }
                )

            # Get recent approvals
            from apps.report_instances.selectors import get_approved_reports

            approved_reports = get_approved_reports(user)[:3]

            for report in approved_reports:
                activities.append(
                    {
                        "title": f"Report approved: {report.title}",
                        "description": (
                            f"Approved by "
                            f'{getattr(user, "get_full_name", lambda: "")()}'
                        ),
                        "time": (
                            str(report.approved_at)[:16]
                            if report.approved_at
                            else "Just now"
                        ),
                        "icon": "bi bi-check-circle",
                        "link": f"/reports/{report.reference_number}/",
                    }
                )

            # Get recent volunteer activity if user has permission
            if user_is_superuser_or_manager(user):
                from apps.volunteers.models import VolunteerActivityLog
                from apps.volunteers.selectors import visible_volunteer_profiles

                profiles = visible_volunteer_profiles(user)
                recent_activity = (
                    VolunteerActivityLog.objects.filter(profile__in=profiles)
                    .select_related("profile__user")
                    .order_by("-activity_date")[:3]
                )

                for log in recent_activity:
                    activities.append(
                        {
                            "title": f"Volunteer activity: {log.activity_title}",
                            "description": (
                                f"{log.hours_served}h served, "
                                f"{log.beneficiaries_reached} beneficiaries"
                            ),
                            "time": str(log.activity_date),
                            "icon": "bi bi-person-workspace",
                        }
                    )

            return {
                "title": widget_title,
                "activities": activities,
            }

        else:
            # Default activity feed
            return {
                "title": widget_title,
                "activities": [],
            }

    return {
        "title": widget_title,
        "activities": [],
    }


def get_notification_data(widget, user, config):
    """Get data for notification widget."""
    widget_type = widget.widget_type
    widget_title = widget.title

    if widget_type == "notification":
        from django.core.cache import cache

        # Try to get unread count from cache or compute it
        cache_key = (
            f"notifications_unread_{user.id}"
            if user
            else "notifications_unread_anonymous"
        )
        unread_count = cache.get(cache_key)

        if unread_count is None:
            # Compute unread count from various sources
            unread_count = 0

            # Check for report-related notifications

            from apps.notifications.models import Notification

            if user and user.is_authenticated:
                # Get unread notifications for this user
                notifications = Notification.objects.filter(
                    recipient=user, is_read=False
                )
                unread_count = notifications.count()

            # Cache for 1 minute
            cache.set(cache_key, unread_count, 60)

        # Get recent read notifications (limit to 5)
        notifications = []
        if user and user.is_authenticated:
            recent_notifications = (
                Notification.objects.filter(recipient=user)
                .select_related("actor", "target_content_type")
                .order("-created_at")[:5]
            )

            for notif in recent_notifications:
                notifications.append(
                    {
                        "title": notif.title,
                        "message": notif.message,
                        "time": str(notif.created_at)[:16],
                        "action_url": (
                            notif.get_absolute_url()
                            if hasattr(notif, "get_absolute_url")
                            else "/notifications/"
                        ),
                        "icon": "bi bi-bell",
                        "id": str(notif.id),
                    }
                )

        return {
            "title": widget_title,
            "notifications": notifications,
            "unread_count": unread_count,
        }

    return {
        "title": widget_title,
        "notifications": [],
        "unread_count": 0,
    }


def get_quick_actions_data(widget, user, config):
    """Get data for quick actions widget."""
    widget_type = widget.widget_type
    widget_title = widget.title

    if widget_type == "quick_actions":
        actions = []

        if not user or not user.is_authenticated:
            return {
                "title": widget_title,
                "actions": actions,
            }

        # Add actions based on user permissions
        # Report-related actions
        if user_has_permission(user, "reports.create") or user_has_permission(
            user, "reports.draft"
        ):
            actions.append(
                {
                    "label": "Create Report",
                    "handler": 'window.location.href = "/reports/create/";',
                }
            )

        if user_has_permission(user, "reports.submit"):
            actions.append(
                {
                    "label": "Submit Report",
                    "handler": 'window.location.href = "/reports/submit/";',
                }
            )

        if user_has_any_permission(user, ["reports.review", "reports.approve"]):
            actions.append(
                {
                    "label": "Review Reports",
                    "handler": 'window.location.href = "/reviews/";',
                }
            )

        if user_has_permission(user, "documents.upload"):
            actions.append(
                {
                    "label": "Upload Document",
                    "handler": 'window.location.href = "/documents/upload/";',
                }
            )

        if user_has_permission(user, "meals.indicator.view") or user_has_permission(
            user, "meal.report"
        ):
            actions.append(
                {
                    "label": "View MEAL Indicators",
                    "handler": 'window.location.href = "/meal/";',
                }
            )

        if user_has_permission(user, "finance.view") or user_has_permission(
            user, "finance.report"
        ):
            actions.append(
                {
                    "label": "View Finance",
                    "handler": 'window.location.href = "/finance/";',
                }
            )

        if user_has_permission(user, "partners.view") or user_has_permission(
            user, "partners.manage"
        ):
            actions.append(
                {
                    "label": "Manage Partners",
                    "handler": 'window.location.href = "/partners/";',
                }
            )

        if user_has_permission(user, "stakeholders.view"):
            actions.append(
                {
                    "label": "View Stakeholders",
                    "handler": 'window.location.href = "/stakeholders/";',
                }
            )

        # User-specific actions
        if user_is_superuser_or_manager(user):
            actions.append(
                {
                    "label": "Admin Dashboard",
                    "handler": 'window.location.href = "/admin/dashboard/";',
                }
            )

        # Always allow profile and notifications
        actions.append(
            {
                "label": "View Profile",
                "handler": 'window.location.href = "/accounts/profile/";',
            }
        )
        actions.append(
            {
                "label": "View Notifications",
                "handler": 'window.location.href = "/notifications/";',
            }
        )

        # Sort actions: role-specific first, then general
        role_specific = [
            a
            for a in actions
            if any(
                kw in a["label"].lower()
                for kw in ["create", "review", "admin", "manage"]
            )
        ]
        general = [a for a in actions if a not in role_specific]
        actions = role_specific + general

        return {
            "title": widget_title,
            "actions": actions,
        }

    return {
        "title": widget_title,
        "actions": [],
    }


def get_welcome_data(widget, user, config):
    """Get data for welcome widget."""
    return {
        "title": widget.title,
        "message": f"Welcome back, {user.get_full_name() or user.username}!",
        "user": {
            "username": user.username,
            "full_name": user.get_full_name(),
        },
        "date": "Today",
    }


def get_profile_data(widget, user, config):
    """Get data for profile widget."""
    if not user or not user.is_authenticated:
        return {
            "title": widget.title,
            "user": {
                "username": "Guest",
                "full_name": "Guest",
                "email": "",
            },
        }

    # Get user's profile photo if available
    profile_photo = None
    try:
        # Try to get profile photograph from user profile
        profile_photo = (
            getattr(user, "profile_photo", None)
            or getattr(user, "volunteer_profile", None).profile_photo
            if hasattr(user, "volunteer_profile")
            else None
        )
    except (AttributeError, TypeError):
        profile_photo = None

    return {
        "title": widget.title,
        "user": {
            "username": user.username,
            "full_name": user.get_full_name(),
            "email": user.email,
            "profile_photo": profile_photo,
            "user_id": user.id,
        },
    }


def get_organizational_info_data(widget, user, config):
    """Get data for organizational info widget."""
    if not user or not user.is_authenticated:
        return {
            "title": widget.title,
            "organizational_unit": "--",
            "position": "--",
            "directorate": "--",
        }

    # Get organizational information based on user's active role assignments
    organizational_unit = "--"
    position = "--"
    directorate = "--"

    # Get active role assignments
    role_assignments = get_active_role_assignments(user)

    if role_assignments.exists():
        for _assignment in role_assignments:
            role = _assignment.role
            access_scope = _assignment.access_scope

            # Get organizational unit from scope
            if access_scope:
                organizational_unit = access_scope.name or access_scope.code or "--"

            # Get position from role
            if role:
                position = role.name or "--"

                # Check for directorate-related information
                if user_has_scope(user, "directorate") or user_has_scope(
                    user, "region"
                ):
                    # Get the highest level scope
                    scopes = get_effective_scopes_for_user(user)
                    if scopes:
                        directorate = scopes[0].name or "--"

    # Fallback: try to get from user's profile if available
    if not position or position == "--":
        try:
            # Try to get position from various profile models
            if hasattr(user, "volunteer_profile"):
                position = user.volunteer_profile.position or position
            if hasattr(user, "leader_profile"):
                position = user.leader_profile.position or position
        except (AttributeError, TypeError):
            pass

    return {
        "title": widget.title,
        "organizational_unit": organizational_unit,
        "position": position,
        "directorate": directorate,
    }


class DashboardConfigurationView(LoginRequiredMixin, TemplateView):
    """View for managing dashboard configuration."""

    template_name = "dashboard/configuration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["configurations"] = DashboardConfiguration.objects.all()
        return context


class DashboardWidgetManagementView(LoginRequiredMixin, TemplateView):
    """View for managing dashboard widgets."""

    template_name = "dashboard/widget_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["widgets"] = DashboardWidget.objects.all()
        return context


# AJAX endpoints for widget configuration
@login_required
def dashboard_widget_config(request, config_type):
    """Get widget configuration for stats row or main content."""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = request.user

    # Get or create user dashboard preference
    user_pref, created = UserDashboardPreference.objects.get_or_create(user=user)

    # Get dashboard configuration based on user role/permissions
    try:
        dashboard_config = DashboardConfiguration.objects.get(is_default=True)
    except DashboardConfiguration.DoesNotExist:
        # Create a default configuration if none exists
        dashboard_config = DashboardConfiguration.objects.create(
            name="Default Dashboard", is_default=True
        )

    # Get widget configurations for this dashboard
    widget_configs = (
        DashboardWidgetConfiguration.objects.filter(
            dashboard_configuration=dashboard_config, is_visible=True
        )
        .select_related("widget")
        .order_by("position")
    )

    # Filter widgets based on config_type
    if config_type == "stats":
        # For stats row, we want statistic widgets
        widget_configs = widget_configs.filter(widget__widget_type="statistic")
    elif config_type == "main":
        # For main content, we want everything except statistics (for now)
        widget_configs = widget_configs.exclude(widget__widget_type="statistic")

    # Prepare widgets data
    widgets = []
    for widget_config in widget_configs:
        widget_data = {
            "id": widget_config.widget.id,
            "title": widget_config.widget.title,
            "widget_type": widget_config.widget.widget_type,
            "icon": getattr(widget_config.widget, "icon", None),
            "column_span": widget_config.column_span,
            "row_span": widget_config.row_span,
            "configuration": widget_config.configuration,
        }
        widgets.append(widget_data)

    return JsonResponse({"widgets": widgets})
