"""Seed Phase 27 Export Engine permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

EXPORTS_ACTIONS = (
    "view",
    "create",
    "download",
    "print",
    "export_pdf",
    "export_docx",
    "export_xlsx",
    "export_csv",
    "export_reports",
    "export_documents",
    "export_registers",
    "export_directories",
    "export_programs",
    "export_projects",
    "export_meal",
    "export_meetings",
    "export_beneficiaries",
    "export_sensitive",
    "export_bulk",
    "view_history",
    "view_all_history",
    "cancel",
    "regenerate",
    "manage_templates",
    "manage_settings",
    "manage",
)

# Roles that can operate the Export Engine.  Administrative roles hold the
# full catalogue; operational roles can view/create/download and export every
# registered source without the sensitive/bulk/manage grants.
ADMIN_EXPORTS_ROLES = (
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

OPERATIONAL_EXPORTS_ROLES = (
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

OPERATIONAL_EXPORTS_ACTIONS = (
    "view",
    "create",
    "download",
    "print",
    "export_pdf",
    "export_docx",
    "export_xlsx",
    "export_csv",
    "export_reports",
    "export_documents",
    "export_registers",
    "export_directories",
    "export_programs",
    "export_projects",
    "export_meal",
    "export_meetings",
    "export_beneficiaries",
    "view_history",
    "cancel",
)


def seed_exports_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="exports",
        defaults={
            "name": "Export Engine",
            "description": "Centralized, permission-aware export of platform data.",
        },
    )

    content_type = ContentType.objects.get_for_model(Role)
    for action in EXPORTS_ACTIONS:
        Permission.objects.update_or_create(
            codename=f"exports.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} exports",
                "content_type": content_type,
            },
        )

    def grant(role_slug: str, actions: tuple[str, ...]) -> None:
        role = Role.objects.filter(slug=role_slug).first()
        if not role:
            return
        permission_ids = []
        for action in actions:
            perm = Permission.objects.get(codename=f"exports.{action}")
            permission_ids.append(perm.pk)
        role.permissions.add(*permission_ids)
        if role.group_id:
            role.group.permissions.add(*permission_ids)

    for role_slug in ADMIN_EXPORTS_ROLES:
        grant(role_slug, EXPORTS_ACTIONS)
    for role_slug in OPERATIONAL_EXPORTS_ROLES:
        grant(role_slug, OPERATIONAL_EXPORTS_ACTIONS)


class Migration(migrations.Migration):

    atomic = False
    dependencies = [
        ("rbac", "0018_seed_search_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_exports_permissions, migrations.RunPython.noop),
    ]
