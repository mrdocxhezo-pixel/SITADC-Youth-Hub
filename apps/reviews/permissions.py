"""Permission checks for Review and Approval module (Phase 21).

Uses the central RBAC engine defined in ``apps.rbac.authorization`` so every
view applies the same ``module.action`` permission codes seeded in the RBAC
catalogue (see ``apps/rbac/seed_data.py``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.rbac.authorization import user_has_permission

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model

    User = get_user_model()

# Permission codenames (must match entries in the RBAC seed data).
MANAGE = "reviews.manage"
VIEW = "reviews.view"
CREATE = "reviews.create"
ASSIGN = "reviews.assign"
ACCEPT = "reviews.accept"
START = "reviews.start"
COMMENT = "reviews.comment"
RESOLVE_COMMENT = "reviews.resolve_comment"
DECIDE = "reviews.decide"
APPROVE = "reviews.approve"
REJECT = "reviews.reject"
RETURN_FOR_CORRECTION = "reviews.return_for_correction"
ESCALATE = "reviews.escalate"
DELEGATE = "reviews.delegate"
SIGN = "reviews.sign"
UPDATE_CHECKLIST = "reviews.update_checklist"
MANAGE_CHECKLISTS = "reviews.manage_checklists"
MANAGE_SLA = "reviews.manage_sla"
MANAGE_CONFIGURATION = "reviews.manage_configuration"


def can_view_reviews(user: User) -> bool:
    """Can the user view reviews?"""
    return user_has_permission(user, VIEW)


def can_create_review(user: User) -> bool:
    """Can the user create reviews?"""
    return user_has_permission(user, CREATE)


def can_assign_reviewer(user: User) -> bool:
    """Can the user assign reviewers?"""
    return user_has_permission(user, ASSIGN)


def can_start_review(user: User) -> bool:
    """Can the user start a review?"""
    return user_has_permission(user, START)


def can_accept_review(user: User) -> bool:
    """Can the user accept a review assignment?"""
    return user_has_permission(user, ACCEPT)


def can_add_comment(user: User) -> bool:
    """Can the user add comments?"""
    return user_has_permission(user, COMMENT)


def can_resolve_comment(user: User) -> bool:
    """Can the user resolve comments?"""
    return user_has_permission(user, RESOLVE_COMMENT)


def can_update_checklist(user: User) -> bool:
    """Can the user complete checklist items?"""
    return user_has_permission(user, UPDATE_CHECKLIST)


def can_make_decision(user: User) -> bool:
    """Can the user make review decisions?"""
    return user_has_permission(user, DECIDE)


def can_approve_report(user: User) -> bool:
    """Can the user approve reports?"""
    return user_has_permission(user, APPROVE)


def can_reject_report(user: User) -> bool:
    """Can the user reject reports?"""
    return user_has_permission(user, REJECT)


def can_return_for_correction(user: User) -> bool:
    """Can the user return reports for correction?"""
    return user_has_permission(user, RETURN_FOR_CORRECTION)


def can_escalate_review(user: User) -> bool:
    """Can the user escalate reviews?"""
    return user_has_permission(user, ESCALATE)


def can_delegate_review(user: User) -> bool:
    """Can the user delegate reviews?"""
    return user_has_permission(user, DELEGATE)


def can_apply_signature(user: User) -> bool:
    """Can the user apply digital signatures?"""
    return user_has_permission(user, SIGN)


def can_manage_checklists(user: User) -> bool:
    """Can the user manage review checklists?"""
    return user_has_permission(user, MANAGE_CHECKLISTS)


def can_manage_sla(user: User) -> bool:
    """Can the user manage SLA configurations?"""
    return user_has_permission(user, MANAGE_SLA)


def can_manage_configuration(user: User) -> bool:
    """Can the user manage review configurations?"""
    return user_has_permission(user, MANAGE_CONFIGURATION)
