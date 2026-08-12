"""View tests for the ``reviews`` app (Phase 21)."""

from django.urls import reverse

from apps.reviews.models import ReviewComment, ReviewStatus

from .base import ReviewBaseTestCase


class ReviewDashboardViewTests(ReviewBaseTestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("reviews:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_dashboard_renders_for_permitted_user(self):
        self.assign_role(self.reviewer, "project-officer")
        self.client.force_login(self.reviewer)
        response = self.client.get(reverse("reviews:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reviews/dashboard.html")

    def test_dashboard_redirects_without_permission(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("reviews:dashboard"))
        self.assertRedirects(response, reverse("core:home"))


class ReviewListViewTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.assign_role(self.reviewer, "district-coordinator")
        self.client.force_login(self.reviewer)

    def test_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("reviews:list"))
        self.assertEqual(response.status_code, 302)

    def test_list_renders(self):
        self.make_assigned_review(reviewer=self.reviewer)
        response = self.client.get(reverse("reviews:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reviews/review_list.html")
        self.assertEqual(response.context["total_count"], 1)

    def test_list_filters_by_status(self):
        self.make_assigned_review(reviewer=self.reviewer)
        response = self.client.get(reverse("reviews:list"), {"status": "APPROVED"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_count"], 0)


class ReviewDetailViewTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review(reviewer=self.reviewer)
        self.assign_role(self.reviewer, "district-coordinator")
        self.client.force_login(self.reviewer)

    def test_detail_renders(self):
        response = self.client.get(
            reverse("reviews:detail", kwargs={"pk": self.review.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reviews/review_detail.html")

    def test_detail_requires_permission(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("reviews:detail", kwargs={"pk": self.review.pk})
        )
        self.assertEqual(response.status_code, 302)


class ReviewAssignViewTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_review()
        self.assign_role(self.reviewer, "district-coordinator")
        self.client.force_login(self.reviewer)

    def test_assign_reviewer(self):
        response = self.client.post(
            reverse("reviews:assign", kwargs={"pk": self.review.pk}),
            {
                "reviewer": str(self.reviewer.pk),
                "role": "PRIMARY",
                "notes": "Primary reviewer",
            },
        )
        self.assertRedirects(
            response, reverse("reviews:detail", kwargs={"pk": self.review.pk})
        )
        self.review.refresh_from_db()
        self.assertEqual(self.review.primary_reviewer, self.reviewer)
        self.assertTrue(
            self.review.assignments.filter(assigned_to=self.reviewer).exists()
        )

    def test_assign_denied_without_permission(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("reviews:assign", kwargs={"pk": self.review.pk}),
            {"reviewer": str(self.reviewer.pk), "role": "PRIMARY"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            self.review.assignments.filter(assigned_to=self.reviewer).exists()
        )


class ReviewStartViewTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review(reviewer=self.reviewer)
        self.assign_role(self.reviewer, "district-coordinator")
        self.client.force_login(self.reviewer)

    def test_start_review_sets_under_review(self):
        response = self.client.post(
            reverse("reviews:start", kwargs={"pk": self.review.pk})
        )
        self.assertRedirects(
            response, reverse("reviews:detail", kwargs={"pk": self.review.pk})
        )
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.UNDER_REVIEW)

    def test_start_review_denied_without_permission(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("reviews:start", kwargs={"pk": self.review.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.ASSIGNED)


class ReviewAcceptViewTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review(reviewer=self.reviewer)
        self.assign_role(self.reviewer, "project-officer")
        self.client.force_login(self.reviewer)

    def test_accept_review(self):
        response = self.client.post(
            reverse("reviews:accept", kwargs={"pk": self.review.pk})
        )
        self.assertRedirects(
            response, reverse("reviews:detail", kwargs={"pk": self.review.pk})
        )
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.ACCEPTED)

    def test_accept_review_denied_without_permission(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("reviews:accept", kwargs={"pk": self.review.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.ASSIGNED)


class ReviewCommentViewTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review(reviewer=self.reviewer)
        self.assign_role(self.reviewer, "project-officer")
        self.client.force_login(self.reviewer)

    def test_add_comment(self):
        response = self.client.post(
            reverse("reviews:comment", kwargs={"pk": self.review.pk}),
            {"body": "Please add more detail.", "comment_type": "GENERAL"},
        )
        self.assertRedirects(
            response, reverse("reviews:detail", kwargs={"pk": self.review.pk})
        )
        self.assertTrue(
            ReviewComment.objects.filter(
                review=self.review, author=self.reviewer
            ).exists()
        )

    def test_comment_denied_without_permission(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("reviews:comment", kwargs={"pk": self.review.pk}),
            {"body": "Nope", "comment_type": "GENERAL"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.review.comments.count(), 0)


class ReviewDecisionViewTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review(reviewer=self.reviewer)
        self.assign_role(self.reviewer, "district-coordinator")
        self.client.force_login(self.reviewer)

    def test_approve_decision(self):
        response = self.client.post(
            reverse("reviews:decision", kwargs={"pk": self.review.pk}),
            {
                "decision": "APPROVED",
                "reason": "All checks passed.",
                "conditions": "",
                "signature_data": self.reviewer.get_full_name(),
            },
        )
        self.assertRedirects(
            response, reverse("reviews:detail", kwargs={"pk": self.review.pk})
        )
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.APPROVED)
        self.assertTrue(self.review.decisions.exists())

    def test_decision_denied_without_permission(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("reviews:decision", kwargs={"pk": self.review.pk}),
            {"decision": "APPROVED", "reason": "Should be denied."},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.review.decisions.exists())


class ReviewEscalateViewTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review(reviewer=self.reviewer)
        self.assign_role(self.reviewer, "district-coordinator")
        self.client.force_login(self.reviewer)

    def test_escalate_review(self):
        response = self.client.post(
            reverse("reviews:escalate", kwargs={"pk": self.review.pk}),
            {"trigger": "GOVERNANCE", "reason": "Needs board input."},
        )
        self.assertRedirects(
            response, reverse("reviews:detail", kwargs={"pk": self.review.pk})
        )
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.ESCALATED)

    def test_escalate_denied_without_permission(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("reviews:escalate", kwargs={"pk": self.review.pk}),
            {"trigger": "CUSTOM", "reason": "Denied."},
        )
        self.assertEqual(response.status_code, 302)
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.ASSIGNED)


class ReviewDelegateViewTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review(reviewer=self.reviewer)
        self.assign_role(self.reviewer, "district-coordinator")
        self.client.force_login(self.reviewer)

    def test_delegate_review(self):
        response = self.client.post(
            reverse("reviews:delegate", kwargs={"pk": self.review.pk}),
            {
                "delegated_to": str(self.secondary.pk),
                "reason": "Out of office.",
                "expires_at": "",
                "notes": "Please continue review.",
            },
        )
        self.assertRedirects(
            response, reverse("reviews:detail", kwargs={"pk": self.review.pk})
        )
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.DELEGATED)
        self.assertTrue(
            self.review.assignments.filter(assigned_to=self.secondary).exists()
        )

    def test_delegate_denied_without_permission(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("reviews:delegate", kwargs={"pk": self.review.pk}),
            {
                "delegated_to": str(self.secondary.pk),
                "reason": "Denied.",
                "expires_at": "",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.ASSIGNED)


class ReviewChecklistViewTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_review(checklist=self.checklist)
        self.assign_role(self.reviewer, "project-officer")
        self.client.force_login(self.reviewer)
        self.response_obj = self.review.checklist_responses.first()

    def test_update_checklist_item(self):
        response = self.client.post(
            reverse("reviews:checklist_update", kwargs={"pk": self.review.pk}),
            {
                "response_id": str(self.response_obj.pk),
                "is_completed": "on",
                "score": "4",
                "notes": "Verified.",
            },
        )
        self.assertRedirects(
            response, reverse("reviews:detail", kwargs={"pk": self.review.pk})
        )
        self.response_obj.refresh_from_db()
        self.assertTrue(self.response_obj.is_completed)
        self.assertEqual(self.response_obj.score, 4)

    def test_checklist_update_denied_without_permission(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("reviews:checklist_update", kwargs={"pk": self.review.pk}),
            {
                "response_id": str(self.response_obj.pk),
                "is_completed": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.response_obj.refresh_from_db()
        self.assertFalse(self.response_obj.is_completed)


class ReviewSLADashboardViewTests(ReviewBaseTestCase):
    def test_sla_dashboard_requires_login(self):
        response = self.client.get(reverse("reviews:sla_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_sla_dashboard_renders_for_permitted_user(self):
        self.assign_role(self.reviewer, "district-coordinator")
        self.client.force_login(self.reviewer)
        response = self.client.get(reverse("reviews:sla_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reviews/sla_dashboard.html")
