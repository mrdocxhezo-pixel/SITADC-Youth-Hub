"""Management command tests for the Calendar & Meetings app."""

from django.core.management import call_command
from django.utils import timezone

from apps.meetings.constants import (
    CalendarType,
    CalendarVisibility,
    MeetingStatus,
    MeetingType,
)
from apps.meetings.models import Calendar, Meeting
from apps.meetings.tests.base import MeetingsTestCase


class ValidateMeetingDataCommandTests(MeetingsTestCase):
    def test_validate_meeting_data_no_issues(self):
        """Test command runs without errors when data is valid."""
        output = self.call_command("validate_meeting_data")
        self.assertIn("No issues found", output)

    def test_validate_meeting_data_detects_missing_organizer(self):
        """Test command detects meetings without organizers."""
        Meeting.objects.create(
            title="No Organizer",
            meeting_type=MeetingType.STAFF,
            start_at=timezone.now() + timezone.timedelta(days=1),
            end_at=timezone.now() + timezone.timedelta(days=1, hours=1),
            status=MeetingStatus.DRAFT,
        )
        output = self.call_command("validate_meeting_data")
        self.assertIn("has no organizer", output)

    def test_validate_meeting_data_detects_bad_dates(self):
        """Test command detects meetings with end before start."""
        Meeting.objects.create(
            title="Bad Dates",
            meeting_type=MeetingType.STAFF,
            organizer=self.manager,
            start_at=timezone.now() + timezone.timedelta(days=2),
            end_at=timezone.now() + timezone.timedelta(days=1),
            status=MeetingStatus.DRAFT,
        )
        output = self.call_command("validate_meeting_data")
        self.assertIn("end_at <= start_at", output)


class ArchiveOldMeetingsCommandTests(MeetingsTestCase):
    def test_archive_old_meetings_dry_run(self):
        """Test dry run shows what would be archived."""
        old_meeting = Meeting.objects.create(
            title="Old Meeting",
            meeting_type=MeetingType.STAFF,
            organizer=self.manager,
            start_at=timezone.now() - timezone.timedelta(days=400),
            end_at=timezone.now() - timezone.timedelta(days=400, hours=1),
            status=MeetingStatus.COMPLETED,
        )
        output = self.call_command("archive_old_meetings", "--dry-run", "--days=365")
        self.assertIn("Would archive", output)
        self.assertIn(str(old_meeting.pk), output)

    def test_archive_old_meetings_actually_archives(self):
        """Test command actually archives old meetings."""
        old_meeting = Meeting.objects.create(
            title="Old Meeting",
            meeting_type=MeetingType.STAFF,
            organizer=self.manager,
            start_at=timezone.now() - timezone.timedelta(days=400),
            end_at=timezone.now() - timezone.timedelta(days=400, hours=1),
            status=MeetingStatus.COMPLETED,
        )
        self.call_command("archive_old_meetings", "--days=365")
        old_meeting.refresh_from_db()
        self.assertTrue(old_meeting.is_archived)

    def test_archive_old_meetings_includes_cancelled(self):
        """Test --include-cancelled flag archives cancelled meetings."""
        old_cancelled = Meeting.objects.create(
            title="Old Cancelled",
            meeting_type=MeetingType.STAFF,
            organizer=self.manager,
            start_at=timezone.now() - timezone.timedelta(days=400),
            end_at=timezone.now() - timezone.timedelta(days=400, hours=1),
            status=MeetingStatus.CANCELLED,
        )
        self.call_command("archive_old_meetings", "--days=365", "--include-cancelled")
        old_cancelled.refresh_from_db()
        self.assertTrue(old_cancelled.is_archived)


class GenerateMeetingReferencesCommandTests(MeetingsTestCase):
    def test_generate_references_dry_run(self):
        """Test dry run shows what references would be generated."""
        cal = Calendar.objects.create(
            name="No Reference",
            calendar_type=CalendarType.TEAM,
            visibility=CalendarVisibility.TEAM,
            owner=self.manager,
        )
        cal.reference = ""
        cal.save(update_fields=["reference"])

        output = self.call_command("generate_meeting_references", "--dry-run")
        self.assertIn("would generate", output)

    def test_generate_references_actually_generates(self):
        """Test command actually generates references."""
        cal = Calendar.objects.create(
            name="No Reference",
            calendar_type=CalendarType.TEAM,
            visibility=CalendarVisibility.TEAM,
            owner=self.manager,
        )
        cal.reference = ""
        cal.save(update_fields=["reference"])

        self.call_command("generate_meeting_references")
        cal.refresh_from_db()
        self.assertTrue(cal.reference)
        self.assertTrue(cal.reference.startswith("SITADC-"))


class CleanupMeetingDataCommandTests(MeetingsTestCase):
    def test_cleanup_dry_run(self):
        """Test dry run shows what would be deleted."""
        cal = Calendar.objects.create(
            name="To Delete",
            calendar_type=CalendarType.TEAM,
            visibility=CalendarVisibility.TEAM,
            owner=self.manager,
        )
        cal.delete()  # Soft delete

        output = self.call_command("cleanup_meeting_data", "--dry-run", "--days=0")
        self.assertIn("would delete", output)

    def test_cleanup_actually_deletes(self):
        """Test command actually hard deletes soft-deleted records."""
        cal = Calendar.objects.create(
            name="To Delete",
            calendar_type=CalendarType.TEAM,
            visibility=CalendarVisibility.TEAM,
            owner=self.manager,
        )
        cal.delete()  # Soft delete

        self.call_command("cleanup_meeting_data", "--days=0")
        # Should be hard deleted (not even in all_objects)
        self.assertFalse(Calendar.all_objects.filter(pk=cal.pk).exists())


class SendMeetingRemindersCommandTests(MeetingsTestCase):
    def test_send_reminders_dry_run(self):
        """Test dry run works without errors."""
        output = self.call_command("send_meeting_reminders", "--dry-run")
        self.assertIn("Dry run complete", output)

    def test_send_reminders_type_filter(self):
        """Test --type filter works."""
        output = self.call_command(
            "send_meeting_reminders", "--dry-run", "--type=event"
        )
        self.assertIn("Dry run complete", output)


class HelperMethods:
    """Mixin to add call_command helper."""

    def call_command(self, command, *args, **kwargs):
        from io import StringIO

        out = StringIO()
        call_command(command, *args, stdout=out, **kwargs)
        return out.getvalue()


# Mix the helper into test classes
class ValidateMeetingDataCommandTests(ValidateMeetingDataCommandTests, HelperMethods):
    pass


class ArchiveOldMeetingsCommandTests(ArchiveOldMeetingsCommandTests, HelperMethods):
    pass


class GenerateMeetingReferencesCommandTests(
    GenerateMeetingReferencesCommandTests, HelperMethods
):
    pass


class CleanupMeetingDataCommandTests(CleanupMeetingDataCommandTests, HelperMethods):
    pass


class SendMeetingRemindersCommandTests(SendMeetingRemindersCommandTests, HelperMethods):
    pass
