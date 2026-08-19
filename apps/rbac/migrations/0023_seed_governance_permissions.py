"""Seed Phase 29 Governance, Risk, Compliance and Safeguarding permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

GOVERNANCE_ACTIONS = (
    "view",
    "view_confidential",
    "create",
    "update",
    "delete",
    "approve",
    "archive",
    "restore",
    "export",
    "manage",
)

# Administrative roles hold the full governance catalogue
ADMIN_GOVERNANCE_ROLES = (
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

# Operational roles with governance responsibilities
OPERATIONAL_GOVERNANCE_ROLES = (
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
    "quality-assurance-officer",
)

OPERATIONAL_GOVERNANCE_ACTIONS = (
    "view",
    "create",
    "update",
    "approve",
    "archive",
    "export",
)

# Specialized governance roles
GOVERNANCE_OFFICER_ROLES = (
    "governance-officer",
    "risk-officer",
    "compliance-officer",
    "safeguarding-officer",
    "ethics-officer",
)

GOVERNANCE_OFFICER_ACTIONS = (
    "view",
    "view_confidential",
    "create",
    "update",
    "delete",
    "approve",
    "archive",
    "restore",
    "export",
    "manage",
)


def seed_governance_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="governance",
        defaults={
            "name": "Governance",
            "description": "Governance, risk management, compliance monitoring, safeguarding, ethics, incident reporting, complaints, whistleblower management, and corrective actions.",
        },
    )

    content_type = ContentType.objects.get_for_model(Role)
    for action in GOVERNANCE_ACTIONS:
        Permission.objects.update_or_create(
            codename=f"governance.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} governance",
                "content_type": content_type,
            },
        )

    def grant(role_slug: str, actions: tuple[str, ...]) -> None:
        role = Role.objects.filter(slug=role_slug).first()
        if not role:
            return
        permission_ids = []
        for action in actions:
            perm = Permission.objects.get(codename=f"governance.{action}")
            permission_ids.append(perm.pk)
        role.permissions.add(*permission_ids)
        if role.group_id:
            role.group.permissions.add(*permission_ids)

    for role_slug in ADMIN_GOVERNANCE_ROLES:
        grant(role_slug, GOVERNANCE_ACTIONS)
    for role_slug in OPERATIONAL_GOVERNANCE_ROLES:
        grant(role_slug, OPERATIONAL_GOVERNANCE_ACTIONS)
    for role_slug in GOVERNANCE_OFFICER_ROLES:
        grant(role_slug, GOVERNANCE_OFFICER_ACTIONS)


class Migration(migrations.Migration):

    atomic = False
    dependencies = [
        ("rbac", "0022_seed_settings_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_governance_permissions, migrations.RunPython.noop),
    ]