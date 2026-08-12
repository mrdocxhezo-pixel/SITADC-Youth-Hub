"""
Service tests for volunteer management business logic.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.references.constants import ReferenceModules
from apps.references.models import ReferenceNumberScheme
from apps.volunteers.constants import LeaveStatus, VolunteerStatus
from apps.volunteers.services import (
    VolunteerAssignmentService,
    VolunteerAttendanceService,
    VolunteerExitService,
    VolunteerLeaveService,
    VolunteerProfileService,
)

User = get_user_model()


class VolunteerServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@example.com",
            username="adminuser",
            first_name="Admin",
            last_name="User",
            is_staff=True,
            is_superuser=True,
        )
        self.vol_user = User.objects.create_user(
            email="vol@example.com",
            username="voluser",
            first_name="Sam",
            last_name="Volunteer",
        )
        ReferenceNumberScheme.objects.update_or_create(
            module=ReferenceModules.VOLUNTEERS,
            record_type="volunteer",
            prefix="VOL",
            defaults={
                "name": "Volunteer Scheme",
                "code": "volunteer",
                "is_default_for_record_type": True,
                "is_default_for_module": True,
            },
        )

    def test_create_profile_service(self):
        service = VolunteerProfileService(user=self.user)
        profile = service.create_profile(user_account=self.vol_user, region="Lusaka")
        self.assertIsNotNone(profile.reference_number)
        self.assertEqual(profile.user, self.vol_user)
        self.assertEqual(profile.region, "Lusaka")

    def test_update_status_service(self):
        service = VolunteerProfileService(user=self.user)
        profile = service.create_profile(user_account=self.vol_user)
        updated = service.update_status(
            profile, new_status=VolunteerStatus.ACTIVE, notes="Verified"
        )
        self.assertEqual(updated.status, VolunteerStatus.ACTIVE)
        self.assertEqual(profile.status_history.count(), 2)

    def test_assignment_service(self):
        profile_service = VolunteerProfileService(user=self.user)
        profile = profile_service.create_profile(user_account=self.vol_user)
        profile_service.update_status(profile, VolunteerStatus.ACTIVE)

        assign_service = VolunteerAssignmentService(user=self.user)
        assign = assign_service.create_assignment(
            profile=profile,
            title="Field Coordinator",
            start_date="2026-01-15",
        )
        self.assertEqual(assign.title, "Field Coordinator")
        profile.refresh_from_db()
        self.assertEqual(profile.status, VolunteerStatus.ASSIGNED)

    def test_attendance_service(self):
        profile_service = VolunteerProfileService(user=self.user)
        profile = profile_service.create_profile(user_account=self.vol_user)

        att_service = VolunteerAttendanceService(user=self.user)
        att = att_service.log_attendance(
            profile=profile,
            date="2026-02-10",
            activity_name="Youth Forum",
            hours=6.0,
        )
        self.assertEqual(att.activity_name, "Youth Forum")
        self.assertEqual(float(att.hours_served), 6.0)

    def test_leave_service(self):
        from datetime import timedelta

        from django.utils import timezone

        profile_service = VolunteerProfileService(user=self.user)
        profile = profile_service.create_profile(user_account=self.vol_user)
        profile_service.update_status(profile, VolunteerStatus.ACTIVE)

        leave_service = VolunteerLeaveService(user=self.user)
        leave = leave_service.apply_leave(
            profile=profile,
            leave_type="ANNUAL",
            start_date=(timezone.localdate() - timedelta(days=1)).isoformat(),
            end_date=(timezone.localdate() + timedelta(days=1)).isoformat(),
            reason="Vacation",
        )
        self.assertEqual(leave.status, LeaveStatus.SUBMITTED)

        leave_service.approve_leave(leave, approve=True)
        leave.refresh_from_db()
        self.assertEqual(leave.status, LeaveStatus.APPROVED)
        profile.refresh_from_db()
        self.assertEqual(profile.status, VolunteerStatus.ON_LEAVE)

    def test_exit_service(self):
        profile_service = VolunteerProfileService(user=self.user)
        profile = profile_service.create_profile(user_account=self.vol_user)
        profile_service.update_status(profile, VolunteerStatus.ACTIVE)

        exit_service = VolunteerExitService(user=self.user)
        exit_rec = exit_service.initiate_exit(
            profile=profile,
            reason="RESIGNATION",
            effective_date="2026-04-01",
            assets_returned=True,
            documents_returned=True,
        )
        self.assertEqual(exit_rec.status, "INITIATED")

        exit_service.complete_exit(exit_rec)
        profile.refresh_from_db()
        self.assertEqual(profile.status, VolunteerStatus.ALUMNI)
