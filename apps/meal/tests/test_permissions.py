"""Permission helper and confidentiality-aware selector tests."""

from django.contrib.auth.models import AnonymousUser

from apps.meal.models import Complaint, Indicator
from apps.meal.permissions import (
    user_can_manage_meal,
    user_can_view_confidential,
    user_can_view_meal,
)
from apps.meal.selectors import meal_queryset, visible_complaints, visible_feedback

from .base import MEALTestCase


class PermissionHelperTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.viewer_with_perm = self.create_user("viewer_with_perm")
        self.grant_permissions(self.viewer_with_perm, "meal.view")

    def test_user_can_view_meal(self):
        self.assertTrue(user_can_view_meal(self.manager))
        self.assertTrue(user_can_view_meal(self.viewer_with_perm))
        self.assertFalse(user_can_view_meal(self.outsider))

    def test_user_can_manage_meal(self):
        self.assertTrue(user_can_manage_meal(self.manager))
        self.assertFalse(user_can_manage_meal(self.viewer))

    def test_view_confidential_requires_flag(self):
        self.assertTrue(user_can_view_confidential(self.manager))
        self.assertFalse(user_can_view_confidential(self.viewer_with_perm))
        confidential_viewer = self.create_user("confidential_viewer")
        self.grant_permissions(
            confidential_viewer, "meal.view", "meal.view_confidential"
        )
        self.assertTrue(user_can_view_confidential(confidential_viewer))


class SelectorTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.viewer = self.create_user("meal_viewer")
        self.confidential_viewer = self.create_user("meal_confidential_viewer")
        self.grant_permissions(self.viewer, "meal.view")
        self.grant_permissions(
            self.confidential_viewer, "meal.view", "meal.view_confidential"
        )
        self.visible_complaint = self.create_complaint(is_confidential=False)
        self.confidential_complaint = self.create_complaint(is_confidential=True)
        self.confidential_feedback = self.create_feedback(is_confidential=True)

    def test_meal_queryset_fail_closed(self):
        self.assertFalse(meal_queryset(self.outsider, Indicator).exists())
        self.assertEqual(meal_queryset(self.manager, Complaint).count(), 2)

    def test_unauthenticated_user_sees_nothing(self):
        anonymous = AnonymousUser()
        self.assertFalse(visible_complaints(anonymous).exists())

    def test_visible_complaints_hides_confidential(self):
        self.assertEqual(visible_complaints(self.viewer).count(), 1)
        self.assertNotIn(
            self.confidential_complaint.pk,
            list(visible_complaints(self.viewer).values_list("pk", flat=True)),
        )

    def test_confidential_visibility_with_permission(self):
        self.assertEqual(visible_complaints(self.confidential_viewer).count(), 2)
        self.assertEqual(visible_feedback(self.confidential_viewer).count(), 1)
        self.assertEqual(visible_feedback(self.viewer).count(), 0)
