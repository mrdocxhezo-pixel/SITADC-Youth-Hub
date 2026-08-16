"""Seed the Quality Assurance Officer and Volunteer roles and their grants."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations


def seed_roles(apps, schema_editor):
    from django.contrib.auth.models import Group, Permission

    from apps.rbac.seed_data import (
        DEFAULT_ROLES,
        ROLE_PERMISSION_SPECS,
        expand_role_permissions,
    )

    Role = apps.get_model("rbac", "Role")

    role_slugs = {"quality-assurance-officer", "volunteer"}

    for seed in DEFAULT_ROLES:
        if seed.slug not in role_slugs:
            continue
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

    atomic = False
    dependencies = [
        ("rbac", "0019_seed_exports_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
    ]