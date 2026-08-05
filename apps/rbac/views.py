"""
Views for the RBAC framework (roles, permissions and access scopes).

Every protected view enforces server-side authorization through the RBAC
decorators or mixins; hiding navigation/buttons is never treated as a
security control.
"""

from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from . import selectors
from .authorization import can_manage_role
from .decorators import any_permission_required, permission_required
from .forms import RoleCloneForm, RoleForm, UserRoleAssignmentForm
from .models import Role, RoleHistory, UserRoleAssignment
from .services import (
    ActivateRoleService,
    ArchiveRoleService,
    AssignRoleService,
    CloneRoleService,
    CreateRoleService,
    DeactivateRoleService,
    DeleteRoleService,
    RestoreRoleService,
    RevokeRoleService,
    SetRolePermissionsService,
    UpdateRoleService,
)

logger = logging.getLogger(__name__)

ROLE_MANAGE_PERMISSION = "administration.manage"
ROLE_VIEW_PERMISSION = "administration.view"


@login_required
def access_denied_view(request):
    """Friendly access-denied page shown when authorization fails."""
    return render(request, "rbac/access_denied.html", status=403)


@permission_required(ROLE_VIEW_PERMISSION)
def role_list_view(request):
    """List all non-deleted roles with usage statistics."""
    roles = selectors.get_roles().annotate(
        assignment_count=Count(
            "user_assignments",
            filter=Q(user_assignments__status="ACTIVE"),
        )
    )
    return render(request, "rbac/role_list.html", {"roles": roles})


@permission_required(ROLE_VIEW_PERMISSION)
def role_detail_view(request, slug):
    """Show a role, its permissions, assignments and audit history."""
    role = get_object_or_404(Role.objects.all(), slug=slug)
    permissions = selectors.get_role_permissions(role)
    assignments = (
        UserRoleAssignment.objects.filter(role=role)
        .select_related("user", "access_scope", "assigned_by")
        .order_by("-created_at")
    )
    history = selectors.get_role_history(role)
    return render(
        request,
        "rbac/role_detail.html",
        {
            "role": role,
            "permissions": permissions,
            "assignments": assignments,
            "history": history,
        },
    )


@permission_required(ROLE_MANAGE_PERMISSION)
def role_create_view(request):
    """Create a new role."""
    if request.method == "POST":
        form = RoleForm(request.POST)
        if form.is_valid():
            try:
                CreateRoleService(user=request.user).execute(
                    name=form.cleaned_data["name"],
                    description=form.cleaned_data["description"],
                    priority=form.cleaned_data["priority"],
                    permissions=list(form.cleaned_data.get("permission_codes") or []),
                )
                messages.success(request, _("Role created successfully."))
                return redirect("core:role_list")
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = RoleForm()

    return render(request, "rbac/role_form.html", {"form": form, "mode": "create"})


@permission_required(ROLE_MANAGE_PERMISSION)
def role_update_view(request, slug):
    """Update an existing role's metadata."""
    role = get_object_or_404(Role.objects.all(), slug=slug)
    if not can_manage_role(request.user, role):
        messages.error(request, _("You are not authorized to manage this role."))
        return redirect("core:role_detail", slug=role.slug)

    if request.method == "POST":
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            try:
                role = UpdateRoleService(user=request.user).execute(
                    role=role,
                    name=form.cleaned_data["name"],
                    description=form.cleaned_data["description"],
                    priority=form.cleaned_data["priority"],
                )
                selected = list(form.cleaned_data.get("permission_codes") or [])
                role = SetRolePermissionsService(user=request.user).execute(
                    role=role, permissions=selected
                )
                messages.success(request, _("Role updated successfully."))
                return redirect("core:role_detail", slug=role.slug)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = RoleForm(instance=role)

    return render(
        request, "rbac/role_form.html", {"form": form, "mode": "update", "role": role}
    )


