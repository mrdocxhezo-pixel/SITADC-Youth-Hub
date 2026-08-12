"""Seed Phase 19 Report Template Builder permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

REPORT_TEMPLATE_ACTIONS = (
    "view",
    "create",
    "update",
    "delete",
    "preview",
    "publish",
    "archive",
    "restore",
    "clone",
    "import",
    "export",
    "configure",
    "manage",
)

OPERATIONAL_ACTIONS = tuple(
    action for action in REPORT_TEMPLATE_ACTIONS if action != "manage"
)

VIEW_ACTIONS = ("view", "preview", "export")


def seed_report_template_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="report_templates",
        defaults={
            "name": "Report Templates",
            "description": (
                "Dynamic report template builder including categories, "
                "templates, versions, schema design, preview, publication, "
                "archival, cloning and import/export of template definitions."
            ),
            "sort_order": 19,
        },
    )
    content_type, _ = ContentType.objects.get_or_create(
        app_label="rbac",
        model="role",
    )
    permissions = {}
    for action in REPORT_TEMPLATE_ACTIONS:
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=f"report_templates.{action}",
            defaults={
                "name": f"Can {action.replace('_', ' ')} report templates",
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
    builder_roles = ("meal-officer", "research-officer")
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
        **{slug: OPERATIONAL_ACTIONS for slug in builder_roles},
        "project-officer": VIEW_ACTIONS,
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
    # SQLite can leave the outer schema transaction marked for rollback when
    # idempotent get_or_create calls encounter existing permission rows.
    atomic = False
    dependencies = [("rbac", "0010_seed_meal_permissions")]

    operations = [
        migrations.RunPython(
            seed_report_template_permissions, migrations.RunPython.noop
        )
    ]
