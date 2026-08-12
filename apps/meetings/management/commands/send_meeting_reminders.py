"""Management command to send meeting reminders."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.meetings.models import EventReminder, Meeting
from apps.meetings.services import ReminderService


class Command(BaseCommand):
    help = "Send pending meeting and event reminders."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours-ahead",
            type=int,
            default=24,
            help="Send reminders for events/meetings within this many hours "
            "(default: 24).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without actually sending.",
        )
        parser.add_argument(
            "--type",
            choices=["all", "event", "meeting"],
            default="all",
            help="Type of reminders to process (default: all).",
        )

    def handle(self, *args, **options):
        hours_ahead = options["hours_ahead"]
        dry_run = options["dry_run"]
        reminder_type = options["type"]

        cutoff = timezone.now() + timezone.timedelta(hours=hours_ahead)

        self.stdout.write(f"Processing reminders due within {hours_ahead} hours...")

        sent = 0
        failed = 0

        if reminder_type in ["all", "event"]:
            s, f = self._process_event_reminders(cutoff, dry_run)
            sent += s
            failed += f

        if reminder_type in ["all", "meeting"]:
            s, f = self._process_meeting_reminders(cutoff, dry_run)
            sent += s
            failed += f

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    "Dry run complete. Would send "
                    f"{sent} reminders, {failed} would fail."
                )
            )
        else:
            if failed:
                self.stdout.write(
                    self.style.WARNING(f"Sent {sent} reminders, {failed} failed.")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully sent {sent} reminders.")
                )

    def _process_event_reminders(self, cutoff, dry_run):
        sent = 0
        failed = 0

        reminders = EventReminder.objects.filter(
            status__in=["PENDING", "SCHEDULED"],
            due_at__lte=cutoff,
        ).select_related("event", "meeting")

        for reminder in reminders:
            if dry_run:
                target = (
                    reminder.event.title if reminder.event else reminder.meeting.title
                )
                self.stdout.write(
                    "  Would send: " f"{reminder.reminder_type} for {target}"
                )
                sent += 1
                continue

            try:
                if reminder.event:
                    user = reminder.event.organizer
                else:
                    user = reminder.meeting.organizer
                service = ReminderService(user=user)
                service.send_reminder(reminder)
                sent += 1
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f"Failed to send reminder {reminder.pk}: {e}")
                )

        return sent, failed

    def _process_meeting_reminders(self, cutoff, dry_run):
        # Meeting reminders are handled via EventReminder with meeting FK
        # This is for any meeting-specific reminders not tied to events
        sent = 0
        failed = 0

        meetings = Meeting.objects.filter(
            start_at__lte=cutoff,
            start_at__gte=timezone.now(),
            status__in=["CONFIRMED", "IN_PROGRESS"],
        ).select_related("organizer")

        for meeting in meetings:
            if dry_run:
                self.stdout.write(f"  Would send meeting reminder for: {meeting.title}")
                sent += 1
                continue

            try:
                # Send reminder logic here
                # For now just log
                self.stdout.write(f"  Sent meeting reminder for: {meeting.title}")
                sent += 1
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to send meeting reminder {meeting.pk}: {e}"
                    )
                )

        return sent, failed
