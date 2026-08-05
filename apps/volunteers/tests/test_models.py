"""
Model tests for volunteer management.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.volunteers.constants import VolunteerStatus
from apps.volunteers.models import (
    VolunteerApplication,
    VolunteerAssignment,
    VolunteerAttendance,
    VolunteerAuditRecord,
    VolunteerCategory,
    VolunteerProfile,
    VolunteerRecruitment,
    VolunteerType,
)

User = get_user_model()


class VolunteerModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="volunteer@example.com",
            username="volunteer",
            first_name="Jane",
            last_name="Doe",
        )
        self.category, _ = VolunteerCategory.objects.get_or_create(
            code="COMMUNITY", defaults={"name": "Community Volunteer"}
        )
        self.youth_category, _ = VolunteerCategory.objects.get_or_create(
            code="YOUTH", defaults={"name": "Youth Volunteer"}
        )
        self.type, _ = VolunteerType.objects.get_or_create(
            code="PART_TIME", defaults={"name": "Part-Time Volunteer"}
        )
        self.profile = VolunteerProfile.objects.create(
            user=self.user,
            reference_number="SITADC-VOL-2026-000001",
            category=self.category,
            volunteer_type=self.type,
            status=VolunteerStatus.ACTIVE,
        )

    def test_volunteer_profile_creation(self):
        self.assertEqual(str(self.profile), "Jane Doe (SITADC-VOL-2026-000001)")
        self.assertEqual(self.profile.category, self.category)
        self.assertEqual(self.profile.status, VolunteerStatus.ACTIVE)

    def test_taxonomy_models(self):
        self.assertEqual(self.category.code, "COMMUNITY")
        self.assertEqual(self.category.name, "Community Volunteer")
        self.assertEqual(self.type.name, "Part-Time Volunteer")
        self.assertIn("Category", str(VolunteerCategory._meta.verbose_name))

    def test_recruitment_and_application(self):
        recruitment = VolunteerRecruitment.objects.create(
            title="Youth Facilitators 2026",
            reference_number="SITADC-REC-2026-000001",
            category=self.youth_category,
            volunteer_type=self.type,
            application_deadline="2026-12-31",
        )
        app = VolunteerApplication.objects.create(
            recruitment=recruitment,
            reference_number="SITADC-APP-2026-000001",
            applicant_name="John Smith",
            email="john@example.com",
            phone_number="+260970000000",
            category=self.youth_category,
            volunteer_type=self.type,
        )
        self.assertEqual(app.applicant_name, "John Smith")
        self.assertEqual(app.recruitment, recruitment)
        self.assertEqual(app.category, self.youth_category)

    def test_assignment(self):
        assignment = VolunteerAssignment.objects.create(
            profile=self.profile,
            title="Community Facilitator",
            program_name="Youth Digital Literacy",
            start_date="2026-01-01",
        )
        self.assertTrue(assignment.is_active)
        self.assertEqual(assignment.profile, self.profile)

    def test_attendance(self):
        att = VolunteerAttendance.objects.create(
            profile=self.profile,
            date="2026-02-01",
            activity_name="Digital Skills Workshop",
            hours_served=4.5,
        )
        self.assertEqual(float(att.hours_served), 4.5)

    def test_audit_record_immutability(self):
        audit = VolunteerAuditRecord.objects.create(
            entity_type="VolunteerProfile",
            entity_id=str(self.profile.id),
            action="CREATED",
        )
        with self.assertRaises(ValidationError):
            audit.notes = "Modified notes"
            audit.save()

        with self.assertRaises(ValidationError):
            audit.delete()

        with self.assertRaises(ValidationError):
            VolunteerAuditRecord.objects.filter(pk=audit.pk).delete()
