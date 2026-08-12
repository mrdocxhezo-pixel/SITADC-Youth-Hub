"""Permission tests for the ``reviews`` app (Phase 21)."""

from apps.rbac.authorization import user_has_permission
from apps.rbac.seed_data import ALL_PERMISSION_CODES
from apps.reviews import permissions

from .base import ReviewBaseTestCase


class ReviewPermissionCatalogueTests(ReviewBaseTestCase):
    def test_all_review_codes_registered_in_catalogue(self):
        codes = [
            permissions.VIEW,
            permissions.CREATE,
            permissions.ASSIGN,
            permissions.ACCEPT,
            permissions.START,
            permissions.COMMENT,
            permissions.RESOLVE_COMMENT,
            permissions.UPDATE_CHECKLIST,
            permissions.DECIDE,
            permissions.APPROVE,
            permissions.REJECT,
            permissions.RETURN_FOR_CORRECTION,
            permissions.ESCALATE,
            permissions.DELEGATE,
            permissions.SIGN,
            permissions.MANAGE_CHECKLISTS,
            permissions.MANAGE_SLA,
            permissions.MANAGE_CONFIGURATION,
        ]
        for code in codes:
            with self.subTest(code=code):
                self.assertIn(code, ALL_PERMISSION_CODES)


class ReviewRolePermissionTests(ReviewBaseTestCase):
    def test_officer_holds_operational_set(self):
        self.assign_role(self.other, "project-officer")
        for code in [
            permissions.VIEW,
            permissions.ACCEPT,
            permissions.START,
            permissions.COMMENT,
            permissions.RESOLVE_COMMENT,
            permissions.UPDATE_CHECKLIST,
            permissions.ESCALATE,
            permissions.DELEGATE,
            permissions.SIGN,
        ]:
            with self.subTest(code=code):
                self.assertTrue(user_has_permission(self.other, code))
        self.assertFalse(user_has_permission(self.other, permissions.APPROVE))
        self.assertFalse(user_has_permission(self.other, permissions.REJECT))
        self.assertFalse(user_has_permission(self.other, permissions.MANAGE))

    def test_coordinator_holds_reviewer_set_without_manage(self):
        self.assign_role(self.other, "district-coordinator")
        for code in [
            permissions.VIEW,
            permissions.CREATE,
            permissions.ASSIGN,
            permissions.ACCEPT,
            permissions.START,
            permissions.COMMENT,
            permissions.DECIDE,
            permissions.APPROVE,
            permissions.REJECT,
            permissions.RETURN_FOR_CORRECTION,
            permissions.ESCALATE,
            permissions.DELEGATE,
            permissions.SIGN,
            permissions.UPDATE_CHECKLIST,
            permissions.MANAGE_CHECKLISTS,
            permissions.MANAGE_SLA,
            permissions.MANAGE_CONFIGURATION,
        ]:
            with self.subTest(code=code):
                self.assertTrue(user_has_permission(self.other, code))
        self.assertFalse(user_has_permission(self.other, permissions.MANAGE))

    def test_board_member_read_only_plus_decisions(self):
        self.assign_role(self.other, "board-member")
        self.assertTrue(user_has_permission(self.other, permissions.VIEW))
        self.assertTrue(user_has_permission(self.other, permissions.APPROVE))
        self.assertTrue(user_has_permission(self.other, permissions.REJECT))
        self.assertFalse(user_has_permission(self.other, permissions.MANAGE_CHECKLISTS))
        self.assertFalse(user_has_permission(self.other, permissions.MANAGE_SLA))

    def test_leadership_holds_full_access(self):
        self.assign_role(self.other, "executive-director")
        self.assertTrue(user_has_permission(self.other, permissions.MANAGE))
        self.assertTrue(user_has_permission(self.other, permissions.DECIDE))

    def test_unassigned_user_denied(self):
        self.assertFalse(user_has_permission(self.other, permissions.VIEW))
        self.assertFalse(user_has_permission(self.other, permissions.COMMENT))

    def test_superuser_allowed(self):
        self.assertTrue(user_has_permission(self.admin, permissions.MANAGE))


class ReviewPermissionHelperTests(ReviewBaseTestCase):
    def test_helpers_gate_by_role(self):
        self.assign_role(self.other, "district-coordinator")
        self.assertTrue(permissions.can_view_reviews(self.other))
        self.assertTrue(permissions.can_assign_reviewer(self.other))
        self.assertTrue(permissions.can_make_decision(self.other))
        self.assertTrue(permissions.can_approve_report(self.other))
        self.assertTrue(permissions.can_reject_report(self.other))
        self.assertTrue(permissions.can_return_for_correction(self.other))
        self.assertTrue(permissions.can_escalate_review(self.other))
        self.assertTrue(permissions.can_delegate_review(self.other))
        self.assertTrue(permissions.can_apply_signature(self.other))
        self.assertFalse(permissions.can_view_reviews(self.owner))
