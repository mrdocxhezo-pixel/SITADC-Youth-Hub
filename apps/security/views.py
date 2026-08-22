"""
Views for the Security Hardening framework.

Every protected view enforces server-side authorization through the RBAC
decorators or mixins; hiding navigation/buttons is never treated as a
security control.
"""

from __future__ import annotations

import logging
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Avg
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)

from apps.rbac.decorators import permission_required, any_permission_required
from apps.rbac.mixins import PermissionRequiredMixin

from . import selectors
from .constants import (
    SecurityConfidentialityLevel,
    SecurityStatus,
    MFAMethod,
    SessionStatus,
    AccessReviewStatus,
    AccessReviewDecision,
)
from .forms import (
    EnterpriseSecurityPolicyForm,
    IdentityForm,
    ServiceIdentityForm,
    OrganizationalIdentityForm,
    PermissionForm,
    RolePermissionForm,
    IdentityRoleForm,
    PermissionGrantForm,
    RoleHierarchyForm,
    AccessReviewForm,
    AccessReviewItemForm,
    MFAEnrollmentForm,
    MFAVerificationForm,
    APICredentialForm,
    APIAccessTokenForm,
    DatabaseSecurityPolicyForm,
    SecureFileForm,
)
from .models import (
    EnterpriseSecurityPolicy,
    Identity,
    ServiceIdentity,
    OrganizationalIdentity,
    Permission,
    RolePermission,
    IdentityRole,
    LoginAttempt,
    AccessReview,
    AccessReviewItem,
    RoleHierarchy,
    PermissionGrant,
    Session,
    MFAEnrollment,
    MFAVerificationAttempt,
    APICredential,
    APIAccessToken,
    APIRateLimit,
    DatabaseSecurityPolicy,
    DatabaseAccessLog,
    SecureFile,
)
from .services import (
    CreateSecurityPolicyService,
    UpdateSecurityPolicyService,
    CreateIdentityService,
    CreateServiceIdentityService,
    CreateOrganizationalIdentityService,
    UpdateIdentityService,
    CreatePermissionService,
    GrantRolePermissionService,
    RevokeRolePermissionService,
    AssignIdentityRoleService,
    RevokeIdentityRoleService,
    GrantPermissionService,
    RevokePermissionService,
    CreateRoleHierarchyService,
    RemoveRoleHierarchyService,
    CreateAccessReviewService,
    StartAccessReviewService,
    ReviewAccessItemService,
    CompleteAccessReviewService,
    CreateSessionService,
    TerminateSessionService,
    ExtendSessionService,
    CreateMFAEnrollmentService,
    VerifyMFAService,
    CreateAPICredentialService,
    RotateAPICredentialService,
    RevokeAPICredentialService,
    CreateAPIAccessTokenService,
    RevokeAPIAccessTokenService,
    CreateDatabaseSecurityPolicyService,
    CreateSecureFileService,
)

logger = logging.getLogger(__name__)

# Permission constants
SECURITY_VIEW_PERMISSION = "security.view"
SECURITY_MANAGE_PERMISSION = "security.manage"
SECURITY_ADMIN_PERMISSION = "security.admin"


def security_access_denied_view(request):
    """Friendly access-denied page shown when authorization fails."""
    return render(request, "security/access_denied.html", status=403)


# ============================================================
# Security Dashboard
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def security_dashboard_view(request):
    """Main security dashboard."""
    stats = selectors.get_security_dashboard_stats()

    # Recent security events
    recent_failed_logins = selectors.get_failed_login_attempts(days=7)[:10]
    recent_suspicious = selectors.get_suspicious_login_attempts(days=7)[:10]
    pending_reviews = selectors.get_pending_access_reviews()[:5]
    overdue_reviews = selectors.get_overdue_access_reviews()[:5]

    context = {
        "stats": stats,
        "recent_failed_logins": recent_failed_logins,
        "recent_suspicious": recent_suspicious,
        "pending_reviews": pending_reviews,
        "overdue_reviews": overdue_reviews,
    }
    return render(request, "security/dashboard.html", context)


