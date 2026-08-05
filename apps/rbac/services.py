"""
Business services for the RBAC framework.

Every state-changing authorization operation flows through these services so
that audit history is recorded and invariants are enforced transactionally.
"""

from __future__ import annotations

import logging

from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.services import BaseService

from .constants import AssignmentStatus, RoleHistoryAction, RoleStatus
from .models import Role, RoleHistory, UserRoleAssignment
from .seed_data import ROLE_PERMISSION_SPECS, expand_role_permissions
from .validators import (
    validate_assignment_dates,
    validate_no_active_assignment,
    validate_permission_codes,
    validate_role_name_available,
    validate_role_slug_available,
    validate_role_usable,
)

logger = logging.getLogger(__name__)


def record_role_history(
    role: Role,
    action: str,
    changed_by,
    from_data: dict | None = None,
    to_data: dict | None = None,
    notes: str = "",
) -> RoleHistory:
    """Append an immutable audit record for a role change."""
    return RoleHistory.objects.create(
        role=role,
        action=action,
        changed_by=changed_by,
        from_data=from_data or {},
        to_data=to_data or {},
        notes=notes,
    )


def sync_group_permissions(role: Role) -> None:
    """
    Mirror the role's permissions onto its linked Django ``Group`` so that
    Django's permission framework stays consistent with the RBAC model.
    """
    if role.group is None:
        return
    role.group.permissions.set(role.permissions.all())


class CreateRoleService(BaseService):
    """Create a role, its linked Django group and an audit record."""

    def _execute(
        self,
        name: str,
        description: str = "",
        priority: int = 100,
        permissions: list[str] | None = None,
    ) -> Role:
        slug = slugify(name)
        validate_role_name_available(name)
        validate_role_slug_available(slug)
        validate_permission_codes(permissions or [])

        group = Group.objects.create(name=name)
        role = Role.objects.create(
            name=name,
            slug=slug,
            description=description,
            priority=priority,
            group=group,
            created_by=self.user,
            updated_by=self.user,
        )
        if permissions:
            role.permissions.set(Permission.objects.filter(codename__in=permissions))
        sync_group_permissions(role)
        record_role_history(
            role,
            RoleHistoryAction.CREATED,
            self.user,
            to_data={
                "name": role.name,
                "slug": role.slug,
                "priority": role.priority,
                "permissions": sorted(permissions or []),
            },
            notes="Role created.",
        )
        logger.info(f"Created role {role.slug} by {self.user}")
        return role


class UpdateRoleService(BaseService):
    """Update a role's metadata and its linked Django group name."""

    def _execute(
        self,
        role: Role,
        name: str,
        description: str,
        priority: int,
    ) -> Role:
        validate_role_name_available(name, exclude_pk=role.pk)
        from_data = {
            "name": role.name,
            "slug": role.slug,
            "description": role.description,
            "priority": role.priority,
        }
        role.name = name
        role.slug = slugify(name)
        validate_role_slug_available(role.slug, exclude_pk=role.pk)
        role.description = description
        role.priority = priority
        role.updated_by = self.user
        role.save(
            update_fields=[
                "name",
                "slug",
                "description",
                "priority",
                "updated_by",
                "updated_at",
            ]
        )

        if role.group is not None:
            role.group.name = name
            role.group.save(update_fields=["name"])

        record_role_history(
            role,
            RoleHistoryAction.UPDATED,
            self.user,
            from_data=from_data,
            to_data={
                "name": role.name,
                "slug": role.slug,
                "description": role.description,
                "priority": role.priority,
            },
            notes="Role metadata updated.",
        )
        logger.info(f"Updated role {role.slug} by {self.user}")
        return role


class SetRolePermissionsService(BaseService):
    """Replace a role's permission set and keep the Django group in sync."""

    def _execute(self, role: Role, permissions: list[str]) -> Role:
        validate_permission_codes(permissions)
        if role.is_system and not _may_modify_system_role(self.user):
            raise ValidationError(
                _("System roles may only be modified by administrators."),
                code="system_role_protected",
            )

        from_data = {"permissions": sorted(p.codename for p in role.permissions.all())}
        role.permissions.set(Permission.objects.filter(codename__in=permissions))
        role.updated_by = self.user
        role.save(update_fields=["updated_by", "updated_at"])
        sync_group_permissions(role)

        record_role_history(
            role,
            RoleHistoryAction.PERMISSIONS_CHANGED,
            self.user,
            from_data=from_data,
            to_data={"permissions": sorted(permissions)},
            notes="Role permissions updated.",
        )
        logger.info(f"Updated permissions for role {role.slug} by {self.user}")
        return role


