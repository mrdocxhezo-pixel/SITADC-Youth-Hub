"""Model tests for the Leadership Management module."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.leadership.constants import (
    AppointmentStatus,
    AppointmentType,
    AttendanceStatus,
    AttendanceType,
    LeadershipLevel,
    LeadershipStatus,
    MentorshipStatus,
    ReviewCycle,
    ReviewStatus,
    SuccessionReadiness,
    SuccessionRisk,
)
from apps.leadership.models import (
    LeadershipAppointment,
    LeadershipAttendance,
    LeadershipProfile,
    MentorshipRecord,
    PerformanceReview,
    SuccessionPlan,
)
from apps.organizations.models import OrganizationLevel, OrganizationUnit, Position

User = get_user_model()


class LeadershipProfileModelTest(TestCase):
    """Tests for the LeadershipProfile model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="leader@sitadc.org",
            password="TestPass123!",
            first_name="John",
            last_name="Banda",
        )

    def test_profile_creation(self):
        """A leadership profile can be created with required fields."""
        profile = LeadershipProfile(
            user=self.user,
            reference_number="SITADC-LDR-2026-00001",
            leadership_level=LeadershipLevel.DIRECTORATE,
            status=LeadershipStatus.ACTIVE,
        )
        profile.full_clean()
        profile.save()
        self.assertEqual(profile.user, self.user)
        self.assertEqual(
            profile.reference_number,
            "SITADC-LDR-2026-00001",
        )
        self.assertEqual(
            profile.status,
            LeadershipStatus.ACTIVE,
        )

    def test_profile_str(self):
        """Profile __str__ includes user name and reference."""
        profile = LeadershipProfile.objects.create(
            user=self.user,
            reference_number="SITADC-LDR-2026-00002",
            leadership_level=LeadershipLevel.REGIONAL,
            status=LeadershipStatus.ACTIVE,
        )
        self.assertIn("SITADC-LDR-2026-00002", str(profile))

    def test_unique_reference_number(self):
        """Reference numbers must be unique."""
        LeadershipProfile.objects.create(
            user=self.user,
            reference_number="SITADC-LDR-2026-00003",
            leadership_level=LeadershipLevel.TEAM,
            status=LeadershipStatus.ACTIVE,
        )
        user2 = User.objects.create_user(
            email="leader2@sitadc.org",
            password="TestPass123!",
        )
        with self.assertRaises(ValidationError):
            LeadershipProfile.objects.create(
                user=user2,
                reference_number="SITADC-LDR-2026-00003",
                leadership_level=LeadershipLevel.TEAM,
                status=LeadershipStatus.ACTIVE,
            )

    def test_one_profile_per_user(self):
        """Each user may only have one leadership profile."""
        LeadershipProfile.objects.create(
            user=self.user,
            reference_number="SITADC-LDR-2026-00004",
            leadership_level=LeadershipLevel.COMMUNITY,
            status=LeadershipStatus.ACTIVE,
        )
        with self.assertRaises(ValidationError):
            LeadershipProfile.objects.create(
                user=self.user,
                reference_number="SITADC-LDR-2026-00005",
                leadership_level=LeadershipLevel.TEAM,
                status=LeadershipStatus.ACTIVE,
            )

    def test_is_currently_active(self):
        """is_currently_active returns True for ACTIVE status."""
        profile = LeadershipProfile.objects.create(
            user=self.user,
            reference_number="SITADC-LDR-2026-00006",
            leadership_level=LeadershipLevel.DIRECTORATE,
            status=LeadershipStatus.ACTIVE,
        )
        self.assertTrue(profile.is_currently_active)

    def test_is_not_currently_active_when_archived(self):
        """is_currently_active returns False for ARCHIVED."""
        profile = LeadershipProfile.objects.create(
            user=self.user,
            reference_number="SITADC-LDR-2026-00007",
            leadership_level=LeadershipLevel.DIRECTORATE,
            status=LeadershipStatus.ARCHIVED,
        )
        self.assertFalse(profile.is_currently_active)

    def test_supervisor_not_self(self):
        """A leader cannot be their own supervisor."""
        profile = LeadershipProfile(
            user=self.user,
            reference_number="SITADC-LDR-2026-00008",
            leadership_level=LeadershipLevel.DIRECTORATE,
            status=LeadershipStatus.ACTIVE,
        )
        profile.save()
        profile.supervisor = profile
        with self.assertRaises(ValidationError):
            profile.full_clean()


