"""Seed Phase 24 Calendar & Meetings permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

MEETING_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "schedule",
    "reschedule",
    "cancel",
    "confirm",
    "start",
    "complete",
    "archive",
    "restore",
    "export",
    "manage_reminders",
    "manage_agendas",
    "approve_agendas",
    "manage_participants",
    "send_invitations",
    "record_attendance",
    "verify_attendance",
    "check_in",
    "check_out",
    "manage_quorum",
    "draft_minutes",
    "submit_minutes",
    "review_minutes",
    "approve_minutes",
    "record_decisions",
    "manage_actions",
    "verify_actions",
    "escalate",
    "manage_templates",
    "manage_venues",
    "configure",
    "view_confidential",
    "manage",
)

CALENDAR_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "share",
    "archive",
    "restore",
    "export",
    "view_confidential",
    "manage",
)

EVENT_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "schedule",
    "confirm",
    "complete",
    "cancel",
    "archive",
    "restore",
    "export",
    "manage_reminders",
    "view_confidential",
    "manage",
)

# Categories -> actions granted per role (subset used by non-* roles).
ROLE_GRANTS = {
    "board-secretary": {
        "meetings": (
            "view",
            "create",
            "update",
            "schedule",
            "reschedule",
            "cancel",
            "confirm",
            "start",
            "complete",
            "manage_agendas",
            "approve_agendas",
            "manage_participants",
            "send_invitations",
            "record_attendance",
            "verify_attendance",
            "manage_quorum",
            "draft_minutes",
            "submit_minutes",
            "review_minutes",
            "record_decisions",
            "manage_actions",
            "verify_actions",
            "escalate",
            "manage_reminders",
            "manage_templates",
            "manage_venues",
            "export",
        ),
        "calendars": ("view", "create", "update", "share", "export", "manage"),
        "events": ("view", "create", "update", "schedule", "confirm", "export"),
    },
    "executive-director": {
        "meetings": (
            "view",
            "create",
            "update",
            "schedule",
            "reschedule",
            "cancel",
            "confirm",
            "approve_agendas",
            "manage_quorum",
            "review_minutes",
            "approve_minutes",
            "verify_actions",
            "escalate",
            "export",
        ),
        "calendars": ("view", "create", "update", "share", "export"),
        "events": ("view", "create", "update", "schedule", "confirm", "export"),
    },
}


def seed_meeting_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    categories = (
        (
            "calendars",
            "Calendars",
            "Organizational calendars, sharing, visibility and availability.",
        ),
        (
            "events",
            "Events",
            "Calendar events, scheduling, confirmation and reminders.",
        ),
        (
            "meetings",
            "Meetings",
            "Meeting lifecycle, participants, invitations, agendas, attendance, "
            "quorum, minutes, decisions, action items and templates.",
        ),
    )
    for code, name, description in categories:
        PermissionCategory.objects.update_or_create(
            code=code,
            defaults={"name": name, "description": description},
        )

    content_type = ContentType.objects.get_for_model(Role)
    for code, actions in (
        ("calendars", CALENDAR_ACTIONS),
        ("events", EVENT_ACTIONS),
        ("meetings", MEETING_ACTIONS),
    ):
        for action in actions:
            Permission.objects.update_or_create(
                codename=f"{code}.{action}",
                defaults={
                    "name": f"Can {action.replace('_', ' ')} {code}",
                    "content_type": content_type,
                },
            )

    for role_slug, category_actions in ROLE_GRANTS.items():
        role = Role.objects.filter(slug=role_slug).first()
        if not role:
            continue
        permission_ids = []
        for category, actions in category_actions.items():
            for action in actions:
                perm = Permission.objects.get(codename=f"{category}.{action}")
                permission_ids.append(perm.pk)
        role.permissions.add(*permission_ids)
        if role.group_id:
            role.group.permissions.add(*permission_ids)


class Migration(migrations.Migration):

    atomic = False
    dependencies = [
        ("rbac", "0015_seed_review_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_meeting_permissions, migrations.RunPython.noop),
    ]
