"""
Idempotently seed the RBAC baseline: permission categories, access scopes,
Django permissions, roles and their linked Django groups.

Run with::

    python manage.py seed_default_roles

Seeding happens in the data migration ``0002_seed_rbac_baseline`` on fresh
databases; this command is provided so operators can re-sync or upgrade an
existing environment without re-running migrations.
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.rbac.constants import RoleStatus
from apps.rbac.models import AccessScope, PermissionCategory, Role
from apps.rbac.seed_data import (
    ACCESS_SCOPES,
    DEFAULT_ROLES,
    PERMISSION_CATEGORIES,
    ROLE_PERMISSION_SPECS,
    expand_role_permissions,
    permission_name,
)
from apps.rbac.services import sync_group_permissions


class Command(BaseCommand):
    help = "Seed permission categories, access scopes, permissions, roles and groups."

    @transaction.atomic
    def handle(self, *args, **options):
        verbosity = int(options.get("verbosity", 1))

        content_type, _ = ContentType.objects.get_or_create(
            app_label="rbac", model="role"
        )

        created_categories = 0
        for code, (label, _actions) in sorted(PERMISSION_CATEGORIES.items()):
            _, was_created = PermissionCategory.objects.update_or_create(
                code=code,
                defaults={
                    "name": label,
                    "sort_order": sorted(PERMISSION_CATEGORIES).index(code),
                },
            )
            if was_created:
                created_categories += 1

        created_permissions = 0
        for category, (label, actions) in sorted(PERMISSION_CATEGORIES.items()):
            for action in actions:
                code = f"{category}.{action}"
                _, was_created = Permission.objects.get_or_create(
                    content_type=content_type,
                    codename=code,
                    defaults={"name": permission_name(label, action)},
                )
                if was_created:
                    created_permissions += 1

        created_scopes = 0
        for code, name, level, description in ACCESS_SCOPES:
            _, was_created = AccessScope.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "level": level,
                    "description": description,
                    "is_active": True,
                },
            )
            if was_created:
                created_scopes += 1

        created_roles = 0
        for seed in DEFAULT_ROLES:
            group, _ = Group.objects.get_or_create(name=seed.name)
            role, role_created = Role.objects.update_or_create(
                slug=seed.slug,
                defaults={
                    "name": seed.name,
                    "description": seed.description,
                    "priority": seed.priority,
                    "is_system": seed.is_system,
                    "status": RoleStatus.ACTIVE,
                    "is_archived": False,
                    "is_deleted": False,
                    "group": group,
                },
            )
            spec = ROLE_PERMISSION_SPECS.get(seed.slug)
            if spec is not None:
                codes = expand_role_permissions(spec)
                role.permissions.set(Permission.objects.filter(codename__in=codes))
                sync_group_permissions(role)
            if role_created:
                created_roles += 1

        if verbosity:
            self.stdout.write(
                self.style.SUCCESS(
                    "RBAC baseline ready: "
                    f"{created_categories} categories, "
                    f"{created_permissions} permissions, "
                    f"{created_scopes} scopes, "
                    f"{created_roles} roles created."
                )
            )