class LeadershipAppointmentModelTest(TestCase):
    """Tests for the LeadershipAppointment model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="appointee@sitadc.org",
            password="TestPass123!",
            first_name="Jane",
            last_name="Mwale",
        )
        self.profile = LeadershipProfile.objects.create(
            user=self.user,
            reference_number="SITADC-LDR-2026-00010",
            leadership_level=LeadershipLevel.DIRECTORATE,
            status=LeadershipStatus.ACTIVE,
        )
        self.level = OrganizationLevel.objects.create(
            name="Test Level",
            code="TEST",
            sort_order=1,
        )
        self.unit = OrganizationUnit.objects.create(
            name="Test Unit",
            unit_type="DEPARTMENT",
            level=self.level,
        )
        self.position = Position.objects.create(
            title="Director",
            organizational_unit=self.unit,
        )

    def test_appointment_creation(self):
        """An appointment can be created for a profile."""
        appt = LeadershipAppointment.objects.create(
            profile=self.profile,
            reference_number="SITADC-APT-2026-00001",
            appointment_type=AppointmentType.PERMANENT,
            status=AppointmentStatus.DRAFT,
            position=self.position,
            organizational_unit=self.unit,
        )
        self.assertEqual(appt.profile, self.profile)
        self.assertEqual(appt.status, AppointmentStatus.DRAFT)

    def test_appointment_linked_to_profile(self):
        """Appointments are accessible via profile relation."""
        LeadershipAppointment.objects.create(
            profile=self.profile,
            reference_number="SITADC-APT-2026-00002",
            appointment_type=AppointmentType.ACTING,
            status=AppointmentStatus.ACTIVE,
            position=self.position,
            organizational_unit=self.unit,
        )
        self.assertEqual(self.profile.appointments.count(), 1)

    def test_current_appointment_property(self):
        """current_appointment returns the active appointment."""
        LeadershipAppointment.objects.create(
            profile=self.profile,
            reference_number="SITADC-APT-2026-00003",
            appointment_type=AppointmentType.PERMANENT,
            status=AppointmentStatus.ACTIVE,
            position=self.position,
            organizational_unit=self.unit,
        )
        self.assertIsNotNone(self.profile.current_appointment)


class LeadershipAttendanceModelTest(TestCase):
    """Tests for the LeadershipAttendance model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="attend@sitadc.org",
            password="TestPass123!",
        )
        self.profile = LeadershipProfile.objects.create(
            user=self.user,
            reference_number="SITADC-LDR-2026-00020",
            leadership_level=LeadershipLevel.TEAM,
            status=LeadershipStatus.ACTIVE,
        )

    def test_attendance_creation(self):
        """An attendance record can be created."""
        record = LeadershipAttendance.objects.create(
            profile=self.profile,
            attendance_type=AttendanceType.MEETING,
            attendance_date="2026-08-01",
            activity_name="Monthly Leadership Meeting",
            status=AttendanceStatus.PRESENT,
        )
        self.assertEqual(record.profile, self.profile)
        self.assertEqual(record.status, AttendanceStatus.PRESENT)


class PerformanceReviewModelTest(TestCase):
    """Tests for the PerformanceReview model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="reviewer@sitadc.org",
            password="TestPass123!",
        )
        self.reviewer_user = User.objects.create_user(
            email="supervisor@sitadc.org",
            password="TestPass123!",
        )
        self.profile = LeadershipProfile.objects.create(
            user=self.user,
            reference_number="SITADC-LDR-2026-00030",
            leadership_level=LeadershipLevel.DEPARTMENT,
            status=LeadershipStatus.ACTIVE,
        )
        self.reviewer = LeadershipProfile.objects.create(
            user=self.reviewer_user,
            reference_number="SITADC-LDR-2026-00031",
            leadership_level=LeadershipLevel.DIRECTORATE,
            status=LeadershipStatus.ACTIVE,
        )

    def test_review_creation(self):
        """A performance review can be created."""
        review = PerformanceReview.objects.create(
            profile=self.profile,
            reviewer=self.reviewer.user,
            review_cycle=ReviewCycle.ANNUAL,
            period_start="2026-01-01",
            period_end="2026-06-30",
            status=ReviewStatus.DRAFT,
        )
        self.assertEqual(review.profile, self.profile)
        self.assertEqual(review.reviewer, self.reviewer.user)


class MentorshipModelTest(TestCase):
    """Tests for the MentorshipRecord model."""

    def setUp(self):
        self.mentor_user = User.objects.create_user(
            email="mentor@sitadc.org",
            password="TestPass123!",
        )
        self.mentee_user = User.objects.create_user(
            email="mentee@sitadc.org",
            password="TestPass123!",
        )
        self.mentor = LeadershipProfile.objects.create(
            user=self.mentor_user,
            reference_number="SITADC-LDR-2026-00040",
            leadership_level=LeadershipLevel.DIRECTORATE,
            status=LeadershipStatus.ACTIVE,
        )
        self.mentee = LeadershipProfile.objects.create(
            user=self.mentee_user,
            reference_number="SITADC-LDR-2026-00041",
            leadership_level=LeadershipLevel.TEAM,
            status=LeadershipStatus.ACTIVE,
        )

    def test_mentorship_creation(self):
        """A mentorship record can be created."""
        record = MentorshipRecord.objects.create(
            mentor=self.mentor.user,
            mentee=self.mentee,
            start_date="2026-01-01",
            status=MentorshipStatus.ACTIVE,
        )
        self.assertEqual(record.mentor, self.mentor.user)
        self.assertEqual(record.mentee, self.mentee)

    def test_self_mentorship_prevented(self):
        """A leader cannot mentor themselves."""
        with self.assertRaises(ValidationError):
            record = MentorshipRecord(
                mentor=self.mentor.user,
                mentee=self.mentor,
                start_date="2026-01-01",
                status=MentorshipStatus.ACTIVE,
            )
            record.full_clean()


class SuccessionPlanModelTest(TestCase):
    """Tests for the SuccessionPlan model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="holder@sitadc.org",
            password="TestPass123!",
        )
        self.profile = LeadershipProfile.objects.create(
            user=self.user,
            reference_number="SITADC-LDR-2026-00050",
            leadership_level=LeadershipLevel.DIRECTORATE,
            status=LeadershipStatus.ACTIVE,
        )

    def test_succession_plan_creation(self):
        """A succession plan can be created."""
        level = OrganizationLevel.objects.create(
            name="HQ Level",
            code="HQ",
            sort_order=1,
        )
        position = Position.objects.create(
            title="Executive Director",
            organizational_unit=OrganizationUnit.objects.create(
                name="HQ", unit_type="DEPARTMENT", level=level
            ),
        )
        plan = SuccessionPlan.objects.create(
            position=position,
            current_holder=self.profile,
            readiness_level=SuccessionReadiness.READY,
            risk=SuccessionRisk.MEDIUM,
            is_active=True,
        )
        self.assertTrue(plan.is_active)
        self.assertEqual(
            plan.readiness_level,
            SuccessionReadiness.READY,
        )