@permission_required(SECURITY_VIEW_PERMISSION)
def security_dashboard_api(request):
    """API endpoint for security dashboard data."""
    stats = selectors.get_security_dashboard_stats()
    return JsonResponse(stats)


# ============================================================
# Security Policies
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def security_policy_list_view(request):
    """List all security policies."""
    policy_type = request.GET.get("type")
    is_active = request.GET.get("is_active")

    policies = selectors.get_security_policies(
        policy_type=policy_type,
        is_active=is_active.lower() == "true" if is_active is not None else None,
    )

    context = {
        "policies": policies,
        "policy_types": EnterpriseSecurityPolicy.POLICY_TYPE_CHOICES,
        "current_type": policy_type,
        "current_active": is_active,
    }
    return render(request, "security/policy_list.html", context)


@permission_required(SECURITY_VIEW_PERMISSION)
def security_policy_detail_view(request, slug):
    """Show a security policy."""
    policy = get_object_or_404(EnterpriseSecurityPolicy, slug=slug)
    return render(request, "security/policy_detail.html", {"policy": policy})


@permission_required(SECURITY_MANAGE_PERMISSION)
def security_policy_create_view(request):
    """Create a new security policy."""
    if request.method == "POST":
        form = EnterpriseSecurityPolicyForm(request.POST)
        if form.is_valid():
            try:
                service = CreateSecurityPolicyService(user=request.user)
                service.execute(**form.cleaned_data)
                messages.success(request, _("Security policy created successfully."))
                return redirect("security:policy_list")
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = EnterpriseSecurityPolicyForm()

    return render(request, "security/policy_form.html", {"form": form, "title": _("Create Security Policy")})


@permission_required(SECURITY_MANAGE_PERMISSION)
def security_policy_update_view(request, slug):
    """Update a security policy."""
    policy = get_object_or_404(EnterpriseSecurityPolicy, slug=slug)

    if request.method == "POST":
        form = EnterpriseSecurityPolicyForm(request.POST, instance=policy)
        if form.is_valid():
            try:
                service = UpdateSecurityPolicyService(user=request.user)
                service.execute(policy=policy, **form.cleaned_data)
                messages.success(request, _("Security policy updated successfully."))
                return redirect("security:policy_detail", slug=policy.slug)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = EnterpriseSecurityPolicyForm(instance=policy)

    return render(request, "security/policy_form.html", {"form": form, "policy": policy, "title": _("Update Security Policy")})


# ============================================================
# Identities
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def identity_list_view(request):
    """List all identities."""
    identity_type = request.GET.get("type")
    status = request.GET.get("status")

    identities = selectors.get_identities(
        identity_type=identity_type,
        status=status,
    )

    context = {
        "identities": identities,
        "identity_types": Identity.IDENTITY_TYPE_CHOICES,
        "statuses": SecurityStatus.CHOICES,
        "current_type": identity_type,
        "current_status": status,
    }
    return render(request, "security/identity_list.html", context)


@permission_required(SECURITY_VIEW_PERMISSION)
def identity_detail_view(request, pk):
    """Show an identity with related data."""
    identity = get_object_or_404(Identity.objects.select_related("owner").prefetch_related("managed_by"), pk=pk)

    # Get related data
    identity_roles = selectors.get_active_identity_roles(identity)
    permission_grants = selectors.get_active_permission_grants(identity)
    mfa_enrollments = selectors.get_mfa_enrollments(identity)
    sessions = selectors.get_active_sessions(identity)
    login_attempts = selectors.get_login_attempts(identity=identity, days=30)[:20]
    mfa_attempts = selectors.get_mfa_verification_attempts(identity=identity, days=30)[:20]
    api_credentials = selectors.get_valid_api_credentials(identity)
    secure_files = selectors.get_secure_files(owner=identity)[:10]

    # Risk score
    risk_score = selectors.get_identity_risk_score(identity)

    context = {
        "identity": identity,
        "identity_roles": identity_roles,
        "permission_grants": permission_grants,
        "mfa_enrollments": mfa_enrollments,
        "sessions": sessions,
        "login_attempts": login_attempts,
        "mfa_attempts": mfa_attempts,
        "api_credentials": api_credentials,
        "secure_files": secure_files,
        "risk_score": risk_score,
    }
    return render(request, "security/identity_detail.html", context)


