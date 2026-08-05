"""Seed the reference numbering permission category and re-grant wildcard roles."""

from django.db import migrations


def seed_reference_number_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    from apps.rbac.seed_data import (
        DEFAULT_ROLES,
        PERMISSION_CATEGORIES,
        ROLE_PERMISSION_SPECS,
        expand_role_permissions,
        permission_name,
    )

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")
    Role = apps.get_model("rbac", "Role")

    content_type, _ = ContentType.objects.get_or_create(app_label="rbac", model="role")

    for code, (label, actions) in sorted(PERMISSION_CATEGORIES.items()):
        if code != "reference_numbers":
            continue
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

    # Roles configured with a "*" spec derive their grants from the catalogue,
    # so they must pick up the newly added reference numbering actions.
    for seed in DEFAULT_ROLES:
        spec = ROLE_PERMISSION_SPECS.get(seed.slug)
        if spec is None or "*" not in spec:
            continue
        role = Role.objects.filter(slug=seed.slug).first()
        if role is None:
            continue
        codes = expand_role_permissions(spec)
        permission_ids = list(
            Permission.objects.filter(codename__in=codes).values_list("pk", flat=True)
        )
        role.permissions.set(permission_ids)


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0002_seed_rbac_baseline"),
    ]

    operations = [
        migrations.RunPython(
            seed_reference_number_permissions, migrations.RunPython.noop
        ),
    ]
