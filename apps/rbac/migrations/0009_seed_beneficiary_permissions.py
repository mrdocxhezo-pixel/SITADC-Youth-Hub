"""Seed Phase 17 beneficiary permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

BENEFICIARY_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "archive",
    "restore",
    "export",
    "manage",
    "view_confidential",
    "submit",
    "approve",
    "manage_households",
    "manage_groups",
    "manage_enrollments",
    "manage_participation",
    "manage_attendance",
    "manage_services",
    "manage_referrals",
    "manage_case_notes",
    "manage_follow_ups",
    "manage_assessments",
    "manage_support_plans",
    "manage_consent",
    "manage_guardians",
    "manage_safeguarding",
    "manage_outcomes",
    "manage_exits",
    "manage_documents",
    "manage_feedback",
    "manage_transfers",
    "manage_duplicates",
    "analytics",
)

OPERATIONAL_ACTIONS = tuple(
    action for action in BENEFICIARY_ACTIONS if action != "view_confidential"
)

OFFICER_ACTIONS = tuple(
    action
    for action in OPERATIONAL_ACTIONS
    if action
    not in {
        "manage",
        "approve",
        "manage_safeguarding",
        "delete",
        "manage_duplicates",
    }
)

GOVERNANCE_ACTIONS = ("view", "view_confidential", "analytics")


def seed_beneficiary_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="beneficiaries",
        defaults={
            "name": "Beneficiaries",
            "description": (
                "Beneficiary profiling, lifecycle, services, and restricted records."
            ),
            "sort_order": 17,
        },
    )
    content_type, _ = ContentType.objects.get_or_create(
        app_label="rbac",
        model="role",
    )
    permissions = {}
    for action in BENEFICIARY_ACTIONS:
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=f"beneficiaries.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} beneficiaries",
            },
        )
        permissions[action] = permission

    coordinator_roles = (
        "regional-coordinator",
        "district-coordinator",
        "community-coordinator",
        "team-leader",
        "programme-manager",
        "project-manager",
    )
    officer_roles = ("project-officer", "meal-officer")
    governance_roles = (
        "president",
        "vice-president",
        "executive-director",
        "deputy-director",
        "director",
        "secretary-general",
        "board-chairperson",
        "board-secretary",
        "nec-member",
        "board-member",
    )
    role_actions = {
        **{slug: OPERATIONAL_ACTIONS for slug in coordinator_roles},
        **{slug: OFFICER_ACTIONS for slug in officer_roles},
        **{slug: GOVERNANCE_ACTIONS for slug in governance_roles},
    }
    for role_slug, actions in role_actions.items():
        for role in Role.objects.filter(slug=role_slug):
            grants = [permissions[action] for action in actions]
            permission_ids = [permission.pk for permission in grants]
            role.permissions.add(*permission_ids)
            if role.group_id:
                role.group.permissions.add(*permission_ids)


class Migration(migrations.Migration):
    # SQLite can leave the outer schema transaction marked for rollback when
    # idempotent get_or_create calls encounter existing permission rows.
    atomic = False
    dependencies = [("rbac", "0008_seed_volunteer_feature_permissions")]

    operations = [
        migrations.RunPython(
            seed_beneficiary_permissions, migrations.RunPython.noop
        )
    ]
