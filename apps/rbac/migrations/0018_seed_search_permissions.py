"""Seed Phase 26 Enterprise Search permissions and role grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

SEARCH_ACTIONS = (
    "view",
    "export",
    "manage",
)

# Categories -> actions granted per role (the "*" roles inherit search.manage
# automatically through the catalogue in seed_data).
ROLE_GRANTS = {
    "super-administrator": {"search": ("view", "export", "manage")},
    "system-administrator": {"search": ("view", "export", "manage")},
    "board-chairperson": {"search": ("view", "export")},
    "board-secretary": {"search": ("view", "export")},
    "board-member": {"search": ("view", "export")},
    "president": {"search": ("view", "export")},
    "vice-president": {"search": ("view", "export")},
    "executive-director": {"search": ("view", "export")},
    "executive-secretary": {"search": ("view", "export")},
    "secretary-general": {"search": ("view", "export")},
    "nec-member": {"search": ("view", "export")},
    "director": {"search": ("view", "export")},
    "deputy-director": {"search": ("view", "export")},
    "regional-coordinator": {"search": ("view", "export")},
    "district-coordinator": {"search": ("view", "export")},
    "community-coordinator": {"search": ("view", "export")},
    "team-leader": {"search": ("view", "export")},
    "programme-manager": {"search": ("view", "export")},
    "project-manager": {"search": ("view", "export")},
    "project-officer": {"search": ("view", "export")},
    "meal-officer": {"search": ("view", "export")},
    "finance-officer": {"search": ("view", "export")},
    "membership-officer": {"search": ("view", "export")},
    "volunteer-officer": {"search": ("view", "export")},
    "communications-officer": {"search": ("view", "export")},
    "training-officer": {"search": ("view", "export")},
    "research-officer": {"search": ("view", "export")},
    "partnerships-officer": {"search": ("view", "export")},
    "resource-mobilization-officer": {"search": ("view", "export")},
}


def seed_search_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    PermissionCategory.objects.update_or_create(
        code="search",
        defaults={
            "name": "Search",
            "description": "Unified enterprise-wide search across all modules.",
        },
    )

    content_type = ContentType.objects.get_for_model(Role)
    for action in SEARCH_ACTIONS:
        Permission.objects.update_or_create(
            codename=f"search.{action}",
            defaults={
                "name": f"Can {action} search",
                "content_type": content_type,
            },
        )

    for role_slug, category_actions in ROLE_GRANTS.items():
        role = Role.objects.filter(slug=role_slug).first()
        if not role:
            continue
        permission_ids = []
        for category, actions in category_actions.items():
            for action in actions:
                perm = Permission.objects.get(codename=f"{category}.{action}")
                permission_ids.append(perm.pk)
        role.permissions.add(*permission_ids)
        if role.group_id:
            role.group.permissions.add(*permission_ids)


class Migration(migrations.Migration):

    atomic = False
    dependencies = [
        ("rbac", "0017_seed_notification_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_search_permissions, migrations.RunPython.noop),
    ]
