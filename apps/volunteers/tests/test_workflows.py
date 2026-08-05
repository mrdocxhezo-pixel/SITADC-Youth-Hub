"""Lifecycle and reference integration tests for Volunteer Management."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.references.constants import ReferenceNumberStatus
from apps.references.models import GeneratedReferenceNumber
from apps.volunteers.constants import ApplicationStatus, VolunteerStatus
from apps.volunteers.services import (
    VolunteerApplicationWorkflowService,
    VolunteerProfileService,
    VolunteerRecruitmentService,
)

User = get_user_model()


class VolunteerWorkflowTests(TestCase):
    def setUp(self):
        self.actor = User.objects.create_superuser(
            email="volunteer-admin@example.com",
            username="volunteer-admin",
            first_name="Volunteer",
            last_name="Admin",
            password="Password123!",
        )
        self.volunteer_user = User.objects.create_user(
            email="candidate@example.com",
            username="candidate",
            first_name="Candidate",
            last_name="Person",
        )

    def test_profile_reference_is_confirmed_and_initial_status_is_audited(self):
        profile = VolunteerProfileService(user=self.actor).create_profile(
            user_account=self.volunteer_user
        )

        reference = GeneratedReferenceNumber.objects.get(
            reference_number=profile.reference_number
        )
        self.assertEqual(reference.status, ReferenceNumberStatus.ASSIGNED)
        self.assertEqual(reference.record_id, profile.pk)
        self.assertEqual(profile.status, VolunteerStatus.REGISTERED)
        self.assertEqual(profile.status_history.count(), 1)

    def test_mutating_service_fails_closed_without_actor(self):
        with self.assertRaises(PermissionDenied):
            VolunteerProfileService().create_profile(user_account=self.volunteer_user)

    def test_application_screening_interview_approval_and_onboarding(self):
        recruitment_service = VolunteerRecruitmentService(user=self.actor)
        campaign = recruitment_service.create_campaign(
            title="Community mobilizers",
            deadline=timezone.localdate() + timedelta(days=30),
            category="COMMUNITY",
            volunteer_type="PART_TIME",
            vacancies=2,
        )
        application = recruitment_service.submit_application(
            applicant_name="Candidate Person",
            email="candidate@example.com",
            phone="+260970000000",
            recruitment=campaign,
            category="COMMUNITY",
            volunteer_type="PART_TIME",
            consent_confirmed=True,
        )
        reference = GeneratedReferenceNumber.objects.get(
            reference_number=application.reference_number
        )
        self.assertEqual(reference.status, ReferenceNumberStatus.ASSIGNED)

        workflow = VolunteerApplicationWorkflowService(user=self.actor)
        workflow.review_application(
            application,
            ApplicationStatus.UNDER_SCREENING,
        )
        screening = workflow.complete_screening(
            application,
            identity_verified=True,
            references_checked=True,
            qualifications_verified=True,
            safeguarding_cleared=True,
            passed=True,
        )
        self.assertTrue(screening.passed)
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.SHORTLISTED)

        workflow.complete_interview(
            application,
            scheduled_datetime=timezone.now(),
            score=85,
            recommendation="Recommended",
            passed=True,
        )
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.INTERVIEWED)
        workflow.review_application(application, ApplicationStatus.APPROVED)
        profile = workflow.register_approved_application(
            application,
            self.volunteer_user,
        )
        onboarding = workflow.complete_onboarding(
            profile,
            orientation_completed=True,
            code_of_conduct_signed=True,
            safeguarding_agreed=True,
            confidentiality_signed=True,
            welcome_pack_issued=True,
            id_card_issued=True,
        )
        profile.refresh_from_db()
        self.assertTrue(onboarding.completed)
        self.assertEqual(profile.status, VolunteerStatus.ACTIVE)

    def test_application_requires_consent(self):
        with self.assertRaises(ValidationError):
            VolunteerRecruitmentService(user=self.actor).submit_application(
                applicant_name="No Consent",
                email="no-consent@example.com",
                phone="+260970000001",
                category="COMMUNITY",
                volunteer_type="PART_TIME",
                consent_confirmed=False,
            )

    def test_invalid_profile_transition_is_rejected(self):
        profile = VolunteerProfileService(user=self.actor).create_profile(
            user_account=self.volunteer_user
        )
        with self.assertRaises(ValidationError):
            VolunteerProfileService(user=self.actor).update_status(
                profile,
                VolunteerStatus.ALUMNI,
            )
