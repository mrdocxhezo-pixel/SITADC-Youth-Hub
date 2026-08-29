from django.db import migrations

WIDGETS = [
    {
        "name": "Welcome Widget",
        "widget_type": "welcome",
        "title": "Welcome",
        "description": "Welcome message for the user",
        "configuration": {},
    },
    {
        "name": "Profile Widget",
        "widget_type": "profile",
        "title": "Profile",
        "description": "User profile information",
        "configuration": {},
    },
    {
        "name": "Organizational Info Widget",
        "widget_type": "organizational_info",
        "title": "Organizational Info",
        "description": "User's organizational information",
        "configuration": {},
    },
    # Statistic widgets. ``stat_key`` ties each widget to its resolver in
    # apps.dashboard.services; permissions/icon/url drive rendering.
    {
        "name": "Members Statistic",
        "widget_type": "statistic",
        "title": "Active Members",
        "description": "Number of active members",
        "configuration": {
            "stat_key": "active_members",
            "icon": "bi-person-badge",
            "url_name": "memberships:dashboard",
            "permissions": [],
        },
    },
    {
        "name": "Volunteers Statistic",
        "widget_type": "statistic",
        "title": "Active Volunteers",
        "description": "Number of active volunteers",
        "configuration": {
            "stat_key": "active_volunteers",
            "icon": "bi-heart",
            "url_name": "volunteers:dashboard",
            "permissions": [],
        },
    },
    {
        "name": "Programs Statistic",
        "widget_type": "statistic",
        "title": "Active Programs",
        "description": "Number of active programs",
        "configuration": {
            "stat_key": "active_programs",
            "icon": "bi-kanban",
            "url_name": "programs:dashboard",
            "permissions": ["programmes.view", "programmes.manage"],
        },
    },
    {
        "name": "Projects Statistic",
        "widget_type": "statistic",
        "title": "Active Projects",
        "description": "Number of projects in delivery phases",
        "configuration": {
            "stat_key": "active_projects",
            "icon": "bi-diagram-3",
            "url_name": "programs:dashboard",
            "permissions": [
                "projects.view",
                "projects.manage",
                "programmes.view",
                "programmes.manage",
            ],
        },
    },
    {
        "name": "Beneficiaries Statistic",
        "widget_type": "statistic",
        "title": "Beneficiaries",
        "description": "Number of active beneficiaries",
        "configuration": {
            "stat_key": "beneficiaries",
            "icon": "bi-people",
            "url_name": "beneficiaries:dashboard",
            "permissions": ["beneficiaries.view", "beneficiaries.manage"],
        },
    },
    {
        "name": "Stakeholders Statistic",
        "widget_type": "statistic",
        "title": "Stakeholders",
        "description": "Number of active stakeholders",
        "configuration": {
            "stat_key": "stakeholders",
            "icon": "bi-building-gear",
            "url_name": "stakeholders:dashboard",
            "permissions": [
                "partners.view",
                "partners.view_directory",
                "partners.manage",
            ],
        },
    },
    {
        "name": "Pending Reviews Statistic",
        "widget_type": "statistic",
        "title": "Pending Reviews",
        "description": "Reports awaiting review",
        "configuration": {
            "stat_key": "reports_pending_review",
            "icon": "bi-check2-square",
            "url_name": "reviews:dashboard",
            "permissions": ["reviews.view", "reviews.manage"],
        },
    },
    {
        "name": "Overdue Reports Statistic",
        "widget_type": "statistic",
        "title": "Overdue Reports",
        "description": "Reports past their due date",
        "configuration": {
            "stat_key": "overdue_reports",
            "icon": "bi-exclamation-triangle",
            "url_name": "report_instances:dashboard",
            "permissions": [],
        },
    },
    {
        "name": "Upcoming Meetings Statistic",
        "widget_type": "statistic",
        "title": "Meetings (7 Days)",
        "description": "Meetings scheduled within the next seven days",
        "configuration": {
            "stat_key": "upcoming_meetings",
            "icon": "bi-calendar3",
            "url_name": "meetings:dashboard",
            "permissions": ["meetings.view", "calendars.view", "meetings.manage"],
        },
    },
    {
        "name": "Documents Statistic",
        "widget_type": "statistic",
        "title": "Documents",
        "description": "Registered documents",
        "configuration": {
            "stat_key": "documents",
            "icon": "bi-folder2-open",
            "url_name": "documents:dashboard",
            "permissions": ["documents.view", "documents.manage"],
        },
    },
    {
        "name": "Quick Actions Widget",
        "widget_type": "quick_actions",
        "title": "Quick Actions",
        "description": "Commonly used actions",
        "configuration": {},
    },
    {
        "name": "Notifications Widget",
        "widget_type": "notification",
        "title": "Notifications",
        "description": "Notification summary for the current user",
        "configuration": {},
    },
    {
        "name": "Activity Feed Widget",
        "widget_type": "activity",
        "title": "Recent Activity",
        "description": "Recent organizational activities",
        "configuration": {},
    },
]

