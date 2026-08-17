"""Seed Phase 28 Settings permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

SETTINGS_ACTIONS = (
    "view",
    "update",
    "manage",
)

ADMIN_SETTINGS_ROLES = (
    "super-administrator",
    "system-administrator",
    "board-chairperson",
    "board-secretary",
    "board-member",
    "president",
    "vice-president",
    "executive-director",
    "executive-secretary",
    "secretary-general",
    "nec-member",
    "director",
    "deputy-director",
)

OPERATIONAL_SETTINGS_ROLES = (
    "regional-coordinator",
    "district-coordinator",
    "community-coordinator",
    "team-leader",
    "programme-manager",
    "project-manager",
    "project-officer",
    "meal-officer",
    "finance-officer",
    "membership-officer",
    "volunteer-officer",
    "communications-officer",
    "training-officer",
    "research-officer",
    "partnerships-officer",
    "resource-mobilization-officer",
)

OPERATIONAL_SETTINGS_ACTIONS = (
    "view",
    "update",
)


def seed_settings_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="settings",
        defaults={
            "name": "Settings",
            "description": "User preferences, system configuration, and integrations.",
        },
    )

    content_type = ContentType.objects.get_for_model(Role)
    for action in SETTINGS_ACTIONS:
        Permission.objects.update_or_create(
            codename=f"settings.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} settings",
                "content_type": content_type,
            },
        )

    def grant(role_slug: str, actions: tuple[str, ...]) -> None:
        role = Role.objects.filter(slug=role_slug).first()
        if not role:
            return
        permission_ids = []
        for action in actions:
            perm = Permission.objects.get(codename=f"settings.{action}")
            permission_ids.append(perm.pk)
        role.permissions.add(*permission_ids)
        if role.group_id:
            role.group.permissions.add(*permission_ids)

    for role_slug in ADMIN_SETTINGS_ROLES:
        grant(role_slug, SETTINGS_ACTIONS)
    for role_slug in OPERATIONAL_SETTINGS_ROLES:
        grant(role_slug, OPERATIONAL_SETTINGS_ACTIONS)


class Migration(migrations.Migration):

    atomic = False
    dependencies = [
        ("rbac", "0021_seed_finance_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_settings_permissions, migrations.RunPython.noop),
    ]