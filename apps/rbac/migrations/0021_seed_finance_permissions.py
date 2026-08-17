"""Seed Phase 27/28 Finance permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

FINANCE_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "approve",
    "archive",
    "restore",
    "export",
    "manage",
)

# Administrative roles hold the full catalogue; operational roles get view/create/update/approve/archive/export
ADMIN_FINANCE_ROLES = (
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

OPERATIONAL_FINANCE_ROLES = (
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

OPERATIONAL_FINANCE_ACTIONS = (
    "view",
    "create",
    "update",
    "approve",
    "archive",
    "export",
)


def seed_finance_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="finance",
        defaults={
            "name": "Finance",
            "description": "Financial management, budgets, transactions, grants, donors, sponsors, and fundraising.",
        },
    )

    content_type = ContentType.objects.get_for_model(Role)
    for action in FINANCE_ACTIONS:
        Permission.objects.update_or_create(
            codename=f"finance.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} finance",
                "content_type": content_type,
            },
        )

    def grant(role_slug: str, actions: tuple[str, ...]) -> None:
        role = Role.objects.filter(slug=role_slug).first()
        if not role:
            return
        permission_ids = []
        for action in actions:
            perm = Permission.objects.get(codename=f"finance.{action}")
            permission_ids.append(perm.pk)
        role.permissions.add(*permission_ids)
        if role.group_id:
            role.group.permissions.add(*permission_ids)

    for role_slug in ADMIN_FINANCE_ROLES:
        grant(role_slug, FINANCE_ACTIONS)
    for role_slug in OPERATIONAL_FINANCE_ROLES:
        grant(role_slug, OPERATIONAL_FINANCE_ACTIONS)


class Migration(migrations.Migration):

    atomic = False
    dependencies = [
        ("rbac", "0020_seed_qa_and_volunteer_roles"),
    ]

    operations = [
        migrations.RunPython(seed_finance_permissions, migrations.RunPython.noop),
    ]