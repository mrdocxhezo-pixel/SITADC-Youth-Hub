"""Seed Phase 30 Communication and Media permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

COMMUNICATIONS_ACTIONS = (
    "view",
    "view_confidential",
    "create",
    "update",
    "delete",
    "approve",
    "publish",
    "archive",
    "restore",
    "export",
    "manage",
)

# Administrative roles hold the full communications catalogue
ADMIN_COMMUNICATIONS_ROLES = (
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

# Roles dedicated to communications operations hold the full catalogue
COMMUNICATIONS_OFFICER_ROLES = (
    "communications-officer",
)

# Operational roles with communications responsibilities
OPERATIONAL_COMMUNICATIONS_ROLES = (
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
    "training-officer",
    "research-officer",
    "partnerships-officer",
    "resource-mobilization-officer",
    "quality-assurance-officer",
)

OPERATIONAL_COMMUNICATIONS_ACTIONS = (
    "view",
    "create",
    "update",
    "publish",
    "archive",
    "export",
)


def seed_communications_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="communications",
        defaults={
            "name": "Communications",
            "description": "Internal and external communications, news, newsletters, press releases, social media, website content, campaigns, media library, publications, branding, and event communications.",
        },
    )

    content_type = ContentType.objects.get_for_model(Role)
    for action in COMMUNICATIONS_ACTIONS:
        Permission.objects.update_or_create(
            codename=f"communications.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} communications",
                "content_type": content_type,
            },
        )

    def grant(role_slug: str, actions: tuple[str, ...]) -> None:
        role = Role.objects.filter(slug=role_slug).first()
        if not role:
            return
        permission_ids = []
        for action in actions:
            perm = Permission.objects.get(codename=f"communications.{action}")
            permission_ids.append(perm.pk)
        role.permissions.add(*permission_ids)
        if role.group_id:
            role.group.permissions.add(*permission_ids)

    for role_slug in ADMIN_COMMUNICATIONS_ROLES:
        grant(role_slug, COMMUNICATIONS_ACTIONS)
    for role_slug in COMMUNICATIONS_OFFICER_ROLES:
        grant(role_slug, COMMUNICATIONS_ACTIONS)
    for role_slug in OPERATIONAL_COMMUNICATIONS_ROLES:
        grant(role_slug, OPERATIONAL_COMMUNICATIONS_ACTIONS)


class Migration(migrations.Migration):

    atomic = False
    dependencies = [
        ("rbac", "0023_seed_governance_permissions"),
    ]

    operations = [
        migrations.RunPython(
            seed_communications_permissions, migrations.RunPython.noop
        ),
    ]