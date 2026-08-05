"""Seed Phase 14 stakeholder permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

STAKEHOLDER_ACTIONS = (
    "view",
    "view_directory",
    "view_profile",
    "view_private_contacts",
    "view_due_diligence",
    "view_financial",
    "view_confidential",
    "create",
    "update",
    "delete",
    "archive",
    "restore",
    "export",
    "assign",
    "manage_categories",
    "manage_contacts",
    "assess",
    "manage_engagements",
    "manage_communications",
    "manage_commitments",
    "manage_contributions",
    "manage_agreements",
    "review_agreements",
    "approve_agreements",
    "manage_due_diligence",
    "manage_risk",
    "manage_performance",
    "review_performance",
    "manage_actions",
    "manage_notes",
    "manage_documents",
    "manage_access",
    "analytics",
    "manage",
)


def seed_stakeholder_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="partners",
        defaults={
            "name": "Stakeholders and Partnerships",
            "description": (
                "Stakeholder lifecycle, relationships, and restricted records."
            ),
            "sort_order": 14,
        },
    )
    content_type, _ = ContentType.objects.get_or_create(app_label="rbac", model="role")
    permissions = {}
    for action in STAKEHOLDER_ACTIONS:
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=f"partners.{action}",
            defaults={"name": f"Can {action.replace('_', ' ')} stakeholders"},
        )
        permissions[action] = permission

    operational_actions = tuple(
        action for action in STAKEHOLDER_ACTIONS if action != "view_confidential"
    )
    role_actions = {
        "partnerships-officer": operational_actions,
        "resource-mobilization-officer": operational_actions,
        "legal-governance-officer": (
            "view",
            "view_profile",
            "view_due_diligence",
            "view_confidential",
            "review_agreements",
            "approve_agreements",
            "manage_due_diligence",
            "manage_risk",
        ),
    }
    for role_slug, actions in role_actions.items():
        for role in Role.objects.filter(slug=role_slug):
            grants = [permissions[action] for action in actions]
            role.permissions.add(*[permission.pk for permission in grants])
            if role.group_id:
                role.group.permissions.add(*[permission.pk for permission in grants])


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("rbac", "0006_seed_volunteer_permissions")]
    operations = [
        migrations.RunPython(seed_stakeholder_permissions, migrations.RunPython.noop)
    ]
