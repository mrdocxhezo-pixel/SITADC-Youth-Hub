"""Seed the extended membership permission actions and role grants."""

from django.db import migrations


def seed_membership_permissions(apps, schema_editor):
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    from apps.rbac.seed_data import (
        PERMISSION_CATEGORIES,
        ROLE_PERMISSION_SPECS,
        expand_role_permissions,
        permission_name,
    )

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    content_type, _ = ContentType.objects.get_or_create(app_label="rbac", model="role")

    for code, (label, actions) in sorted(PERMISSION_CATEGORIES.items()):
        PermissionCategory.objects.update_or_create(
            code=code,
            defaults={
                "name": label,
                "sort_order": sorted(PERMISSION_CATEGORIES).index(code),
            },
        )
        for action in actions:
            Permission.objects.get_or_create(
                content_type=content_type,
                codename=f"{code}.{action}",
                defaults={"name": permission_name(label, action)},
            )

    for seed in Role.objects.filter(slug__in=ROLE_PERMISSION_SPECS):
        spec = ROLE_PERMISSION_SPECS.get(seed.slug)
        if spec is None:
            continue
        codes = expand_role_permissions(spec)
        permission_ids = list(
            Permission.objects.filter(codename__in=codes).values_list("pk", flat=True)
        )
        seed.permissions.set(permission_ids)
        if seed.group_id:
            try:
                group = Group.objects.get(pk=seed.group_id)
            except Group.DoesNotExist:
                group = None
            if group is not None:
                group.permissions.set(permission_ids)


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0004_alter_rolehistory_action"),
    ]

    operations = [
        migrations.RunPython(seed_membership_permissions, migrations.RunPython.noop),
    ]