# Default home layout: statistics first (span 1 = one card column),
# then quick actions, notifications and the activity feed.
LAYOUT = [
    ("Members Statistic", 0, 1, True),
    ("Volunteers Statistic", 1, 1, True),
    ("Programs Statistic", 2, 1, True),
    ("Projects Statistic", 3, 1, True),
    ("Beneficiaries Statistic", 4, 1, True),
    ("Stakeholders Statistic", 5, 1, True),
    ("Pending Reviews Statistic", 6, 1, True),
    ("Overdue Reports Statistic", 7, 1, True),
    ("Upcoming Meetings Statistic", 8, 1, True),
    ("Documents Statistic", 9, 1, True),
    ("Quick Actions Widget", 10, 2, True),
    ("Notifications Widget", 11, 2, True),
    ("Activity Feed Widget", 12, 4, True),
]


def create_initial_data(apps, schema_editor):
    DashboardConfiguration = apps.get_model("dashboard", "DashboardConfiguration")
    DashboardWidget = apps.get_model("dashboard", "DashboardWidget")
    DashboardWidgetConfiguration = apps.get_model(
        "dashboard", "DashboardWidgetConfiguration"
    )

    default_config, _ = DashboardConfiguration.objects.get_or_create(
        name="Default Dashboard", defaults={"is_default": True}
    )
    if not default_config.is_default:
        default_config.is_default = True
        default_config.save(update_fields=["is_default"])

    widgets_by_name = {}
    for widget_data in WIDGETS:
        widget, _ = DashboardWidget.objects.update_or_create(
            name=widget_data["name"],
            defaults={
                "widget_type": widget_data["widget_type"],
                "title": widget_data["title"],
                "description": widget_data["description"],
                "is_enabled": True,
                "configuration": widget_data["configuration"],
            },
        )
        widgets_by_name[widget.name] = widget

    for name, position, column_span, is_visible in LAYOUT:
        # unique_together includes position; clear stale rows for these
        # widgets first so re-seeding can never collide.
        DashboardWidgetConfiguration.objects.filter(
            dashboard_configuration=default_config,
            widget=widgets_by_name[name],
        ).delete()
        DashboardWidgetConfiguration.objects.create(
            dashboard_configuration=default_config,
            widget=widgets_by_name[name],
            position=position,
            column_span=column_span,
            row_span=1,
            is_visible=is_visible,
            configuration={},
        )


def reverse_initial_data(apps, schema_editor):
    DashboardConfiguration = apps.get_model("dashboard", "DashboardConfiguration")
    DashboardWidgetConfiguration = apps.get_model(
        "dashboard", "DashboardWidgetConfiguration"
    )
    DashboardWidget = apps.get_model("dashboard", "DashboardWidget")

    names = [widget["name"] for widget in WIDGETS]
    DashboardWidgetConfiguration.objects.filter(widget__name__in=names).delete()
    DashboardWidget.objects.filter(name__in=names).delete()
    DashboardConfiguration.objects.filter(name="Default Dashboard").update(
        is_default=False
    )


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0002_setup_initial_data"),
    ]

    operations = [
        migrations.RunPython(create_initial_data, reverse_initial_data),
    ]
