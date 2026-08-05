"""Seed the Organizations permission category and its permissions."""

from django.db import migrations

from apps.rbac.seed_data import PERMISSION_CATEGORIES, permission_name


def seed_organizations_permissions(apps, schema_editor):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    PermissionCategory = apps.get_model("rbac", "PermissionCategory")

    category_code = "organizations"
    label, actions = PERMISSION_CATEGORIES[category_code]

    content_type, _ = ContentType.objects.get_or_create(app_label="rbac", model="role")

    PermissionCategory.objects.update_or_create(
        code=category_code,
        defaults={
            "name": label,
            "sort_order": sorted(PERMISSION_CATEGORIES).index(category_code),
        },
    )

    for action in actions:
        Permission.objects.get_or_create(
            content_type=content_type,
            codename=f"{category_code}.{action}",
            defaults={"name": permission_name(label, action)},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0001_initial"),
        ("rbac", "0002_seed_rbac_baseline"),
    ]

    operations = [
        migrations.RunPython(seed_organizations_permissions, migrations.RunPython.noop),
    ]