@permission_required(ROLE_MANAGE_PERMISSION)
@require_http_methods(["POST"])
def role_permissions_view(request, slug):
    """Replace the permission set of a role."""
    role = get_object_or_404(Role.objects.all(), slug=slug)
    if not can_manage_role(request.user, role):
        messages.error(request, _("You are not authorized to manage this role."))
        return redirect("core:role_detail", slug=role.slug)

    codes = request.POST.getlist("permission_codes")
    try:
        SetRolePermissionsService(user=request.user).execute(
            role=role, permissions=codes
        )
        messages.success(request, _("Role permissions updated successfully."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:role_detail", slug=role.slug)


def _role_action_view(request, slug, service, success_message, action_name):
    """Shared handler for POST-only role lifecycle actions."""
    role = get_object_or_404(Role.objects.all(), slug=slug)
    if not can_manage_role(request.user, role):
        messages.error(request, _("You are not authorized to manage this role."))
        return redirect("core:role_detail", slug=role.slug)
    try:
        service(user=request.user).execute(role=role)
        messages.success(request, success_message)
        logger.info(f"{action_name} role {role.slug} by {request.user}")
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:role_detail", slug=role.slug)


@permission_required(ROLE_MANAGE_PERMISSION)
@require_http_methods(["POST"])
def role_archive_view(request, slug):
    return _role_action_view(
        request, slug, ArchiveRoleService, _("Role archived successfully."), "Archived"
    )


@permission_required(ROLE_MANAGE_PERMISSION)
@require_http_methods(["POST"])
def role_restore_view(request, slug):
    return _role_action_view(
        request, slug, RestoreRoleService, _("Role restored successfully."), "Restored"
    )


@permission_required(ROLE_MANAGE_PERMISSION)
@require_http_methods(["POST"])
def role_activate_view(request, slug):
    return _role_action_view(
        request,
        slug,
        ActivateRoleService,
        _("Role activated successfully."),
        "Activated",
    )


@permission_required(ROLE_MANAGE_PERMISSION)
@require_http_methods(["POST"])
def role_deactivate_view(request, slug):
    return _role_action_view(
        request,
        slug,
        DeactivateRoleService,
        _("Role deactivated successfully."),
        "Deactivated",
    )


@permission_required(ROLE_MANAGE_PERMISSION)
@require_http_methods(["POST"])
def role_clone_view(request, slug):
    """Clone a role under a new name."""
    source = get_object_or_404(Role.objects.all(), slug=slug)
    if not can_manage_role(request.user, source):
        messages.error(request, _("You are not authorized to manage this role."))
        return redirect("core:role_detail", slug=source.slug)
    form = RoleCloneForm(request.POST)
    if form.is_valid():
        try:
            CloneRoleService(user=request.user).execute(
                source_role=source, new_name=form.cleaned_data["new_name"]
            )
            messages.success(request, _("Role cloned successfully."))
        except ValidationError as e:
            messages.error(request, e.message)
    else:
        messages.error(request, _("Please provide a name for the cloned role."))
    return redirect("core:role_detail", slug=source.slug)


@permission_required(ROLE_MANAGE_PERMISSION)
@require_http_methods(["POST"])
def role_delete_view(request, slug):
    """Soft-delete a role."""
    role = get_object_or_404(Role.objects.all(), slug=slug)
    if not can_manage_role(request.user, role):
        messages.error(request, _("You are not authorized to manage this role."))
        return redirect("core:role_detail", slug=role.slug)
    try:
        DeleteRoleService(user=request.user).execute(role=role)
        messages.success(request, _("Role deleted successfully."))
        return redirect("core:role_list")
    except ValidationError as e:
        messages.error(request, e.message)
        return redirect("core:role_detail", slug=role.slug)


@permission_required(ROLE_VIEW_PERMISSION)
def role_assignments_view(request, slug):
    """List the users currently assigned to a role."""
    role = get_object_or_404(Role.objects.all(), slug=slug)
    assignments = (
        UserRoleAssignment.objects.filter(role=role)
        .select_related("user", "access_scope", "assigned_by")
        .order_by("-created_at")
    )
    return render(
        request,
        "rbac/role_assignments.html",
        {
            "role": role,
            "assignments": assignments,
            "active_users": selectors.get_active_users(),
            "active_scopes": selectors.get_active_access_scopes(),
        },
    )


@permission_required(ROLE_MANAGE_PERMISSION)
@require_http_methods(["POST"])
def role_assignment_create_view(request, slug):
    """Assign a role to a user."""
    role = get_object_or_404(Role.objects.all(), slug=slug)
    if not can_manage_role(request.user, role):
        messages.error(request, _("You are not authorized to manage this role."))
        return redirect("core:role_detail", slug=role.slug)
    form = UserRoleAssignmentForm(request.POST)
    if form.is_valid():
        try:
            AssignRoleService(user=request.user).execute(
                user=form.cleaned_data["user"],
                role=form.cleaned_data["role"],
                access_scope=form.cleaned_data.get("access_scope"),
                is_primary=form.cleaned_data.get("is_primary", False),
                effective_from=form.cleaned_data.get("effective_from"),
                expires_at=form.cleaned_data.get("expires_at"),
                notes=form.cleaned_data.get("notes", ""),
            )
            messages.success(request, _("Role assigned successfully."))
        except ValidationError as e:
            messages.error(request, e.message)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect("core:role_assignments", slug=role.slug)


@permission_required(ROLE_MANAGE_PERMISSION)
@require_http_methods(["POST"])
def role_assignment_revoke_view(request, assignment_id):
    """Revoke an active role assignment."""
    assignment = get_object_or_404(UserRoleAssignment, id=assignment_id)
    role_slug = assignment.role.slug
    try:
        RevokeRoleService(user=request.user).execute(assignment=assignment)
        messages.success(request, _("Role assignment revoked successfully."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:role_assignments", slug=role_slug)


@permission_required(ROLE_VIEW_PERMISSION)
def permission_list_view(request):
    """List permission categories and their permissions."""
    categories = selectors.get_permission_categories()
    permission_map = {}
    for category in categories:
        permission_map[category.code] = selectors.get_permissions_by_category(category)
    return render(
        request,
        "rbac/permission_list.html",
        {"categories": categories, "permission_map": permission_map},
    )


@permission_required(ROLE_VIEW_PERMISSION)
def access_scope_list_view(request):
    """List hierarchical organizational access scopes."""
    scopes = selectors.get_access_scopes()
    return render(request, "rbac/access_scope_list.html", {"scopes": scopes})


@permission_required(ROLE_VIEW_PERMISSION)
def role_history_view(request, slug):
    """Show the immutable audit history of a role."""
    role = get_object_or_404(Role.objects.all(), slug=slug)
    history = selectors.get_role_history(role)
    return render(request, "rbac/role_history.html", {"role": role, "history": history})


@any_permission_required(ROLE_VIEW_PERMISSION)
def rbac_index_view(request):
    """Landing index for the roles and permissions area."""
    return render(
        request,
        "rbac/index.html",
        {
            "role_count": Role.objects.all().count(),
            "active_role_count": selectors.get_active_roles().count(),
            "scope_count": selectors.get_access_scopes().count(),
            "category_count": selectors.get_permission_categories().count(),
            "history_count": RoleHistory.objects.count(),
        },
    )
