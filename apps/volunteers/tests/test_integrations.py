"""Seed, selector, storage, and query regression tests."""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.references.models import ReferenceNumberScheme
from apps.volunteers.models import VolunteerApplication, VolunteerProfile
from apps.volunteers.selectors import visible_volunteer_profiles

User = get_user_model()


class VolunteerIntegrationTests(TestCase):
    def test_seed_command_is_idempotent(self):
        call_command("seed_volunteers", verbosity=0)
        call_command("seed_volunteers", verbosity=0)
        self.assertEqual(
            ReferenceNumberScheme.objects.filter(module="volunteers").count(),
            4,
        )

    def test_profile_selector_avoids_user_n_plus_one_queries(self):
        admin = User.objects.create_superuser(
            email="query-admin@example.com",
            username="query-admin",
            first_name="Query",
            last_name="Admin",
        )
        for index in range(5):
            user = User.objects.create_user(
                email=f"query-{index}@example.com",
                username=f"query-{index}",
                first_name="Query",
                last_name=str(index),
            )
            VolunteerProfile.objects.create(
                user=user,
                reference_number=f"VOL-QUERY-{index:04d}",
            )
        with self.assertNumQueries(1):
            names = [
                profile.user.full_name
                for profile in visible_volunteer_profiles(admin).order_by(
                    "reference_number"
                )
            ]
        self.assertEqual(len(names), 5)

    def test_confidential_upload_storage_has_no_public_url(self):
        field = VolunteerApplication._meta.get_field("cv_file")
        with self.assertRaises(ValueError):
            field.storage.url("volunteers/applications/cv/test.pdf")
