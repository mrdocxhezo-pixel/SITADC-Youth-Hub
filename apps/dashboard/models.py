from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import models


class DashboardConfiguration(models.Model):
    """Global dashboard configuration."""

    name = models.CharField(max_length=100, unique=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dashboard Configuration"
        verbose_name_plural = "Dashboard Configurations"

    def __str__(self):
        return self.name


class DashboardWidget(models.Model):
    """Reusable dashboard widget."""

    WIDGET_TYPES: ClassVar[list[tuple[str, str]]] = [
        ("statistic", "Statistic"),
        ("chart", "Chart"),
        ("table", "Table"),
        ("list", "List"),
        ("calendar", "Calendar"),
        ("activity", "Activity Feed"),
        ("notification", "Notification"),
        ("quick_actions", "Quick Actions"),
        ("welcome", "Welcome"),
        ("profile", "Profile"),
        ("organizational_info", "Organizational Info"),
    ]

    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_enabled = models.BooleanField(default=True)
    refresh_interval = models.PositiveIntegerField(
        default=300,
        help_text="Refresh interval in seconds",  # 5 minutes in seconds
    )
    configuration = models.JSONField(
        default=dict, blank=True, help_text="Widget-specific configuration"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dashboard Widget"
        verbose_name_plural = "Dashboard Widgets"

    def __str__(self):
        return f"{self.name} ({self.get_widget_type_display()})"


class UserDashboardPreference(models.Model):
    """User-specific dashboard preferences."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard_preference",
    )
    theme = models.CharField(
        max_length=20,
        choices=[
            ("light", "Light"),
            ("dark", "Dark"),
        ],
        default="light",
    )
    default_reporting_period = models.CharField(
        max_length=20,
        choices=[
            ("today", "Today"),
            ("this_week", "This Week"),
            ("this_month", "This Month"),
            ("this_quarter", "This Quarter"),
            ("this_year", "This Year"),
        ],
        default="this_month",
    )
    preferred_chart_style = models.CharField(
        max_length=20,
        choices=[
            ("bar", "Bar"),
            ("line", "Line"),
            ("pie", "Pie"),
            ("doughnut", "Doughnut"),
        ],
        default="bar",
    )
    column_layout = models.PositiveSmallIntegerField(
        default=3, help_text="Number of columns in dashboard layout (1-4)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Dashboard Preference"
        verbose_name_plural = "User Dashboard Preferences"

    def __str__(self):
        return f"{self.user.username}'s Dashboard Preference"


class DashboardWidgetConfiguration(models.Model):
    """Configuration of widgets on a specific dashboard."""

    dashboard_configuration = models.ForeignKey(
        DashboardConfiguration,
        on_delete=models.CASCADE,
        related_name="widget_configurations",
    )
    widget = models.ForeignKey(DashboardWidget, on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(
        help_text="Position in dashboard layout (0-based index)"
    )
    column_span = models.PositiveSmallIntegerField(
        default=1, help_text="Number of columns this widget spans (1-4)"
    )
    row_span = models.PositiveSmallIntegerField(
        default=1, help_text="Number of rows this widget spans (1-4)"
    )
    is_visible = models.BooleanField(default=True)
    configuration = models.JSONField(
        default=dict, blank=True, help_text="Instance-specific widget configuration"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dashboard Widget Configuration"
        verbose_name_plural = "Dashboard Widget Configurations"
        unique_together: ClassVar[list[str]] = [
            "dashboard_configuration",
            "widget",
            "position",
        ]
        ordering: ClassVar[list[str]] = ["position"]

    def __str__(self):
        return f"{self.dashboard_configuration.name} - {self.widget.name}"


class UserWidgetState(models.Model):
    """Per-user personalization of a dashboard widget.

    Personalization only affects presentation (visibility and ordering)
    for the owning user; permissions and the organizational default
    layout remain authoritative.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard_widget_states",
    )
    widget = models.ForeignKey(DashboardWidget, on_delete=models.CASCADE)
    is_hidden = models.BooleanField(default=False)
    position = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="User-specific position override (0-based index)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Widget State"
        verbose_name_plural = "User Widget States"
        unique_together: ClassVar[list[str]] = ["user", "widget"]
        ordering: ClassVar[list[str]] = ["position"]

    def __str__(self):
        return f"{self.user.username} - {self.widget.name}"
