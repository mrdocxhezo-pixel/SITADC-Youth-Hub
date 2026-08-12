"""Seed Phase 23 Organizational Registers permissions."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

REGISTER_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "submit",
    "review",
    "approve",
    "archive",
    "restore",
    "export",
    "view_confidential",
    "manage",
)

FULL_ACCESS_ACTIONS = REGISTER_ACTIONS

OPERATE_ACTIONS = (
    "view",
    "create",
    "update",
    "submit",
    "review",
    "approve",
    "archive",
    "export",
)

VIEW_ACTIONS = ("view", "export")


def seed_register_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="registers",
        defaults={
            "name": "Registers",
            "description": (
                "Organizational registers including category and template "
                "configuration, entry management, approval workflow, search, "
                "confidentiality controls, archival and export."
            ),
            "sort_order": 23,
        },
    )
    content_type, _ = ContentType.objects.get_or_create(
        app_label="rbac",
        model="role",
    )
    permissions = {}
    for action in REGISTER_ACTIONS:
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=f"registers.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} registers",
            },
        )
        permissions[action] = permission

    role_actions = {
        "president": FULL_ACCESS_ACTIONS,
        "vice-president": FULL_ACCESS_ACTIONS,
        "executive-director": FULL_ACCESS_ACTIONS,
        "deputy-director": FULL_ACCESS_ACTIONS,
        "director": FULL_ACCESS_ACTIONS,
        "secretary-general": FULL_ACCESS_ACTIONS,
        "board-chairperson": VIEW_ACTIONS,
        "board-secretary": VIEW_ACTIONS,
        "nec-member": VIEW_ACTIONS,
        "board-member": VIEW_ACTIONS,
        "regional-coordinator": OPERATE_ACTIONS,
        "district-coordinator": OPERATE_ACTIONS,
        "community-coordinator": OPERATE_ACTIONS,
        "team-leader": OPERATE_ACTIONS,
        "programme-manager": OPERATE_ACTIONS,
        "project-manager": OPERATE_ACTIONS,
        "project-officer": OPERATE_ACTIONS,
        "meal-officer": OPERATE_ACTIONS,
        "research-officer": OPERATE_ACTIONS,
        "volunteer-coordinator": OPERATE_ACTIONS,
    }
    for role_slug, actions in role_actions.items():
        for role in Role.objects.filter(slug=role_slug):
            grants = [permissions[action] for action in actions]
            permission_ids = [permission.pk for permission in grants]
            role.permissions.add(*permission_ids)
            if role.group_id:
                role.group.permissions.add(*permission_ids)


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("rbac", "0012_seed_document_permissions")]

    operations = [
        migrations.RunPython(
            seed_register_permissions, migrations.RunPython.noop
        )
    ]
