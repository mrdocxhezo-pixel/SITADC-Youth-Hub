"""Permissions for report instances (Phase 20 — Report Management).

The RBAC system defined in ``apps.rbac`` provides a ``has_permission``
helper that checks a user's groups and scoped permissions.  Each view
calls the appropriate check before proceeding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.rbac.authorization import user_has_permission

if TYPE_CHECKING:
    from django.http import HttpRequest

    from .models import Report

# Permission codenames (must match entries in the RBAC seed data)
CREATE = "report_instances.create"
VIEW = "report_instances.view"
VIEW_OWN = "report_instances.view_own"
VIEW_ALL = "report_instances.view_all"
UPDATE = "report_instances.update"
UPDATE_OWN = "report_instances.update_own"
DELETE = "report_instances.delete"
SUBMIT = "report_instances.submit"
SUBMIT_OWN = "report_instances.submit_own"
WITHDRAW = "report_instances.withdraw"
RESUBMIT = "report_instances.resubmit"
VALIDATE = "report_instances.validate"
APPROVE = "report_instances.approve"
REJECT = "report_instances.reject"
ARCHIVE = "report_instances.archive"
RESTORE = "report_instances.restore"
EXPORT = "report_instances.export"
ASSIGN = "report_instances.assign"
COMMENT = "report_instances.comment"
COMMENT_INTERNAL = "report_instances.comment_internal"
UPLOAD_EVIDENCE = "report_instances.upload_evidence"
VERIFY_EVIDENCE = "report_instances.verify_evidence"
UPLOAD_ATTACHMENT = "report_instances.upload_attachment"
VIEW_TIMELINE = "report_instances.view_timeline"
VIEW_VALIDATION = "report_instances.view_validation"
MANAGE_REMINDERS = "report_instances.manage_reminders"


def check_permission(
    request: HttpRequest,
    codename: str,
    obj: Report | None = None,
) -> bool:
    """Central permission check used by views.

    ``obj`` is optional — some permissions are object-level (e.g., update_own).
    Returns ``True`` if the user has the permission, otherwise ``False``.
    """
    return user_has_permission(request.user, codename)


def can_create_report(request: HttpRequest) -> bool:
    """Check if the user can create reports."""
    return check_permission(request, CREATE)


def can_view_report(request: HttpRequest, report: Report) -> bool:
    """Check if the user can view a specific report."""
    if check_permission(request, VIEW_ALL):
        return True
    if check_permission(request, VIEW_OWN) and report.owner_id == request.user.id:
        return True
    if report.assigned_reviewer_id == request.user.id:
        return True
    return check_permission(request, VIEW, report)


def can_update_report(request: HttpRequest, report: Report) -> bool:
    """Check if the user can update a specific report."""
    if not report.is_editable:
        return False
    if check_permission(request, UPDATE):
        return True
    return bool(
        check_permission(request, UPDATE_OWN) and report.owner_id == request.user.id
    )


def can_submit_report(request: HttpRequest, report: Report) -> bool:
    """Check if the user can submit a specific report."""
    if check_permission(request, SUBMIT):
        return True
    return bool(
        check_permission(request, SUBMIT_OWN) and report.owner_id == request.user.id
    )


def can_withdraw_report(request: HttpRequest, report: Report) -> bool:
    """Check if the user can withdraw a specific report."""
    if not report.is_submitted:
        return False
    return not (
        report.owner_id != request.user.id and not check_permission(request, WITHDRAW)
    )


def can_validate_report(request: HttpRequest) -> bool:
    """Check if the user can run validation."""
    return check_permission(request, VALIDATE)


def can_approve_report(request: HttpRequest) -> bool:
    """Check if the user can approve reports."""
    return check_permission(request, APPROVE)


def can_reject_report(request: HttpRequest) -> bool:
    """Check if the user can reject reports."""
    return check_permission(request, REJECT)


def can_archive_report(request: HttpRequest) -> bool:
    """Check if the user can archive reports."""
    return check_permission(request, ARCHIVE)


def can_restore_report(request: HttpRequest) -> bool:
    """Check if the user can restore reports."""
    return check_permission(request, RESTORE)


def can_export_report(request: HttpRequest) -> bool:
    """Check if the user can export reports."""
    return check_permission(request, EXPORT)


def can_assign_report(request: HttpRequest) -> bool:
    """Check if the user can assign reviewers."""
    return check_permission(request, ASSIGN)


def can_comment(request: HttpRequest, is_internal: bool = False) -> bool:
    """Check if the user can comment on reports."""
    if is_internal:
        return check_permission(request, COMMENT_INTERNAL)
    return check_permission(request, COMMENT)


def can_upload_evidence(request: HttpRequest) -> bool:
    """Check if the user can upload evidence."""
    return check_permission(request, UPLOAD_EVIDENCE)


def can_verify_evidence(request: HttpRequest) -> bool:
    """Check if the user can verify evidence."""
    return check_permission(request, VERIFY_EVIDENCE)


def can_upload_attachment(request: HttpRequest) -> bool:
    """Check if the user can upload attachments."""
    return check_permission(request, UPLOAD_ATTACHMENT)


def can_delete_report(request: HttpRequest, report: Report) -> bool:
    """Check if the user can delete a specific report (only drafts)."""
    if not report.is_draft:
        return False
    if check_permission(request, DELETE):
        return True
    return False
