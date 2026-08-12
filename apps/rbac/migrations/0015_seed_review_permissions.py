"""Seed Phase 21 Review & Approval permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

REVIEW_ACTIONS = (
    "view",
    "create",
    "assign",
    "accept",
    "start",
    "comment",
    "resolve_comment",
    "update_checklist",
    "decide",
    "approve",
    "reject",
    "return_for_correction",
    "escalate",
    "delegate",
    "sign",
    "manage_checklists",
    "manage_sla",
    "manage_configuration",
    "manage",
)

REVIEWER_ACTIONS = tuple(
    action for action in REVIEW_ACTIONS if action != "manage"
)

OPERATIONAL_ACTIONS = (
    "view",
    "accept",
    "start",
    "comment",
    "resolve_comment",
    "update_checklist",
    "escalate",
    "delegate",
    "sign",
)

BOARD_ACTIONS = ("view", "approve", "reject")


def seed_review_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="reviews",
        defaults={
            "name": "Reviews",
            "description": (
                "Structured review and approval of submitted reports, including "
                "reviewer assignment, acceptance, review lifecycle, structured "
                "comments, checklist responses, evidence verification, formal "
                "decisions (approve, reject, return for correction), escalation, "
                "delegation, digital signatures and SLA monitoring."
            ),
            "sort_order": 21,
        },
    )
    content_type, _ = ContentType.objects.get_or_create(
        app_label="rbac",
        model="role",
    )
    permissions = {}
    for action in REVIEW_ACTIONS:
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=f"reviews.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} reviews",
            },
        )
        permissions[action] = permission

    leadership_roles = (
        "super-administrator",
        "system-administrator",
        "president",
        "vice-president",
        "executive-director",
        "executive-secretary",
        "secretary-general",
        "director",
        "deputy-director",
    )
    coordinator_roles = (
        "regional-coordinator",
        "district-coordinator",
        "community-coordinator",
        "team-leader",
        "programme-manager",
        "project-manager",
    )
    officer_roles = (
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
        "volunteer-coordinator",
    )
    governance_roles = (
        "board-chairperson",
        "board-secretary",
        "nec-member",
        "board-member",
    )
    role_actions = {
        **{slug: REVIEW_ACTIONS for slug in leadership_roles},
        **{slug: REVIEWER_ACTIONS for slug in coordinator_roles},
        **{slug: OPERATIONAL_ACTIONS for slug in officer_roles},
        **{slug: BOARD_ACTIONS for slug in governance_roles},
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
    dependencies = [("rbac", "0014_seed_report_instance_permissions")]

    operations = [
        migrations.RunPython(
            seed_review_permissions, migrations.RunPython.noop
        )
    ]
