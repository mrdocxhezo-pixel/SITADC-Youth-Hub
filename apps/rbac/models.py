from typing import ClassVar

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    ArchivableModel,
    CreatedByModel,
    SoftDeleteModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)

from .constants import AssignmentStatus, RoleHistoryAction, RoleStatus


class PermissionCategory(UUIDModel, TimeStampedModel):
    """
    A functional grouping of permissions, e.g. ``Reports`` or ``Finance``.

    Category codes double as the ``module`` component of the
    ``module.action`` permission naming convention.
    """

    code = models.CharField(_("Code"), max_length=50, unique=True)
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("Permission Category")
        verbose_name_plural = _("Permission Categories")
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class AccessScope(UUIDModel, TimeStampedModel):
    """
    A hierarchical organizational access scope.

    Level values align with ``AccessScopeLevel``; lower values denote broader
    scopes that cover every narrower scope.  Phase 08 will attach concrete
    organizational units to these scopes.
    """

    code = models.CharField(_("Code"), max_length=50, unique=True)
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    level = models.PositiveIntegerField(_("Level"), unique=True, db_index=True)
    is_active = models.BooleanField(_("Is active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Access Scope")
        verbose_name_plural = _("Access Scopes")
        ordering = ("level", "name")

    def __str__(self) -> str:
        return self.name


class Role(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    SoftDeleteModel,
    ArchivableModel,
):
    """
    A role groups related permissions and maps to a Django ``Group``.

    Business logic must never depend directly on role names; authorization
    decisions are made by the RBAC authorization services.
    """

    name = models.CharField(_("Name"), max_length=150, unique=True)
    slug = models.SlugField(_("Slug"), max_length=150, unique=True)
    description = models.TextField(_("Description"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=RoleStatus.choices,
        default=RoleStatus.ACTIVE,
        db_index=True,
    )
    priority = models.PositiveIntegerField(
        _("Priority"),
        default=100,
        help_text=_("Lower values indicate higher authority."),
    )
    is_system = models.BooleanField(
        _("System role"),
        default=False,
        help_text=_("System roles are seeded by the platform and cannot be deleted."),
    )
    permissions = models.ManyToManyField(
        Permission,
        related_name="roles",
        verbose_name=_("Permissions"),
        blank=True,
    )
    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="role",
        verbose_name=_("Django group"),
    )

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        ordering = ("priority", "name")

    def __str__(self) -> str:
        return self.name

    def archive(self, archived_by=None) -> None:
        """Archive the role, keeping it searchable and auditable."""
        super().archive(archived_by=archived_by)
        self.status = RoleStatus.INACTIVE
        self.save(update_fields=["status"])

    def restore(self) -> None:
        """Restore an archived role back to active duty."""
        super().unarchive()
        self.status = RoleStatus.ACTIVE
        self.save(update_fields=["status"])


class RoleHistory(UUIDModel, TimeStampedModel):
    """
    Immutable audit trail of every role lifecycle and permission change.
    """

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name=_("Role"),
    )
    action = models.CharField(
        _("Action"),
        max_length=40,
        choices=RoleHistoryAction.choices,
        db_index=True,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="role_history_changes",
        verbose_name=_("Changed by"),
    )
    from_data = models.JSONField(_("From data"), default=dict, blank=True)
    to_data = models.JSONField(_("To data"), default=dict, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Role History")
        verbose_name_plural = _("Role History")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.role.name} - {self.get_action_display()}"

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError(
                _("Role history records are immutable and cannot be modified."),
                code="immutable_role_history",
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            _("Role history records are immutable and cannot be deleted."),
            code="immutable_role_history",
        )


class UserRoleAssignment(UUIDModel, TimeStampedModel):
    """
    Associates a user with a role, an optional access scope and assignment
    metadata.  Users may hold multiple roles simultaneously.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="role_assignments",
        verbose_name=_("User"),
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_assignments",
        verbose_name=_("Role"),
    )
    access_scope = models.ForeignKey(
        AccessScope,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="role_assignments",
        verbose_name=_("Access scope"),
        help_text=_("Leave blank to grant the default (National) scope."),
    )
    is_primary = models.BooleanField(
        _("Primary role"),
        default=False,
        help_text=_("Each user may designate at most one primary active role."),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.ACTIVE,
        db_index=True,
    )
    effective_from = models.DateTimeField(
        _("Effective from"), default=timezone.now, db_index=True
    )
    expires_at = models.DateTimeField(_("Expires at"), null=True, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="role_assignments_made",
        verbose_name=_("Assigned by"),
    )
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("User Role Assignment")
        verbose_name_plural = _("User Role Assignments")
        ordering = ("user", "role", "-created_at")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["user", "role", "access_scope"],
                condition=models.Q(status=AssignmentStatus.ACTIVE),
                name="unique_active_role_assignment",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_primary=True, status=AssignmentStatus.ACTIVE),
                name="unique_primary_role_per_user",
            ),
        ]

    def __str__(self) -> str:
        scope = self.access_scope.name if self.access_scope else "National"
        return f"{self.user.email} - {self.role.name} ({scope})"

    def is_active_now(self) -> bool:
        """Whether the assignment is currently active and effective."""
        now = timezone.now()
        return (
            self.status == AssignmentStatus.ACTIVE
            and self.effective_from <= now
            and (self.expires_at is None or self.expires_at > now)
        )

    def is_expired(self) -> bool:
        return bool(self.expires_at and self.expires_at <= timezone.now())
