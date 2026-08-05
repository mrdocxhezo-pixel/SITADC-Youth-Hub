"""Seed the RBAC baseline: categories, scopes, permissions, roles and groups."""

from django.db import migrations


def seed_rbac_baseline(apps, schema_editor):
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    from apps.rbac.seed_data import (
        ACCESS_SCOPES,
        DEFAULT_ROLES,
        PERMISSION_CATEGORIES,
        ROLE_PERMISSION_SPECS,
        expand_role_permissions,
        permission_name,
    )

    AccessScope = apps.get_model("rbac", "AccessScope")
    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    content_type, _ = ContentType.objects.get_or_create(app_label="rbac", model="role")

    for code, (label, _actions) in sorted(PERMISSION_CATEGORIES.items()):
        PermissionCategory.objects.update_or_create(
            code=code,
            defaults={
                "name": label,
                "sort_order": sorted(PERMISSION_CATEGORIES).index(code),
            },
        )

    for category, (label, actions) in sorted(PERMISSION_CATEGORIES.items()):
        for action in actions:
            Permission.objects.get_or_create(
                content_type=content_type,
                codename=f"{category}.{action}",
                defaults={"name": permission_name(label, action)},
            )

    for code, name, level, description in ACCESS_SCOPES:
        AccessScope.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "level": level,
                "description": description,
                "is_active": True,
            },
        )

    for seed in DEFAULT_ROLES:
        group, _ = Group.objects.get_or_create(name=seed.name)
        role, _ = Role.objects.update_or_create(
            slug=seed.slug,
            defaults={
                "name": seed.name,
                "description": seed.description,
                "priority": seed.priority,
                "is_system": seed.is_system,
                "status": "ACTIVE",
                "is_archived": False,
                "is_deleted": False,
                "group_id": group.pk,
            },
        )
        spec = ROLE_PERMISSION_SPECS.get(seed.slug)
        if spec is not None:
            codes = expand_role_permissions(spec)
            permission_ids = list(
                Permission.objects.filter(codename__in=codes).values_list(
                    "pk", flat=True
                )
            )
            role.permissions.set(permission_ids)
            group.permissions.set(permission_ids)


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_rbac_baseline, migrations.RunPython.noop),
    ]
