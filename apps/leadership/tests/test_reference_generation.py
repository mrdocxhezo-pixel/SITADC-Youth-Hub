"""
Reference-number regression tests for the Leadership Management module.

These tests lock in the contract that ``LeadershipProfile`` and
``LeadershipAppointment`` reference numbers are system-generated through the
centralized ``ReferenceNumberService``:

* issued automatically before ``full_clean()`` runs;
* following the official ``LDR-SITADC-{YEAR}-{SEQUENCE}`` scheme format;
* unique across records;
* never regenerated when an established record is edited;
* populated on every creation path (web form, model layer, Django admin).
"""

import re

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from apps.leadership.constants import LeadershipLevel, LeadershipStatus
from apps.leadership.forms import LeadershipProfileForm
from apps.leadership.models import LeadershipProfile
from apps.references.models import GeneratedReferenceNumber

User = get_user_model()

# Official numbering scheme for leaders (apps/references/seed_data.py):
# pattern "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}", prefix LDR, org SITADC,
# sequence length 6.
LEADER_REFERENCE_PATTERN = re.compile(r"^LDR-SITADC-\d{4}-\d{6}$")


def _leader_count_registry_rows():
    return GeneratedReferenceNumber.objects.filter(record_type="leader").count()


def _seed_reference_schemes():
    """Install the official default schemes (idempotent, mirrors programs)."""
    call_command("seed_reference_schemes", verbosity=0)


class AutoReferenceNumberModelTest(TestCase):
    """Model-layer generation: issue before validation, preserve on edit."""

    def setUp(self):
        _seed_reference_schemes()
        self.user = User.objects.create_user(
            email="autoleader@sitadc.org",
            password="TestPass123!",
            first_name="Auto",
            last_name="Leader",
        )

    def test_create_generates_reference_before_validation(self):
        """A profile saved without a reference gets one before full_clean()."""
        profile = LeadershipProfile(
            user=self.user,
            leadership_level=LeadershipLevel.TEAM_LEADER,
            status=LeadershipStatus.NOMINATED,
        )
        profile.save()

        self.assertTrue(profile.reference_number)
        # full_clean() ran as part of save() without raising, proving the
        # reference existed before validation.  The registry entry is
        # confirmed against the persisted record.
        profile.full_clean()
        registry_entry = GeneratedReferenceNumber.objects.get(
            reference_number=profile.reference_number
        )
        self.assertEqual(str(registry_entry.record_id), str(profile.pk))

    def test_generated_reference_matches_official_format(self):
        """Generated numbers follow the official LDR-SITADC scheme."""
        profile = LeadershipProfile.objects.create(
            user=self.user,
            leadership_level=LeadershipLevel.TEAM_LEADER,
            status=LeadershipStatus.NOMINATED,
        )
        self.assertRegex(profile.reference_number, LEADER_REFERENCE_PATTERN)

    def test_generated_references_are_unique(self):
        """Multiple profiles receive distinct reference numbers."""
        references = set()
        for index in range(3):
            leader = User.objects.create_user(
                email=f"unique{index}@sitadc.org",
                password="TestPass123!",
            )
            profile = LeadershipProfile.objects.create(
                user=leader,
                leadership_level=LeadershipLevel.TEAM_LEADER,
                status=LeadershipStatus.NOMINATED,
            )
            references.add(profile.reference_number)
        self.assertEqual(len(references), 3)

    def test_edit_preserves_existing_reference(self):
        """Editing a profile never regenerates its reference number."""
        profile = LeadershipProfile.objects.create(
            user=self.user,
            leadership_level=LeadershipLevel.TEAM_LEADER,
            status=LeadershipStatus.NOMINATED,
        )
        original_reference = profile.reference_number
        registry_rows = _leader_count_registry_rows()

        profile.biography = "Updated biography."
        profile.status = LeadershipStatus.ACTIVE
        profile.save()
        profile.refresh_from_db()

        self.assertEqual(profile.reference_number, original_reference)
        self.assertEqual(_leader_count_registry_rows(), registry_rows)

    def test_explicit_reference_is_not_replaced(self):
        """Explicitly supplied references are kept untouched."""
        profile = LeadershipProfile.objects.create(
            user=self.user,
            reference_number="SITADC-LDR-2026-00999",
            leadership_level=LeadershipLevel.TEAM_LEADER,
            status=LeadershipStatus.ACTIVE,
        )
        self.assertEqual(profile.reference_number, "SITADC-LDR-2026-00999")


