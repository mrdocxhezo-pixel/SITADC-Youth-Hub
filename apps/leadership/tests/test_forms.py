"""Tests for LeadershipProfileForm and leadership structure validation."""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.leadership.constants import LeadershipLevel, LeadershipStatus, TermStatus
from apps.leadership.forms import LeadershipProfileForm
from apps.leadership.models import LeadershipProfile
from apps.organizations.constants import UnitStatus, UnitType
from apps.organizations.models import OrganizationLevel, OrganizationUnit, Position

User = get_user_model()


class LeadershipProfileFormTests(TestCase):
    """Test LeadershipProfileForm dropdowns, validation, and editing."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_organization_structure", verbosity=0)
        call_command("seed_reference_schemes", verbosity=0)

        cls.user = User.objects.create_user(
            email="leader.test@sitadc.org",
            username="leadertest",
            first_name="Leader",
            last_name="Test",
            password="StrongPassword123!",
        )

        cls.dir_meal = OrganizationUnit.objects.get(identifier="DIR-MEAL")
        cls.dept_meal = OrganizationUnit.objects.get(identifier="DEPT-MEAL")
        cls.ptm_meo = OrganizationUnit.objects.get(identifier="PTM-MEO")

        cls.dir_fin = OrganizationUnit.objects.get(identifier="DIR-FIN-RES")
        cls.dept_fin = OrganizationUnit.objects.get(identifier="DEPT-FGRM")
        cls.ptm_fm = OrganizationUnit.objects.get(identifier="PTM-FM")

        cls.position = Position.objects.filter(status="ACTIVE").first()

    def test_form_labels_and_placeholders(self):
        """Form fields must have approved labels and placeholder values."""
        form = LeadershipProfileForm()

        self.assertEqual(str(form.fields["position"].label), "Position (Optional)")
        self.assertEqual(
            str(form.fields["organizational_unit"].label),
            "Organizational Unit (Optional)",
        )
        self.assertEqual(
            str(form.fields["directorate"].label), "Directorate (Optional)"
        )
        self.assertEqual(str(form.fields["department"].label), "Department (Optional)")
        self.assertEqual(
            str(form.fields["program_technical_management"].label),
            "Program and Technical Management (Optional)",
        )
        self.assertEqual(str(form.fields["team"].label), "Team (Optional)")

        self.assertEqual(form.fields["position"].empty_label, "Select Position")
        self.assertEqual(
            form.fields["organizational_unit"].empty_label, "Select Organizational Unit"
        )
        self.assertEqual(form.fields["directorate"].empty_label, "Select Directorate")
        self.assertEqual(form.fields["department"].empty_label, "Select Department")
        self.assertEqual(
            form.fields["program_technical_management"].empty_label,
            "Select Program / Technical Management",
        )
        self.assertEqual(form.fields["team"].empty_label, "Select Team")

    def test_form_optional_fields_blank(self):
        """Optional organizational fields can be blank."""
        data = {
            "user": self.user.pk,
            "leadership_level": LeadershipLevel.DIRECTORATE,
            "status": LeadershipStatus.ACTIVE,
            "term_status": TermStatus.CURRENT,
        }
        form = LeadershipProfileForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_directorate_department_ptm_combination(self):
        """Valid functional combinations pass validation."""
        data = {
            "user": self.user.pk,
            "leadership_level": LeadershipLevel.DIRECTORATE,
            "status": LeadershipStatus.ACTIVE,
            "term_status": TermStatus.CURRENT,
            "directorate": self.dir_meal.pk,
            "department": self.dept_meal.pk,
            "program_technical_management": self.ptm_meo.pk,
            "position": self.position.pk,
        }
        form = LeadershipProfileForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_directorate_department_combination_rejected(self):
        """Mismatched Directorate and Department are rejected by clean()."""
        data = {
            "user": self.user.pk,
            "leadership_level": LeadershipLevel.DIRECTORATE,
            "status": LeadershipStatus.ACTIVE,
            "term_status": TermStatus.CURRENT,
            "directorate": self.dir_meal.pk,
            "department": self.dept_fin.pk,  # Mismatched (Finance Dept under MEAL Dir)
        }
        form = LeadershipProfileForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("department", form.errors)

    def test_invalid_department_ptm_combination_rejected(self):
        """Mismatched Department and PTM role are rejected by clean()."""
        data = {
            "user": self.user.pk,
            "leadership_level": LeadershipLevel.DIRECTORATE,
            "status": LeadershipStatus.ACTIVE,
            "term_status": TermStatus.CURRENT,
            "directorate": self.dir_meal.pk,
            "department": self.dept_meal.pk,
            "program_technical_management": self.ptm_fm.pk,  # Mismatched (FM role in MEAL dept)
        }
        form = LeadershipProfileForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("program_technical_management", form.errors)

    def test_edit_profile_preserves_values(self):
        """Editing an existing profile retains existing organizational selections."""
        profile = LeadershipProfile.objects.create(
            user=self.user,
            leadership_level=LeadershipLevel.DIRECTORATE,
            directorate=self.dir_meal,
            department=self.dept_meal,
            program_technical_management=self.ptm_meo,
            position=self.position,
            status=LeadershipStatus.ACTIVE,
        )

        form = LeadershipProfileForm(instance=profile)
        self.assertEqual(form.initial["directorate"], self.dir_meal.pk)
        self.assertEqual(form.initial["department"], self.dept_meal.pk)
        self.assertEqual(
            form.initial["program_technical_management"], self.ptm_meo.pk
        )
        self.assertEqual(form.initial["position"], self.position.pk)