@permission_required(SECURITY_MANAGE_PERMISSION)
def identity_create_view(request):
    """Create a new identity."""
    identity_type = request.GET.get("type", "user")

    if identity_type == "service":
        form_class = ServiceIdentityForm
        service = CreateServiceIdentityService
    elif identity_type == "organization":
        form_class = OrganizationalIdentityForm
        service = CreateOrganizationalIdentityService
    else:
        form_class = IdentityForm
        service = CreateIdentityService

    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            try:
                svc = service(user=request.user)
                svc.execute(**form.cleaned_data)
                messages.success(request, _("Identity created successfully."))
                return redirect("security:identity_list")
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = form_class()

    return render(request, "security/identity_form.html", {"form": form, "title": _("Create Identity"), "identity_type": identity_type})


@permission_required(SECURITY_MANAGE_PERMISSION)
def identity_update_view(request, pk):
    """Update an identity."""
    identity = get_object_or_404(Identity, pk=pk)

    if identity.identity_type == "service":
        form_class = ServiceIdentityForm
    elif identity.identity_type == "organization":
        form_class = OrganizationalIdentityForm
    else:
        form_class = IdentityForm

    if request.method == "POST":
        form = form_class(request.POST, instance=identity)
        if form.is_valid():
            try:
                service = UpdateIdentityService(user=request.user)
                service.execute(identity=identity, **form.cleaned_data)
                messages.success(request, _("Identity updated successfully."))
                return redirect("security:identity_detail", pk=identity.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = form_class(instance=identity)

    return render(request, "security/identity_form.html", {"form": form, "identity": identity, "title": _("Update Identity")})


# ============================================================
# Permissions
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def permission_list_view(request):
    """List all permissions."""
    module = request.GET.get("module")

    permissions = selectors.get_permissions(module=module)

    modules = Permission.objects.values_list("module", flat=True).distinct().order_by("module")

    context = {
        "permissions": permissions,
        "modules": modules,
        "current_module": module,
    }
    return render(request, "security/permission_list.html", context)


@permission_required(SECURITY_MANAGE_PERMISSION)
def permission_create_view(request):
    """Create a new permission."""
    if request.method == "POST":
        form = PermissionForm(request.POST)
        if form.is_valid():
            try:
                service = CreatePermissionService(user=request.user)
                service.execute(**form.cleaned_data)
                messages.success(request, _("Permission created successfully."))
                return redirect("security:permission_list")
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = PermissionForm()

    return render(request, "security/permission_form.html", {"form": form, "title": _("Create Permission")})


# ============================================================
# Role Permissions
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def role_permission_list_view(request, role_slug):
    """List permissions for a role."""
    role = get_object_or_404(Role, slug=role_slug)
    role_permissions = selectors.get_role_permissions(role)

    return render(request, "security/role_permission_list.html", {
        "role": role,
        "role_permissions": role_permissions,
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def role_permission_grant_view(request, role_slug):
    """Grant a permission to a role."""
    role = get_object_or_404(Role, slug=role_slug)

    if request.method == "POST":
        form = RolePermissionForm(request.POST)
        form.fields["role"].initial = role
        form.fields["role"].widget = forms.HiddenInput()
        if form.is_valid():
            try:
                service = GrantRolePermissionService(user=request.user)
                service.execute(
                    role=role,
                    permission=form.cleaned_data["permission"],
                    expires_at=form.cleaned_data.get("expires_at"),
                    conditions=form.cleaned_data.get("conditions"),
                    justification=form.cleaned_data.get("justification"),
                )
                messages.success(request, _("Permission granted to role successfully."))
                return redirect("security:role_permissions", role_slug=role.slug)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = RolePermissionForm(initial={"role": role})
        form.fields["role"].widget = forms.HiddenInput()

    return render(request, "security/role_permission_form.html", {
        "form": form,
        "role": role,
        "title": _("Grant Permission to Role"),
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def role_permission_revoke_view(request, role_slug, permission_id):
    """Revoke a permission from a role."""
    role = get_object_or_404(Role, slug=role_slug)
    permission = get_object_or_404(Permission, pk=permission_id)

    if request.method == "POST":
        try:
            service = RevokeRolePermissionService(user=request.user)
            service.execute(role=role, permission=permission)
            messages.success(request, _("Permission revoked from role successfully."))
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect("security:role_permissions", role_slug=role.slug)

    return render(request, "security/role_permission_confirm_revoke.html", {
        "role": role,
        "permission": permission,
    })


# ============================================================
# Identity Roles
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def identity_role_list_view(request, identity_pk):
    """List roles for an identity."""
    identity = get_object_or_404(Identity, pk=identity_pk)
    identity_roles = selectors.get_active_identity_roles(identity)

    return render(request, "security/identity_role_list.html", {
        "identity": identity,
        "identity_roles": identity_roles,
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def identity_role_assign_view(request, identity_pk):
    """Assign a role to an identity."""
    identity = get_object_or_404(Identity, pk=identity_pk)

    if request.method == "POST":
        form = IdentityRoleForm(request.POST)
        form.fields["identity"].initial = identity
        form.fields["identity"].widget = forms.HiddenInput()
        if form.is_valid():
            try:
                service = AssignIdentityRoleService(user=request.user)
                service.execute(
                    identity=identity,
                    role=form.cleaned_data["role"],
                    expires_at=form.cleaned_data.get("expires_at"),
                    conditions=form.cleaned_data.get("conditions"),
                    justification=form.cleaned_data.get("justification"),
                )
                messages.success(request, _("Role assigned to identity successfully."))
                return redirect("security:identity_roles", identity_pk=identity.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = IdentityRoleForm(initial={"identity": identity})
        form.fields["identity"].widget = forms.HiddenInput()

    return render(request, "security/identity_role_form.html", {
        "form": form,
        "identity": identity,
        "title": _("Assign Role to Identity"),
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def identity_role_revoke_view(request, identity_pk, role_slug):
    """Revoke a role from an identity."""
    identity = get_object_or_404(Identity, pk=identity_pk)
    role = get_object_or_404(Role, slug=role_slug)

    if request.method == "POST":
        try:
            service = RevokeIdentityRoleService(user=request.user)
            service.execute(identity=identity, role=role)
            messages.success(request, _("Role revoked from identity successfully."))
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect("security:identity_roles", identity_pk=identity.pk)

    return render(request, "security/identity_role_confirm_revoke.html", {
        "identity": identity,
        "role": role,
    })


# ============================================================
# Permission Grants
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def permission_grant_list_view(request, identity_pk):
    """List direct permission grants for an identity."""
    identity = get_object_or_404(Identity, pk=identity_pk)
    grants = selectors.get_active_permission_grants(identity)

    return render(request, "security/permission_grant_list.html", {
        "identity": identity,
        "grants": grants,
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def permission_grant_create_view(request, identity_pk):
    """Grant a direct permission to an identity."""
    identity = get_object_or_404(Identity, pk=identity_pk)

    if request.method == "POST":
        form = PermissionGrantForm(request.POST)
        form.fields["identity"].initial = identity
        form.fields["identity"].widget = forms.HiddenInput()
        if form.is_valid():
            try:
                service = GrantPermissionService(user=request.user)
                service.execute(
                    identity=identity,
                    permission=form.cleaned_data["permission"],
                    expires_at=form.cleaned_data.get("expires_at"),
                    conditions=form.cleaned_data.get("conditions"),
                    justification=form.cleaned_data.get("justification"),
                )
                messages.success(request, _("Permission granted successfully."))
                return redirect("security:permission_grants", identity_pk=identity.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = PermissionGrantForm(initial={"identity": identity})
        form.fields["identity"].widget = forms.HiddenInput()

    return render(request, "security/permission_grant_form.html", {
        "form": form,
        "identity": identity,
        "title": _("Grant Permission"),
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def permission_grant_revoke_view(request, identity_pk, permission_id):
    """Revoke a direct permission from an identity."""
    identity = get_object_or_404(Identity, pk=identity_pk)
    permission = get_object_or_404(Permission, pk=permission_id)

    if request.method == "POST":
        try:
            service = RevokePermissionService(user=request.user)
            service.execute(identity=identity, permission=permission)
            messages.success(request, _("Permission revoked successfully."))
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect("security:permission_grants", identity_pk=identity.pk)

    return render(request, "security/permission_grant_confirm_revoke.html", {
        "identity": identity,
        "permission": permission,
    })


# ============================================================
# Role Hierarchy
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def role_hierarchy_list_view(request):
    """List role hierarchies."""
    hierarchies = selectors.get_role_hierarchy()

    return render(request, "security/role_hierarchy_list.html", {
        "hierarchies": hierarchies,
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def role_hierarchy_create_view(request):
    """Create a role hierarchy."""
    if request.method == "POST":
        form = RoleHierarchyForm(request.POST)
        if form.is_valid():
            try:
                service = CreateRoleHierarchyService(user=request.user)
                service.execute(
                    parent_role=form.cleaned_data["parent_role"],
                    child_role=form.cleaned_data["child_role"],
                    inherit_permissions=form.cleaned_data["inherit_permissions"],
                    inherit_role_permissions=form.cleaned_data["inherit_role_permissions"],
                    justification=form.cleaned_data.get("justification", ""),
                )
                messages.success(request, _("Role hierarchy created successfully."))
                return redirect("security:role_hierarchy_list")
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = RoleHierarchyForm()

    return render(request, "security/role_hierarchy_form.html", {
        "form": form,
        "title": _("Create Role Hierarchy"),
    })


# ============================================================
# Login Attempts
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def login_attempt_list_view(request):
    """List login attempts with filters."""
    identity_id = request.GET.get("identity")
    ip_address = request.GET.get("ip")
    outcome = request.GET.get("outcome")
    is_suspicious = request.GET.get("suspicious")
    days = int(request.GET.get("days", 30))

    identity = None
    if identity_id:
        identity = Identity.objects.filter(pk=identity_id).first()

    attempts = selectors.get_login_attempts(
        identity=identity,
        ip_address=ip_address,
        outcome=outcome,
        is_suspicious=is_suspicious.lower() == "true" if is_suspicious else None,
        days=days,
    )

    identities = Identity.objects.filter(status=SecurityStatus.ACTIVE).order_by("display_name")
    outcomes = LoginAttempt.ATTEMPT_OUTCOME_CHOICES

    context = {
        "attempts": attempts[:100],
        "identities": identities,
        "outcomes": outcomes,
        "current_identity": identity_id,
        "current_ip": ip_address,
        "current_outcome": outcome,
        "current_suspicious": is_suspicious,
        "current_days": days,
    }
    return render(request, "security/login_attempt_list.html", context)


@permission_required(SECURITY_VIEW_PERMISSION)
def login_attempt_detail_view(request, pk):
    """Show login attempt details."""
    attempt = get_object_or_404(LoginAttempt.objects.select_related("identity"), pk=pk)
    return render(request, "security/login_attempt_detail.html", {"attempt": attempt})


# ============================================================
# Access Reviews
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def access_review_list_view(request):
    """List access reviews."""
    review_type = request.GET.get("type")
    status = request.GET.get("status")

    reviews = selectors.get_access_reviews(
        review_type=review_type,
        status=status,
    )

    context = {
        "reviews": reviews,
        "review_types": AccessReview._meta.get_field("review_type").choices,
        "statuses": AccessReviewStatus.CHOICES,
        "current_type": review_type,
        "current_status": status,
    }
    return render(request, "security/access_review_list.html", context)


@permission_required(SECURITY_VIEW_PERMISSION)
def access_review_detail_view(request, pk):
    """Show access review details."""
    review = get_object_or_404(AccessReview.objects.select_related(
        "target_identity", "target_role", "target_permission", "lead_reviewer"
    ).prefetch_related("reviewers"), pk=pk)

    items = selectors.get_access_review_items(review)

    context = {
        "review": review,
        "items": items,
    }
    return render(request, "security/access_review_detail.html", context)


@permission_required(SECURITY_MANAGE_PERMISSION)
def access_review_create_view(request):
    """Create a new access review."""
    if request.method == "POST":
        form = AccessReviewForm(request.POST)
        if form.is_valid():
            try:
                service = CreateAccessReviewService(user=request.user)
                review = service.execute(**form.cleaned_data)
                messages.success(request, _("Access review created successfully."))
                return redirect("security:access_review_detail", pk=review.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = AccessReviewForm()

    return render(request, "security/access_review_form.html", {"form": form, "title": _("Create Access Review")})


@permission_required(SECURITY_MANAGE_PERMISSION)
def access_review_start_view(request, pk):
    """Start an access review (populate items)."""
    review = get_object_or_404(AccessReview, pk=pk)

    if request.method == "POST":
        try:
            service = StartAccessReviewService(user=request.user)
            service.execute(review=review)
            messages.success(request, _("Access review started successfully."))
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect("security:access_review_detail", pk=review.pk)

    return render(request, "security/access_review_confirm_start.html", {"review": review})


@permission_required(SECURITY_VIEW_PERMISSION)
def access_review_item_view(request, item_pk):
    """Review an access review item."""
    item = get_object_or_404(AccessReviewItem.objects.select_related(
        "access_review", "identity", "role", "permission", "identity_role", "reviewer"
    ), pk=item_pk)

    # Check if user is a reviewer
    if request.user not in item.access_review.reviewers.all() and request.user != item.access_review.lead_reviewer:
        return HttpResponseForbidden(_("You are not authorized to review this item."))

    if request.method == "POST":
        form = AccessReviewItemForm(request.POST, instance=item)
        if form.is_valid():
            try:
                service = ReviewAccessItemService(user=request.user)
                service.execute(
                    item=item,
                    decision=form.cleaned_data["decision"],
                    reviewer=request.user,
                    justification=form.cleaned_data.get("justification", ""),
                    new_value=form.cleaned_data.get("new_value"),
                    change_reason=form.cleaned_data.get("change_reason", ""),
                )
                messages.success(request, _("Review decision recorded."))
                return redirect("security:access_review_detail", pk=item.access_review.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = AccessReviewItemForm(instance=item)

    return render(request, "security/access_review_item_form.html", {
        "form": form,
        "item": item,
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def access_review_complete_view(request, pk):
    """Complete an access review."""
    review = get_object_or_404(AccessReview, pk=pk)

    if request.method == "POST":
        try:
            service = CompleteAccessReviewService(user=request.user)
            service.execute(review=review)
            messages.success(request, _("Access review completed successfully."))
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect("security:access_review_detail", pk=review.pk)

    return render(request, "security/access_review_confirm_complete.html", {"review": review})


# ============================================================
# Sessions
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def session_list_view(request):
    """List sessions with filters."""
    identity_id = request.GET.get("identity")
    status = request.GET.get("status")
    ip_address = request.GET.get("ip")

    identity = None
    if identity_id:
        identity = Identity.objects.filter(pk=identity_id).first()

    sessions = selectors.get_sessions(
        identity=identity,
        status=status,
        ip_address=ip_address,
    )

    identities = Identity.objects.filter(status=SecurityStatus.ACTIVE).order_by("display_name")

    context = {
        "sessions": sessions[:100],
        "identities": identities,
        "statuses": SessionStatus.CHOICES,
        "current_identity": identity_id,
        "current_status": status,
        "current_ip": ip_address,
    }
    return render(request, "security/session_list.html", context)


@permission_required(SECURITY_VIEW_PERMISSION)
def session_detail_view(request, pk):
    """Show session details."""
    session = get_object_or_404(Session.objects.select_related("identity"), pk=pk)
    return render(request, "security/session_detail.html", {"session": session})


@permission_required(SECURITY_MANAGE_PERMISSION)
def session_terminate_view(request, pk):
    """Terminate a session."""
    session = get_object_or_404(Session, pk=pk)

    if request.method == "POST":
        try:
            service = TerminateSessionService(user=request.user)
            service.execute(session=session, terminated_by=request.user, terminated_by_ip=request.META.get("REMOTE_ADDR"))
            messages.success(request, _("Session terminated successfully."))
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect("security:session_list")

    return render(request, "security/session_confirm_terminate.html", {"session": session})


@permission_required(SECURITY_MANAGE_PERMISSION)
def session_extend_view(request, pk):
    """Extend a session."""
    session = get_object_or_404(Session, pk=pk)

    if request.method == "POST":
        minutes = int(request.POST.get("minutes", 60))
        try:
            service = ExtendSessionService(user=request.user)
            service.execute(session=session, extension_minutes=minutes)
            messages.success(request, _("Session extended successfully."))
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect("security:session_detail", pk=session.pk)

    return render(request, "security/session_extend.html", {"session": session})


# ============================================================
# MFA
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def mfa_enrollment_list_view(request, identity_pk):
    """List MFA enrollments for an identity."""
    identity = get_object_or_404(Identity, pk=identity_pk)
    enrollments = selectors.get_mfa_enrollments(identity)

    return render(request, "security/mfa_enrollment_list.html", {
        "identity": identity,
        "enrollments": enrollments,
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def mfa_enrollment_create_view(request, identity_pk):
    """Create an MFA enrollment."""
    identity = get_object_or_404(Identity, pk=identity_pk)

    if request.method == "POST":
        form = MFAEnrollmentForm(request.POST)
        form.fields["identity"].initial = identity
        form.fields["identity"].widget = forms.HiddenInput()
        if form.is_valid():
            try:
                service = CreateMFAEnrollmentService(user=request.user)
                service.execute(
                    identity=identity,
                    method=form.cleaned_data["method"],
                    is_primary=form.cleaned_data["is_primary"],
                    is_backup=form.cleaned_data["is_backup"],
                    secret_key=form.cleaned_data.get("secret_key", ""),
                    phone_number=form.cleaned_data.get("phone_number", ""),
                    email_address=form.cleaned_data.get("email_address", ""),
                    name=form.cleaned_data.get("name", ""),
                    attributes=form.cleaned_data.get("attributes"),
                )
                messages.success(request, _("MFA enrollment created successfully."))
                return redirect("security:mfa_enrollments", identity_pk=identity.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = MFAEnrollmentForm(initial={"identity": identity})
        form.fields["identity"].widget = forms.HiddenInput()

    return render(request, "security/mfa_enrollment_form.html", {
        "form": form,
        "identity": identity,
        "title": _("Create MFA Enrollment"),
    })


@permission_required(SECURITY_VIEW_PERMISSION)
def mfa_verification_view(request):
    """Handle MFA verification (for login flow)."""
    # This would be called during login
    if request.method == "POST":
        form = MFAVerificationForm(request.POST)
        if form.is_valid():
            # In a real implementation, this would verify against the user's enrollments
            pass
    else:
        form = MFAVerificationForm()

    return render(request, "security/mfa_verification.html", {"form": form})


# ============================================================
# API Credentials
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def api_credential_list_view(request, identity_pk):
    """List API credentials for an identity."""
    identity = get_object_or_404(Identity, pk=identity_pk)
    credentials = selectors.get_valid_api_credentials(identity)

    return render(request, "security/api_credential_list.html", {
        "identity": identity,
        "credentials": credentials,
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def api_credential_create_view(request, identity_pk):
    """Create an API credential."""
    identity = get_object_or_404(Identity, pk=identity_pk)

    if request.method == "POST":
        form = APICredentialForm(request.POST)
        if form.is_valid():
            try:
                service = CreateAPICredentialService(user=request.user)
                service.execute(
                    identity=identity,
                    **form.cleaned_data,
                )
                messages.success(request, _("API credential created successfully."))
                return redirect("security:api_credentials", identity_pk=identity.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = APICredentialForm()

    return render(request, "security/api_credential_form.html", {
        "form": form,
        "identity": identity,
        "title": _("Create API Credential"),
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def api_credential_rotate_view(request, identity_pk, credential_pk):
    """Rotate an API credential."""
    identity = get_object_or_404(Identity, pk=identity_pk)
    credential = get_object_or_404(APICredential, pk=credential_pk, identity=identity)

    if request.method == "POST":
        new_key = request.POST.get("new_key") or None
        new_secret = request.POST.get("new_secret", "")
        try:
            service = RotateAPICredentialService(user=request.user)
            service.execute(credential=credential, new_key=new_key, new_secret=new_secret)
            messages.success(request, _("API credential rotated successfully."))
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect("security:api_credentials", identity_pk=identity.pk)

    return render(request, "security/api_credential_confirm_rotate.html", {
        "identity": identity,
        "credential": credential,
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def api_credential_revoke_view(request, identity_pk, credential_pk):
    """Revoke an API credential."""
    identity = get_object_or_404(Identity, pk=identity_pk)
    credential = get_object_or_404(APICredential, pk=credential_pk, identity=identity)

    if request.method == "POST":
        reason = request.POST.get("reason", "")
        try:
            service = RevokeAPICredentialService(user=request.user)
            service.execute(credential=credential, reason=reason)
            messages.success(request, _("API credential revoked successfully."))
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect("security:api_credentials", identity_pk=identity.pk)

    return render(request, "security/api_credential_confirm_revoke.html", {
        "identity": identity,
        "credential": credential,
    })


# ============================================================
# Database Security
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def database_policy_list_view(request):
    """List database security policies."""
    policies = selectors.get_database_security_policies()

    return render(request, "security/database_policy_list.html", {
        "policies": policies,
    })


@permission_required(SECURITY_MANAGE_PERMISSION)
def database_policy_create_view(request):
    """Create a database security policy."""
    if request.method == "POST":
        form = DatabaseSecurityPolicyForm(request.POST)
        if form.is_valid():
            try:
                service = CreateDatabaseSecurityPolicyService(user=request.user)
                service.execute(**form.cleaned_data)
                messages.success(request, _("Database security policy created successfully."))
                return redirect("security:database_policies")
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = DatabaseSecurityPolicyForm()

    return render(request, "security/database_policy_form.html", {
        "form": form,
        "title": _("Create Database Security Policy"),
    })


@permission_required(SECURITY_VIEW_PERMISSION)
def database_access_log_view(request, policy_pk):
    """View database access logs."""
    policy = get_object_or_404(DatabaseSecurityPolicy, pk=policy_pk)
    logs = selectors.get_database_access_logs(policy)

    return render(request, "security/database_access_log.html", {
        "policy": policy,
        "logs": logs[:100],
    })


# ============================================================
# Secure Files
# ============================================================

@permission_required(SECURITY_VIEW_PERMISSION)
def secure_file_list_view(request):
    """List secure files."""
    owner_id = request.GET.get("owner")
    confidentiality = request.GET.get("confidentiality")
    is_encrypted = request.GET.get("encrypted")

    owner = None
    if owner_id:
        owner = Identity.objects.filter(pk=owner_id).first()

    files = selectors.get_secure_files(
        owner=owner,
        confidentiality=confidentiality,
        is_encrypted=is_encrypted.lower() == "true" if is_encrypted else None,
    )

    identities = Identity.objects.filter(status=SecurityStatus.ACTIVE).order_by("display_name")
    confidentiality_levels = SecurityConfidentialityLevel.CHOICES

    context = {
        "files": files[:100],
        "identities": identities,
        "confidentiality_levels": confidentiality_levels,
        "current_owner": owner_id,
        "current_confidentiality": confidentiality,
        "current_encrypted": is_encrypted,
    }
    return render(request, "security/secure_file_list.html", context)


@permission_required(SECURITY_VIEW_PERMISSION)
def secure_file_detail_view(request, pk):
    """Show secure file details."""
    file = get_object_or_404(SecureFile.objects.select_related("owner", "uploaded_by").prefetch_related("allowed_identities", "allowed_roles"), pk=pk)
    return render(request, "security/secure_file_detail.html", {"file": file})


@permission_required(SECURITY_MANAGE_PERMISSION)
def secure_file_create_view(request):
    """Create a secure file record."""
    if request.method == "POST":
        form = SecureFileForm(request.POST)
        if form.is_valid():
            try:
                service = CreateSecureFileService(user=request.user)
                service.execute(**form.cleaned_data)
                messages.success(request, _("Secure file created successfully."))
                return redirect("security:secure_files")
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = SecureFileForm()

    return render(request, "security/secure_file_form.html", {
        "form": form,
        "title": _("Create Secure File"),
    })