"""Seed Phase 18 MEAL permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

MEAL_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "submit",
    "approve",
    "archive",
    "restore",
    "export",
    "view_confidential",
    "manage_frameworks",
    "manage_indicators",
    "manage_data_collection",
    "manage_monitoring",
    "manage_evaluations",
    "manage_dqa",
    "manage_accountability",
    "manage_learning",
    "manage_scorecards",
    "manage_reports",
    "configure",
    "manage",
)

OPERATIONAL_ACTIONS = tuple(
    action for action in MEAL_ACTIONS if action != "view_confidential"
)

MEAL_OFFICER_ACTIONS = tuple(
    action
    for action in OPERATIONAL_ACTIONS
    if action
    not in {
        "manage",
        "approve",
        "delete",
        "configure",
    }
)

FIELD_ACTIONS = (
    "view",
    "create",
    "update",
    "submit",
    "export",
    "manage_data_collection",
    "manage_monitoring",
    "manage_indicators",
)

GOVERNANCE_ACTIONS = ("view", "view_confidential", "export")


def seed_meal_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="meal",
        defaults={
            "name": "MEAL",
            "description": (
                "Monitoring, evaluation, accountability and learning, including "
                "frameworks, indicators, data collection, monitoring, "
                "evaluations, DQA, accountability, learning, scorecards and "
                "MEAL reports."
            ),
            "sort_order": 18,
        },
    )
    content_type, _ = ContentType.objects.get_or_create(
        app_label="rbac",
        model="role",
    )
    permissions = {}
    for action in MEAL_ACTIONS:
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=f"meal.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} MEAL",
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
        "meal-officer": MEAL_OFFICER_ACTIONS,
        "project-officer": FIELD_ACTIONS,
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
    dependencies = [("rbac", "0009_seed_beneficiary_permissions")]

    operations = [
        migrations.RunPython(
            seed_meal_permissions, migrations.RunPython.noop
        )
    ]
