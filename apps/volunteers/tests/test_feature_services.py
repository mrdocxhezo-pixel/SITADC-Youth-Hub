"""
Service tests for volunteer activity, disciplinary, communication,
and document management.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.references.constants import ReferenceModules
from apps.references.models import ReferenceNumberScheme
from apps.volunteers.constants import (
    DisciplinaryStatus,
    VolunteerDocumentStatus,
    VolunteerStatus,
)
from apps.volunteers.models import (
    VolunteerActivityLog,
    VolunteerCommunication,
    VolunteerDisciplinaryRecord,
)
from apps.volunteers.services import (
    VolunteerActivityService,
    VolunteerCommunicationService,
    VolunteerDisciplinaryService,
    VolunteerDocumentService,
    VolunteerProfileService,
)

User = get_user_model()


class VolunteerFeatureServiceTests(TestCase):
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
        ReferenceNumberScheme.objects.update_or_create(
            module=ReferenceModules.VOLUNTEERS,
            record_type="disciplinary",
            prefix="VDC",
            defaults={
                "name": "Disciplinary Scheme",
                "code": "disciplinary",
                "is_default_for_record_type": True,
                "is_default_for_module": False,
            },
        )
        self.profile = VolunteerProfileService(user=self.user).create_profile(
            user_account=self.vol_user, region="Lusaka"
        )

    def test_activity_log_service(self):
        service = VolunteerActivityService(user=self.user)
        entry = service.log_activity(
            profile=self.profile,
            activity_title="Community Cleanup",
            activity_date="2026-03-10",
            category="OUTREACH",
            hours_served="4.5",
        )
        self.assertIsInstance(entry, VolunteerActivityLog)
        self.assertEqual(entry.activity_title, "Community Cleanup")
        self.assertEqual(float(entry.hours_served), 4.5)
        self.assertEqual(entry.category, "OUTREACH")

    def test_activity_log_rejects_future_date(self):
        service = VolunteerActivityService(user=self.user)
        with self.assertRaises(ValidationError):
            service.log_activity(
                profile=self.profile,
                activity_title="Future Event",
                activity_date="2099-01-01",
            )

    def test_activity_log_rejects_exited_volunteer(self):
        from apps.volunteers.services import VolunteerExitService

        profile_service = VolunteerProfileService(user=self.user)
        profile_service.update_status(self.profile, VolunteerStatus.ACTIVE)
        exit_service = VolunteerExitService(user=self.user)
        exit_rec = exit_service.initiate_exit(
            profile=self.profile,
            reason="RESIGNATION",
            effective_date="2026-04-01",
            assets_returned=True,
            documents_returned=True,
        )
        exit_service.complete_exit(exit_rec)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, VolunteerStatus.ALUMNI)
        service = VolunteerActivityService(user=self.user)
        with self.assertRaises(ValidationError):
            service.log_activity(
                profile=self.profile,
                activity_title="Late Log",
                activity_date="2026-03-01",
            )

    def test_disciplinary_open_and_decision(self):
        service = VolunteerDisciplinaryService(user=self.user)
        record = service.open_disciplinary(
            profile=self.profile,
            incident_date="2026-03-15",
            nature_of_concern="Violated code of conduct.",
        )
        self.assertIsInstance(record, VolunteerDisciplinaryRecord)
        self.assertTrue(record.reference_number.startswith("VDC"))
        self.assertEqual(record.status, DisciplinaryStatus.PENDING)

        decided = service.decide_disciplinary(
            record,
            status=DisciplinaryStatus.RESOLVED,
            decision="SUSPENSION",
            investigation_summary="Confirmed after review.",
            corrective_action="Two week suspension.",
            effective_date="2026-03-20",
        )
        self.assertEqual(decided.status, DisciplinaryStatus.RESOLVED)
        self.assertEqual(decided.decision, "SUSPENSION")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, VolunteerStatus.SUSPENDED)

    def test_disciplinary_termination_exits_volunteer(self):
        service = VolunteerDisciplinaryService(user=self.user)
        record = service.open_disciplinary(
            profile=self.profile,
            incident_date="2026-03-15",
            nature_of_concern="Serious misconduct.",
        )
        service.decide_disciplinary(
            record,
            status=DisciplinaryStatus.APPLIED,
            decision="TERMINATION",
            effective_date="2026-03-20",
        )
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, VolunteerStatus.EXITED)
        self.assertEqual(self.profile.exit_reason, "DISMISSAL")

    def test_disciplinary_requires_decision_when_resolved(self):
        service = VolunteerDisciplinaryService(user=self.user)
        record = service.open_disciplinary(
            profile=self.profile,
            incident_date="2026-03-15",
            nature_of_concern="Misconduct.",
        )
        with self.assertRaises(ValidationError):
            service.decide_disciplinary(
                record,
                status=DisciplinaryStatus.RESOLVED,
                decision="",
            )

    def test_communication_service(self):
        service = VolunteerCommunicationService(user=self.user)
        message = service.record_communication(
            profile=self.profile,
            channel="EMAIL",
            subject="Welcome",
            body="Welcome to the team.",
        )
        self.assertIsInstance(message, VolunteerCommunication)
        self.assertEqual(message.channel, "EMAIL")
        self.assertEqual(message.sent_by, self.user)

    def test_communication_rejects_invalid_channel(self):
        service = VolunteerCommunicationService(user=self.user)
        with self.assertRaises(ValidationError):
            service.record_communication(
                profile=self.profile,
                channel="PIGEON",
                subject="Nope",
            )

    def test_document_versioning_and_approval(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        service = VolunteerDocumentService(user=self.user)
        content = SimpleUploadedFile(
            "contract.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        )
        doc1 = service.upload_document(
            profile=self.profile,
            title="Volunteer Contract",
            file=content,
            document_type="Contract",
            is_confidential=True,
        )
        self.assertEqual(doc1.version, 1)
        self.assertEqual(doc1.status, VolunteerDocumentStatus.PENDING_APPROVAL)

        doc2 = service.upload_document(
            profile=self.profile,
            title="Volunteer Contract",
            file=content,
            document_type="Contract",
            is_confidential=True,
        )
        self.assertEqual(doc2.version, 2)
        self.assertEqual(doc2.supersedes, doc1)

        approved = service.approve_document(doc2)
        self.assertEqual(approved.status, VolunteerDocumentStatus.APPROVED)
        self.assertEqual(approved.approved_by, self.user)
        self.assertIsNotNone(approved.approved_at)

    def test_document_approve_requires_pending(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        service = VolunteerDocumentService(user=self.user)
        content = SimpleUploadedFile(
            "notes.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        )
        doc = service.upload_document(
            profile=self.profile,
            title="Notes",
            file=content,
        )
        service.reject_document(doc, notes="Incomplete.")
        doc.refresh_from_db()
        self.assertEqual(doc.status, VolunteerDocumentStatus.REJECTED)
        with self.assertRaises(ValidationError):
            service.approve_document(doc)

    def test_document_archive(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        service = VolunteerDocumentService(user=self.user)
        content = SimpleUploadedFile(
            "notes.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        )
        doc = service.upload_document(
            profile=self.profile,
            title="Notes",
            file=content,
        )
        archived = service.archive_document(doc)
        self.assertEqual(archived.status, VolunteerDocumentStatus.ARCHIVED)
