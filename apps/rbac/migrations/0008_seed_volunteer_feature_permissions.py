"""Seed additional Phase 13 volunteer feature permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

ADDITIONAL_VOLUNTEER_ACTIONS = (
    "manage_activity",
    "manage_disciplinary",
    "manage_communications",
    "manage_documents",
    "configure",
)

VOLUNTEER_OFFICER_ACTIONS = (
    "manage_activity",
    "manage_disciplinary",
    "manage_communications",
    "manage_documents",
)


def seed_additional_volunteer_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    Role = apps.get_model("rbac", "Role")

    content_type, _ = ContentType.objects.get_or_create(
        app_label="rbac",
        model="role",
    )
    permissions = {}
    for action in ADDITIONAL_VOLUNTEER_ACTIONS:
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
    atomic = False
    dependencies = [("rbac", "0007_seed_stakeholder_permissions")]

    operations = [
        migrations.RunPython(
            seed_additional_volunteer_permissions, migrations.RunPython.noop
        )
    ]
