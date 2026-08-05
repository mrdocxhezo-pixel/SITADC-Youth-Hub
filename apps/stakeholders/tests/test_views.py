"""Stakeholder page, form, and URL integration tests."""

from datetime import date, timedelta
from uuid import uuid4

from django.urls import resolve, reverse
from django.utils import timezone

from apps.stakeholders.constants import (
    ConfidentialityLevel,
    DueDiligenceStatus,
    ReferenceDataKind,
    StakeholderEntityType,
)
from apps.stakeholders.forms import (
    AgreementTransitionForm,
    StakeholderArchiveForm,
    StakeholderForm,
)
from apps.stakeholders.models import Stakeholder, StakeholderDueDiligence

from .base import StakeholderTestCase


class StakeholderPageTests(StakeholderTestCase):
    def setUp(self):
        super().setUp()
        self.stakeholder = self.create_stakeholder(
            legal_name="Visible Youth Partner",
            confidentiality=ConfidentialityLevel.DIRECTORY,
        )
        self.grant_permissions(
            self.viewer,
            "partners.view_directory",
            "partners.view_profile",
            "partners.analytics",
        )
        self.client.force_login(self.viewer)

    def test_dashboard_renders_scoped_metrics(self):
        response = self.client.get(reverse("stakeholders:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stakeholders/dashboard.html")
        self.assertEqual(response.context["metrics"]["total"], 1)

    def test_directory_renders_search_filters_and_results(self):
        response = self.client.get(
            reverse("stakeholders:directory"), {"q": "Youth", "view": "cards"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stakeholders/directory.html")
        self.assertContains(response, "Visible Youth Partner")
        self.assertEqual(response.context["display_mode"], "cards")

    def test_profile_renders_authorized_record(self):
        response = self.client.get(
            reverse("stakeholders:profile", kwargs={"pk": self.stakeholder.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stakeholders/profile.html")
        self.assertContains(response, self.stakeholder.reference_number)
        self.assertContains(response, "Visible Youth Partner")

    def test_profile_shows_archive_action_to_manager(self):
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse("stakeholders:profile", kwargs={"pk": self.stakeholder.pk})
        )

        self.assertContains(
            response,
            reverse("stakeholders:archive", kwargs={"pk": self.stakeholder.pk}),
        )


class StakeholderFormTests(StakeholderTestCase):
    def test_profile_form_limits_each_taxonomy_to_its_kind(self):
        form = StakeholderForm()
        expected = {
            "categories": ReferenceDataKind.CATEGORY,
            "relationship_type": ReferenceDataKind.TYPE,
            "classification": ReferenceDataKind.CLASSIFICATION,
            "ownership_type": ReferenceDataKind.OWNERSHIP_TYPE,
            "priority": ReferenceDataKind.PRIORITY,
            "relationship_level": ReferenceDataKind.RELATIONSHIP_LEVEL,
            "sectors": ReferenceDataKind.SECTOR,
            "focus_areas": ReferenceDataKind.FOCUS_AREA,
            "sdgs": ReferenceDataKind.SDG,
        }
        for field_name, kind in expected.items():
            with self.subTest(field=field_name):
                self.assertFalse(
                    form.fields[field_name].queryset.exclude(kind=kind).exists()
                )

    def test_profile_form_rejects_future_establishment(self):
        form = StakeholderForm(
            data={
                "entity_type": StakeholderEntityType.ORGANIZATION,
                "legal_name": "Invalid Form Partner",
                "date_established": timezone.localdate() + timedelta(days=1),
                "confidentiality": ConfidentialityLevel.INTERNAL,
                "specialization_data": "{}",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("date_established", form.errors)

    def test_profile_form_rejects_reversed_relationship_dates(self):
        form = StakeholderForm(
            data={
                "entity_type": StakeholderEntityType.ORGANIZATION,
                "legal_name": "Reversed Dates Partner",
                "relationship_start_date": date(2026, 8, 2),
                "relationship_end_date": date(2026, 8, 1),
                "confidentiality": ConfidentialityLevel.INTERNAL,
                "specialization_data": "{}",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("relationship_end_date", form.errors)

    def test_archive_form_contains_only_required_reason_workflow_field(self):
        form = StakeholderArchiveForm()
        self.assertEqual(set(form.fields), {"reason"})
        self.assertTrue(form.fields["reason"].required)

    def test_agreement_transition_form_validates_after_choices_are_populated(self):
        agreement = self.create_agreement()
        form = AgreementTransitionForm(
            data={"new_status": "UNDER_REVIEW", "reason": ""},
            agreement=agreement,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["new_status"], "UNDER_REVIEW")

    def test_create_view_uses_service_and_redirects_to_profile(self):
        creator = self.create_user("creator")
        self.grant_permissions(creator, "partners.create", "partners.view")
        self.client.force_login(creator)
        response = self.client.post(
            reverse("stakeholders:create"),
            {
                "entity_type": StakeholderEntityType.ORGANIZATION,
                "legal_name": "Created From Form",
                "confidentiality": ConfidentialityLevel.INTERNAL,
                "specialization_data": "{}",
            },
        )
        stakeholder = Stakeholder.objects.get(legal_name="Created From Form")
        self.assertRedirects(
            response,
            reverse("stakeholders:profile", kwargs={"pk": stakeholder.pk}),
            fetch_redirect_response=False,
        )

    def test_due_diligence_view_accepts_completed_status(self):
        stakeholder = self.create_stakeholder()
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("stakeholders:due_diligence", kwargs={"pk": stakeholder.pk}),
            {
                "review_date": "2026-08-02",
                "expiry_date": "2027-08-02",
                "status": DueDiligenceStatus.PASSED,
                "checks": '{"registration": "passed"}',
                "missing_information": "[]",
                "findings": "No material findings.",
                "recommendation": "Proceed.",
            },
        )

        self.assertRedirects(
            response,
            reverse("stakeholders:due_diligence", kwargs={"pk": stakeholder.pk}),
            fetch_redirect_response=False,
        )
        review = StakeholderDueDiligence.objects.get(stakeholder=stakeholder)
        self.assertEqual(review.status, DueDiligenceStatus.PASSED)
        self.assertEqual(review.reviewed_by, self.manager)
        self.assertIsNotNone(review.completed_at)


class StakeholderRouteTests(StakeholderTestCase):
    def test_all_named_routes_reverse_to_stakeholder_views(self):
        stakeholder_pk = uuid4()
        related_pk = uuid4()
        routes = {
            "dashboard": {},
            "dashboard_alt": {},
            "directory": {},
            "partners": {},
            "donors": {},
            "sponsors": {},
            "government": {},
            "community": {},
            "mapping_matrix": {},
            "create": {},
            "profile": {"pk": stakeholder_pk},
            "edit": {"pk": stakeholder_pk},
            "status": {"pk": stakeholder_pk},
            "archive": {"pk": stakeholder_pk},
            "restore": {"pk": stakeholder_pk},
            "contacts": {"pk": stakeholder_pk},
            "contact_primary": {"contact_pk": related_pk},
            "contact_deactivate": {"contact_pk": related_pk},
            "assessments": {"pk": stakeholder_pk},
            "engagement_plans": {"pk": stakeholder_pk},
            "engagements": {"pk": stakeholder_pk},
            "engagement_complete": {"engagement_pk": related_pk},
            "communications": {"pk": stakeholder_pk},
            "commitments": {"pk": stakeholder_pk},
            "commitment_progress": {"commitment_pk": related_pk},
            "contributions": {"pk": stakeholder_pk},
            "contribution_verify": {"contribution_pk": related_pk},
            "agreements": {"pk": stakeholder_pk},
            "agreement_transition": {"agreement_pk": related_pk},
            "agreement_version_add": {"agreement_pk": related_pk},
            "agreement_version_download": {"version_pk": related_pk},
            "renewal_request": {"agreement_pk": related_pk},
            "renewal_decision": {"renewal_pk": related_pk},
            "due_diligence": {"pk": stakeholder_pk},
            "risks": {"pk": stakeholder_pk},
            "performance": {"pk": stakeholder_pk},
            "performance_finalize": {"review_pk": related_pk},
            "actions": {"pk": stakeholder_pk},
            "action_status": {"action_pk": related_pk},
            "notes": {"pk": stakeholder_pk},
            "note_version_add": {"note_pk": related_pk},
            "note_finalize": {"note_pk": related_pk},
            "documents": {"pk": stakeholder_pk},
            "document_download": {"document_pk": related_pk},
            "document_archive": {"document_pk": related_pk},
            "reports": {},
            "register_export": {},
        }
        for route_name, kwargs in routes.items():
            with self.subTest(route=route_name):
                path = reverse(f"stakeholders:{route_name}", kwargs=kwargs)
                self.assertTrue(resolve(path).view_name.startswith("stakeholders:"))
