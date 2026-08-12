"""Seed Phase 20 Report Instance permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

REPORT_INSTANCE_ACTIONS = (
    "view",
    "view_own",
    "view_all",
    "view_timeline",
    "view_validation",
    "create",
    "update",
    "update_own",
    "delete",
    "submit",
    "submit_own",
    "withdraw",
    "resubmit",
    "validate",
    "approve",
    "reject",
    "archive",
    "restore",
    "export",
    "assign",
    "comment",
    "comment_internal",
    "upload_evidence",
    "verify_evidence",
    "upload_attachment",
    "manage_reminders",
    "manage",
)

REVIEW_ACTIONS = tuple(
    action for action in REPORT_INSTANCE_ACTIONS if action != "manage"
)

OPERATE_ACTIONS = (
    "view",
    "view_own",
    "view_all",
    "view_timeline",
    "view_validation",
    "create",
    "update",
    "update_own",
    "delete",
    "submit",
    "submit_own",
    "withdraw",
    "resubmit",
    "comment",
    "comment_internal",
    "upload_evidence",
    "upload_attachment",
    "export",
)

VIEW_ACTIONS = ("view", "view_own", "view_timeline", "view_validation", "export")


def seed_report_instance_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="report_instances",
        defaults={
            "name": "Report Instances",
            "description": (
                "Concrete report instances created from published templates, "
                "including the report lifecycle (draft, validation, submission, "
                "withdrawal, resubmission, review, approval, archival), data "
                "entry, evidence, comments, version history, assignment, "
                "reminders and export."
            ),
            "sort_order": 20,
        },
    )
    content_type, _ = ContentType.objects.get_or_create(
        app_label="rbac",
        model="role",
    )
    permissions = {}
    for action in REPORT_INSTANCE_ACTIONS:
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=f"report_instances.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} report instances",
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
        **{slug: REPORT_INSTANCE_ACTIONS for slug in leadership_roles},
        **{slug: REVIEW_ACTIONS for slug in coordinator_roles},
        **{slug: OPERATE_ACTIONS for slug in officer_roles},
        **{slug: VIEW_ACTIONS for slug in governance_roles},
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
    dependencies = [("rbac", "0013_seed_register_permissions")]

    operations = [
        migrations.RunPython(
            seed_report_instance_permissions, migrations.RunPython.noop
        )
    ]
