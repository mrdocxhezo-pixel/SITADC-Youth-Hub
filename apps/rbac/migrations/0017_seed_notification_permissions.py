"""Seed Phase 25 Notifications & Announcements permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

NOTIFICATION_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "send",
    "archive",
    "manage_templates",
    "manage_rules",
    "configure",
    "manage",
)

ANNOUNCEMENT_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "publish",
    "manage",
)

PREFERENCE_ACTIONS = (
    "view",
    "update",
    "manage",
)

# Categories -> actions granted per role (subset used by non-* roles).
ROLE_GRANTS = {
    "communications-officer": {
        "notifications": ("view", "create", "send", "archive"),
        "announcements": ("view", "create", "update", "publish", "manage"),
        "preferences": ("view", "update"),
    },
    "board-secretary": {
        "notifications": ("view", "create", "send", "archive"),
        "announcements": ("view", "create", "update", "publish"),
        "preferences": ("view", "update"),
    },
    "executive-director": {
        "notifications": ("view", "create", "send", "archive"),
        "announcements": ("view", "create", "update", "publish"),
        "preferences": ("view", "update"),
    },
}


def seed_notification_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    categories = (
        (
            "notifications",
            "Notifications",
            "In-app notifications, delivery channels, templates, rules and digests.",
        ),
        (
            "announcements",
            "Announcements",
            "Organizational announcements targeted to roles or units.",
        ),
        (
            "preferences",
            "Notification Preferences",
            "Per-user notification channel, digest and quiet-hours preferences.",
        ),
    )
    for code, name, description in categories:
        PermissionCategory.objects.update_or_create(
            code=code,
            defaults={"name": name, "description": description},
        )

    content_type = ContentType.objects.get_for_model(Role)
    for code, actions in (
        ("notifications", NOTIFICATION_ACTIONS),
        ("announcements", ANNOUNCEMENT_ACTIONS),
        ("preferences", PREFERENCE_ACTIONS),
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
        ("rbac", "0016_seed_meeting_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_notification_permissions, migrations.RunPython.noop),
    ]