class ProfileFormReferenceTest(TestCase):
    """The form does not require a reference number up front."""

    def setUp(self):
        _seed_reference_schemes()
        self.target = User.objects.create_user(
            email="formleader@sitadc.org",
            password="TestPass123!",
        )

    def test_form_valid_without_reference_number(self):
        """A valid form does not fail because the reference is missing."""
        form = LeadershipProfileForm(
            data={
                "user": self.target.pk,
                "leadership_level": LeadershipLevel.TEAM_LEADER,
                "status": LeadershipStatus.NOMINATED,
                "phone_number": "+260971234567",
                "email": "formleader@sitadc.org",
                # Term-tracking fields carry model defaults but are still
                # required inputs on the auto-generated ModelForm.
                "terms_completed": 0,
                "max_terms": 2,
                "term_status": "CURRENT",
                "renewal_status": "NOT_ELIGIBLE",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertNotIn("reference_number", form.errors)

        profile = form.save()
        self.assertRegex(profile.reference_number, LEADER_REFERENCE_PATTERN)


class ProfileCreateViewReferenceTest(TestCase):
    """Web-form creation issues a reference and redirects successfully."""

    def setUp(self):
        _seed_reference_schemes()
        self.client = Client()
        self.creator = User.objects.create_user(
            email="creator@sitadc.org",
            password="TestPass123!",
        )
        self.creator.user_permissions.add(
            Permission.objects.get(codename="leadership.create"),
            Permission.objects.get(codename="leadership.view"),
        )
        self.client.login(email="creator@sitadc.org", password="TestPass123!")
        self.leader = User.objects.create_user(
            email="newleader@sitadc.org",
            password="TestPass123!",
            first_name="New",
            last_name="Leader",
        )

    def _valid_payload(self):
        return {
            "user": self.leader.pk,
            "leadership_level": LeadershipLevel.TEAM_LEADER,
            "status": LeadershipStatus.APPLIED,
            "phone_number": "",
            "email": "",
            # Term-tracking fields carry model defaults but are still
            # required inputs on the auto-generated ModelForm.
            "terms_completed": 0,
            "max_terms": 2,
            "term_status": "CURRENT",
            "renewal_status": "NOT_ELIGIBLE",
        }

    def test_create_view_succeeds_and_generates_reference(self):
        """POSTing a valid profile succeeds and populates the reference."""
        url = reverse("leadership:profile_create")
        response = self.client.post(url, self._valid_payload(), follow=True)

        self.assertEqual(response.status_code, 200)
        profile = LeadershipProfile.objects.get(user=self.leader)
        self.assertRegex(profile.reference_number, LEADER_REFERENCE_PATTERN)

        messages_list = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(
            any(profile.reference_number in m for m in messages_list),
            "Success message should display the generated reference.",
        )

    def test_duplicate_profile_renders_form_error_not_crash(self):
        """Submitting a duplicate renders the form with an error, not a 500."""
        url = reverse("leadership:profile_create")
        first = self.client.post(url, self._valid_payload())
        self.assertEqual(first.status_code, 302)

        second = self.client.post(url, self._valid_payload())
        self.assertEqual(second.status_code, 200)
        self.assertContains(second, "already exists", status_code=200)
        self.assertEqual(LeadershipProfile.objects.filter(user=self.leader).count(), 1)


class ProfileUpdateViewReferenceTest(TestCase):
    """Editing through the web form preserves the reference number."""

    def setUp(self):
        _seed_reference_schemes()
        self.client = Client()
        self.editor = User.objects.create_user(
            email="editor@sitadc.org",
            password="TestPass123!",
        )
        self.editor.user_permissions.add(
            Permission.objects.get(codename="leadership.update")
        )
        self.leader_user = User.objects.create_user(
            email="editme@sitadc.org",
            password="TestPass123!",
        )
        self.profile = LeadershipProfile.objects.create(
            user=self.leader_user,
            leadership_level=LeadershipLevel.TEAM_LEADER,
            status=LeadershipStatus.NOMINATED,
        )
        self.original_reference = self.profile.reference_number
        self.registry_rows = _leader_count_registry_rows()
        self.client.login(email="editor@sitadc.org", password="TestPass123!")

    def test_update_view_preserves_reference(self):
        url = reverse("leadership:profile_update", args=[self.profile.pk])
        response = self.client.post(
            url,
            {
                "user": self.leader_user.pk,
                "leadership_level": LeadershipLevel.TEAM_LEADER,
                "status": LeadershipStatus.ACTIVE,
                "biography": "Edited through the web form.",
                "phone_number": "",
                "email": "",
                # Term-tracking fields carry model defaults but are still
                # required inputs on the auto-generated ModelForm.
                "terms_completed": 0,
                "max_terms": 2,
                "term_status": "CURRENT",
                "renewal_status": "NOT_ELIGIBLE",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.reference_number, self.original_reference)
        self.assertEqual(_leader_count_registry_rows(), self.registry_rows)
        self.assertEqual(self.profile.biography, "Edited through the web form.")


class AdminCreationReferenceTest(TestCase):
    """Django admin creation also receives a generated reference."""

    def setUp(self):
        _seed_reference_schemes()
        self.admin = User.objects.create_superuser(
            email="root@sitadc.org",
            password="AdminPass123!",
        )
        self.leader = User.objects.create_user(
            email="admincreated@sitadc.org",
            password="TestPass123!",
        )
        self.client = Client()
        self.client.force_login(self.admin)

    def test_admin_add_generates_reference(self):
        url = "/admin/leadership/leadershipprofile/add/"
        response = self.client.post(
            url,
            {
                "user": self.leader.pk,
                "leadership_level": LeadershipLevel.TEAM_LEADER,
                "status": LeadershipStatus.NOMINATED,
                # The admin renders every model field; these carry defaults on
                # the model but are still required in the auto-generated form.
                "terms_completed": 0,
                "max_terms": 2,
                "term_status": "CURRENT",
                "renewal_status": "NOT_ELIGIBLE",
            },
        )
        self.assertEqual(response.status_code, 302)

        profile = LeadershipProfile.objects.get(user=self.leader)
        self.assertRegex(profile.reference_number, LEADER_REFERENCE_PATTERN)

        # The registry entry is confirmed against the persisted record.
        registry_entry = GeneratedReferenceNumber.objects.get(
            reference_number=profile.reference_number
        )
        self.assertEqual(str(registry_entry.record_id), str(profile.pk))


class AppointmentAutoReferenceTest(TestCase):
    """Appointments share the same automatic generation behaviour."""

    def setUp(self):
        _seed_reference_schemes()
        self.user = User.objects.create_user(
            email="appt@sitadc.org",
            password="TestPass123!",
        )
        self.profile = LeadershipProfile.objects.create(
            user=self.user,
            leadership_level=LeadershipLevel.TEAM_LEADER,
            status=LeadershipStatus.ACTIVE,
        )

    def test_appointment_saved_without_reference_gets_one(self):
        from apps.organizations.models import (
            OrganizationLevel,
            OrganizationUnit,
            Position,
        )

        level = OrganizationLevel.objects.create(
            name="Ref Level", code="REFLVL", sort_order=1
        )
        unit = OrganizationUnit.objects.create(
            name="Ref Unit", unit_type="DEPARTMENT", level=level
        )
        position = Position.objects.create(
            title="Ref Position", organizational_unit=unit
        )
        appointment = self.profile.appointments.create(
            position=position,
            organizational_unit=unit,
        )
        self.assertTrue(appointment.reference_number)
        self.assertRegex(appointment.reference_number, LEADER_REFERENCE_PATTERN)