class ArchiveRoleService(BaseService):
    """Archive a role so it is hidden from operational workflows."""

    def _execute(self, role: Role) -> Role:
        if role.is_system:
            raise ValidationError(
                _("System roles cannot be archived."),
                code="system_role_protected",
            )
        if role.is_archived:
            raise ValidationError(
                _("Role is already archived."), code="already_archived"
            )

        from_data = {"status": role.status, "is_archived": role.is_archived}
        role.archive(archived_by=self.user)
        record_role_history(
            role,
            RoleHistoryAction.ARCHIVED,
            self.user,
            from_data=from_data,
            to_data={"status": role.status, "is_archived": role.is_archived},
            notes="Role archived.",
        )
        logger.info(f"Archived role {role.slug} by {self.user}")
        return role


class RestoreRoleService(BaseService):
    """Restore an archived role back to active duty."""

    def _execute(self, role: Role) -> Role:
        if not role.is_archived:
            raise ValidationError(_("Role is not archived."), code="not_archived")

        from_data = {"status": role.status, "is_archived": role.is_archived}
        role.restore()
        role.updated_by = self.user
        role.save(
            update_fields=[
                "status",
                "is_archived",
                "archived_at",
                "archived_by",
                "updated_by",
                "updated_at",
            ]
        )
        record_role_history(
            role,
            RoleHistoryAction.RESTORED,
            self.user,
            from_data=from_data,
            to_data={"status": role.status, "is_archived": role.is_archived},
            notes="Role restored from archive.",
        )
        logger.info(f"Restored role {role.slug} by {self.user}")
        return role


class ActivateRoleService(BaseService):
    """Activate a role so it can be assigned to users."""

    def _execute(self, role: Role) -> Role:
        if role.is_archived:
            raise ValidationError(
                _("Archived roles must be restored before they can be activated."),
                code="archived_role",
            )
        if role.status == RoleStatus.ACTIVE:
            raise ValidationError(_("Role is already active."), code="already_active")

        from_data = {"status": role.status}
        role.status = RoleStatus.ACTIVE
        role.updated_by = self.user
        role.save(update_fields=["status", "updated_by", "updated_at"])
        record_role_history(
            role,
            RoleHistoryAction.ACTIVATED,
            self.user,
            from_data=from_data,
            to_data={"status": role.status},
            notes="Role activated.",
        )
        logger.info(f"Activated role {role.slug} by {self.user}")
        return role


class DeactivateRoleService(BaseService):
    """Deactivate a role so it can no longer be freshly assigned."""

    def _execute(self, role: Role) -> Role:
        if role.slug == "super-administrator":
            raise ValidationError(
                _("The Super Administrator role cannot be deactivated."),
                code="super_admin_protected",
            )
        if role.status == RoleStatus.INACTIVE:
            raise ValidationError(
                _("Role is already inactive."), code="already_inactive"
            )

        from_data = {"status": role.status}
        role.status = RoleStatus.INACTIVE
        role.updated_by = self.user
        role.save(update_fields=["status", "updated_by", "updated_at"])
        record_role_history(
            role,
            RoleHistoryAction.DEACTIVATED,
            self.user,
            from_data=from_data,
            to_data={"status": role.status},
            notes="Role deactivated.",
        )
        logger.info(f"Deactivated role {role.slug} by {self.user}")
        return role


class CloneRoleService(BaseService):
    """Clone an existing role (metadata and permissions) under a new name."""

    def _execute(self, source_role: Role, new_name: str) -> Role:
        validate_role_name_available(new_name)
        slug = slugify(new_name)
        validate_role_slug_available(slug)

        group = Group.objects.create(name=new_name)
        cloned = Role.objects.create(
            name=new_name,
            slug=slug,
            description=(
                f"Cloned from {source_role.name}. " f"{source_role.description}"
            ).strip(),
            priority=source_role.priority,
            is_system=False,
            group=group,
            created_by=self.user,
            updated_by=self.user,
        )
        permission_ids = list(source_role.permissions.values_list("id", flat=True))
        cloned.permissions.set(permission_ids)
        sync_group_permissions(cloned)

        record_role_history(
            cloned,
            RoleHistoryAction.CLONED,
            self.user,
            to_data={
                "source_role": source_role.slug,
                "permissions": sorted(
                    p.codename for p in source_role.permissions.all()
                ),
            },
            notes=f"Cloned from {source_role.slug}.",
        )
        logger.info(f"Cloned role {source_role.slug} -> {cloned.slug} by {self.user}")
        return cloned


