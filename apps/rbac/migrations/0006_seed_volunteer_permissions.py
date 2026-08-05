"""Seed Phase 13 volunteer permissions and operational role grants."""

from django.db import migrations


VOLUNTEER_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "archive",
    "restore",
    "export",
    "assign",
    "manage_attendance",
    "manage_training",
    "manage_performance",
    "manage_leave",
    "manage_exit",
    "view_confidential",
    "manage",
)

VOLUNTEER_OFFICER_ACTIONS = tuple(
    action for action in VOLUNTEER_ACTIONS if action != "view_confidential"
)


def seed_volunteer_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="volunteers",
        defaults={
            "name": "Volunteers",
            "description": "Volunteer lifecycle and confidential record access.",
            "sort_order": 13,
        },
    )
    content_type, _ = ContentType.objects.get_or_create(
        app_label="rbac",
        model="role",
    )
    permissions = {}
    for action in VOLUNTEER_ACTIONS:
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=f"volunteers.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} volunteers",
            },
        )
        permissions[action] = permission

    for role in Role.objects.filter(slug="volunteer-officer"):
        grants = [permissions[action] for action in VOLUNTEER_OFFICER_ACTIONS]
        permission_ids = [permission.pk for permission in grants]
        role.permissions.add(*permission_ids)
        if role.group_id:
            role.group.permissions.add(*permission_ids)


class Migration(migrations.Migration):
    # SQLite can leave the outer schema transaction marked for rollback when
    # idempotent get_or_create calls encounter existing permission rows.
    atomic = False
    dependencies = [("rbac", "0005_seed_membership_permissions")]

    operations = [
        migrations.RunPython(seed_volunteer_permissions, migrations.RunPython.noop)
    ]
