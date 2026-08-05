"""
Permission constants and helpers for the membership management module.

Authorization is always enforced on the server; these helpers centralize the
permission checks used across views, services and templates.
"""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

MEMBERSHIP_VIEW = "membership.view"
MEMBERSHIP_CREATE = "membership.create"
MEMBERSHIP_UPDATE = "membership.update"
MEMBERSHIP_DELETE = "membership.delete"
MEMBERSHIP_SUBMIT = "membership.submit"
MEMBERSHIP_ARCHIVE = "membership.archive"
MEMBERSHIP_RESTORE = "membership.restore"
MEMBERSHIP_EXPORT = "membership.export"
MEMBERSHIP_ASSIGN = "membership.assign"
MEMBERSHIP_VERIFY = "membership.verify"
MEMBERSHIP_REVIEW = "membership.review"
MEMBERSHIP_APPROVE = "membership.approve"
MEMBERSHIP_REJECT = "membership.reject"
MEMBERSHIP_RENEW = "membership.renew"
MEMBERSHIP_SUSPEND = "membership.suspend"
MEMBERSHIP_TERMINATE = "membership.terminate"
MEMBERSHIP_TRANSFER = "membership.transfer"
MEMBERSHIP_WAIVE = "membership.waive"
MEMBERSHIP_RECORD_PAYMENT = "membership.record_payment"
MEMBERSHIP_VERIFY_PAYMENT = "membership.verify_payment"
MEMBERSHIP_ISSUE_CARD = "membership.issue_card"
MEMBERSHIP_VIEW_CONFIDENTIAL = "membership.view_confidential"
MEMBERSHIP_MANAGE_ATTENDANCE = "membership.manage_attendance"
MEMBERSHIP_MANAGE_PARTICIPATION = "membership.manage_participation"
MEMBERSHIP_MANAGE_LEAVE = "membership.manage_leave"
MEMBERSHIP_MANAGE_EXIT = "membership.manage_exit"
MEMBERSHIP_CONFIGURE = "membership.configure"
MEMBERSHIP_MANAGE = "membership.manage"

VIEW_PERMISSIONS: tuple[str, ...] = (MEMBERSHIP_VIEW,)
MANAGE_PERMISSIONS: tuple[str, ...] = (
    MEMBERSHIP_VIEW,
    MEMBERSHIP_CREATE,
    MEMBERSHIP_UPDATE,
    MEMBERSHIP_DELETE,
    MEMBERSHIP_SUBMIT,
    MEMBERSHIP_ARCHIVE,
    MEMBERSHIP_RESTORE,
    MEMBERSHIP_EXPORT,
    MEMBERSHIP_ASSIGN,
    MEMBERSHIP_VERIFY,
    MEMBERSHIP_REVIEW,
    MEMBERSHIP_APPROVE,
    MEMBERSHIP_REJECT,
    MEMBERSHIP_RENEW,
    MEMBERSHIP_SUSPEND,
    MEMBERSHIP_TERMINATE,
    MEMBERSHIP_TRANSFER,
    MEMBERSHIP_WAIVE,
    MEMBERSHIP_RECORD_PAYMENT,
    MEMBERSHIP_VERIFY_PAYMENT,
    MEMBERSHIP_ISSUE_CARD,
    MEMBERSHIP_VIEW_CONFIDENTIAL,
    MEMBERSHIP_MANAGE_ATTENDANCE,
    MEMBERSHIP_MANAGE_PARTICIPATION,
    MEMBERSHIP_MANAGE_LEAVE,
    MEMBERSHIP_MANAGE_EXIT,
    MEMBERSHIP_CONFIGURE,
    MEMBERSHIP_MANAGE,
)


def _or_manage(user, permission_code: str) -> bool:
    return user_has_permission(user, permission_code) or user_has_permission(
        user, MEMBERSHIP_MANAGE
    )


def user_can_view_members(user) -> bool:
    return _or_manage(user, MEMBERSHIP_VIEW)


def user_can_create_members(user) -> bool:
    return _or_manage(user, MEMBERSHIP_CREATE)


def user_can_update_members(user) -> bool:
    return _or_manage(user, MEMBERSHIP_UPDATE)


def user_can_approve(user) -> bool:
    return _or_manage(user, MEMBERSHIP_APPROVE)


def user_can_review(user) -> bool:
    return _or_manage(user, MEMBERSHIP_REVIEW)


def user_can_verify(user) -> bool:
    return _or_manage(user, MEMBERSHIP_VERIFY)


def user_can_renew(user) -> bool:
    return _or_manage(user, MEMBERSHIP_RENEW)


def user_can_manage_payments(user) -> bool:
    return _or_manage(user, MEMBERSHIP_RECORD_PAYMENT)


def user_can_issue_cards(user) -> bool:
    return _or_manage(user, MEMBERSHIP_ISSUE_CARD)


def user_can_view_confidential(user) -> bool:
    return _or_manage(user, MEMBERSHIP_VIEW_CONFIDENTIAL)


def user_can_manage_exit(user) -> bool:
    return _or_manage(user, MEMBERSHIP_MANAGE_EXIT)


def user_can_configure(user) -> bool:
    return _or_manage(user, MEMBERSHIP_CONFIGURE)
