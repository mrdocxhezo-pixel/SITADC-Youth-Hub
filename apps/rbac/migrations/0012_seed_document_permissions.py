"""Seed Phase 22 Document Management permissions."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

DOCUMENT_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "download",
    "upload",
    "approve",
    "archive",
    "restore",
    "export",
    "manage",
    "submit",
    "review",
    "publish",
    "unpublish",
    "checkout",
    "checkin",
    "cancel_checkout",
    "upload_version",
    "update_metadata",
    "return_for_correction",
    "request_disposal",
    "approve_disposal",
    "print",
    "share_internal",
    "share_external",
    "manage_categories",
    "manage_types",
    "manage_folders",
    "manage_tags",
    "manage_retention",
    "view_history",
    "view_audit",
)

FULL_ACCESS_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "download",
    "upload",
    "approve",
    "archive",
    "restore",
    "export",
    "manage",
    "submit",
    "review",
    "publish",
    "unpublish",
    "checkout",
    "checkin",
    "cancel_checkout",
    "upload_version",
    "update_metadata",
    "return_for_correction",
    "request_disposal",
    "approve_disposal",
    "print",
    "share_internal",
    "share_external",
    "manage_categories",
    "manage_types",
    "manage_folders",
    "manage_tags",
    "manage_retention",
    "view_history",
    "view_audit",
)

OPERATE_ACTIONS = (
    "view",
    "create",
    "update",
    "upload",
    "download",
    "submit",
    "checkout",
    "checkin",
    "upload_version",
    "update_metadata",
    "print",
    "share_internal",
)

VIEW_ACTIONS = ("view", "download", "view_history", "view_audit")


def seed_document_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="documents",
        defaults={
            "name": "Documents",
            "description": (
                "Document management including upload, versioning, checkout, "
                "workflow, sharing, archival, retention and disposal."
            ),
            "sort_order": 22,
        },
    )
    content_type, _ = ContentType.objects.get_or_create(
        app_label="rbac",
        model="role",
    )
    permissions = {}
    for action in DOCUMENT_ACTIONS:
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=f"documents.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} documents",
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
    dependencies = [("rbac", "0011_seed_report_template_permissions")]

    operations = [
        migrations.RunPython(
            seed_document_permissions, migrations.RunPython.noop
        )
    ]