class DeleteRoleService(BaseService):
    """Soft-delete a role and its linked Django group."""

    def _execute(self, role: Role) -> None:
        if role.is_system:
            raise ValidationError(
                _("System roles cannot be deleted."),
                code="system_role_protected",
            )
        if UserRoleAssignment.objects.filter(
            role=role, status=AssignmentStatus.ACTIVE
        ).exists():
            raise ValidationError(
                _("This role is still assigned to users and cannot be deleted."),
                code="role_in_use",
            )
        record_role_history(
            role,
            RoleHistoryAction.DELETED,
            self.user,
            to_data={"name": role.name},
            notes="Role deleted.",
        )
        if role.group is not None:
            group = role.group
            role.group = None
            role.save(update_fields=["group"])
            group.delete()
        role.delete(deleted_by=self.user)
        logger.info(f"Deleted role {role.slug} by {self.user}")


class AssignRoleService(BaseService):
    """Assign a role (with optional scope and dates) to a user."""

    def _execute(
        self,
        user,
        role: Role,
        access_scope=None,
        is_primary: bool = False,
        effective_from=None,
        expires_at=None,
        notes: str = "",
    ) -> UserRoleAssignment:
        validate_role_usable(role)
        validate_assignment_dates(effective_from, expires_at)
        validate_no_active_assignment(user, role, access_scope)

        if is_primary:
            _clear_other_primary(user)

        assignment = UserRoleAssignment.objects.create(
            user=user,
            role=role,
            access_scope=access_scope,
            is_primary=is_primary,
            status=AssignmentStatus.ACTIVE,
            effective_from=effective_from or timezone.now(),
            expires_at=expires_at,
            assigned_by=self.user,
            notes=notes,
        )

        record_role_history(
            role,
            RoleHistoryAction.ROLE_ASSIGNED,
            self.user,
            to_data={
                "user": str(user),
                "scope": access_scope.code if access_scope else None,
                "is_primary": is_primary,
                "expires_at": expires_at.isoformat() if expires_at else None,
            },
            notes="Role assigned to user.",
        )
        logger.info(f"Assigned role {role.slug} to {user} by {self.user}")
        return assignment


class RevokeRoleService(BaseService):
    """Revoke an active role assignment (soft state change, fully audited)."""

    def _execute(self, assignment: UserRoleAssignment) -> UserRoleAssignment:
        if assignment.status != AssignmentStatus.ACTIVE:
            raise ValidationError(
                _("This assignment is not active and cannot be revoked."),
                code="assignment_not_active",
            )
        assignment.status = AssignmentStatus.REVOKED
        assignment.save(update_fields=["status"])
        record_role_history(
            assignment.role,
            RoleHistoryAction.ROLE_REVOKED,
            self.user,
            to_data={
                "user": str(assignment.user),
                "scope": (
                    assignment.access_scope.code if assignment.access_scope else None
                ),
            },
            notes="Role assignment revoked.",
        )
        logger.info(
            f"Revoked role {assignment.role.slug} for {assignment.user} by {self.user}"
        )
        return assignment


def _clear_other_primary(user) -> None:
    """Ensure only one primary active assignment exists per user."""
    UserRoleAssignment.objects.filter(user=user, is_primary=True).update(
        is_primary=False
    )


def _may_modify_system_role(user) -> bool:
    from .authorization import user_has_permission

    return bool(user and user.is_superuser) or bool(
        user and user_has_permission(user, "administration.manage")
    )


def seed_role_permissions_for_role(role: Role) -> None:
    """Apply the canonical permission spec for a default role slug, if any."""
    spec = ROLE_PERMISSION_SPECS.get(role.slug)
    if spec is None:
        return
    codes = expand_role_permissions(spec)
    role.permissions.set(Permission.objects.filter(codename__in=codes))
    sync_group_permissions(role)
