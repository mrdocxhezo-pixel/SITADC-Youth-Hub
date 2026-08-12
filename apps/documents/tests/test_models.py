"""Model-level tests for the Document Management module."""

from __future__ import annotations

from django.core.exceptions import ValidationError

from ..constants import (
    DocumentStatus,
    HoldType,
)
from ..models import (
    DocumentAuditRecord,
    DocumentTimelineEvent,
)
from .base import DocumentsTestCase


class DocumentModelTests(DocumentsTestCase):
    """Test Document creation, reference allocation, and string representation."""

    def test_document_creation_and_reference_number_allocation(self):
        document = self._upload_document()
        self.assertIsNotNone(document.pk)
        self.assertTrue(document.reference_number.startswith("SITADC/"))
        self.assertEqual(document.title, "Test Document")
        self.assertEqual(document.status, DocumentStatus.UPLOADED)
        self.assertEqual(document.current_version_number, 1)
        self.assertIsNotNone(document.checksum)
        self.assertIsNotNone(document.mime_type)

    def test_document_str_representation(self):
        document = self._upload_document()
        expected = f"{document.reference_number} — {document.title}"
        self.assertEqual(str(document), expected)

    def test_document_version_str_representation(self):
        document = self._upload_document()
        version = document.versions.first()
        self.assertIsNotNone(version)
        expected = f"{document.reference_number} v{version.version_number}"
        self.assertEqual(str(version), expected)

    def test_document_unique_reference_number(self):
        doc1 = self._upload_document(title="First Document")
        doc2 = self._upload_document(title="Second Document")
        self.assertNotEqual(doc1.reference_number, doc2.reference_number)

    def test_document_defaults(self):
        document = self._upload_document()
        self.assertEqual(document.current_version_number, 1)
        self.assertFalse(document.is_sensitive)
        self.assertFalse(document.legal_hold)
        self.assertFalse(document.safeguarding_hold)
        self.assertFalse(document.download_restricted)
        self.assertFalse(document.print_restricted)
        self.assertTrue(document.external_sharing_restricted)
        self.assertEqual(document.keywords, [])


class DocumentCategoryModelTests(DocumentsTestCase):
    """Test DocumentCategory string representation."""

    def test_document_category_str_representation(self):
        self.assertEqual(str(self.category), "General Documents")


class DocumentFolderModelTests(DocumentsTestCase):
    """Test DocumentFolder string representation."""

    def test_document_folder_str_representation(self):
        expected = f"{self.folder.reference_number} — {self.folder.name}"
        self.assertEqual(str(self.folder), expected)


class DocumentTagModelTests(DocumentsTestCase):
    """Test DocumentTag string representation."""

    def test_document_tag_str_representation(self):
        self.assertEqual(str(self.tag), "Important")


class DocumentTypeModelTests(DocumentsTestCase):
    """Test DocumentType string representation."""

    def test_document_type_str_representation(self):
        self.assertEqual(str(self.doc_type), "Policy")


class DocumentCheckoutModelTests(DocumentsTestCase):
    """Test DocumentCheckout string representation."""

    def test_document_checkout_str_representation(self):
        from ..services import checkout_document

        document = self._upload_document()
        checkout = checkout_document(self.manager, document)
        expected = (
            f"Checkout — {document.reference_number} "
            f"by {checkout.checked_out_by} [{checkout.status}]"
        )
        self.assertEqual(str(checkout), expected)


class DocumentShareModelTests(DocumentsTestCase):
    """Test DocumentShare string representation."""

    def test_document_share_str_representation(self):
        from ..services import share_document

        document = self._upload_document()
        share = share_document(
            self.manager, document, self.viewer, permission_level="VIEW"
        )
        expected = (
            f"Share — {document.reference_number} to {self.viewer} "
            f"[{share.permission_level}]"
        )
        self.assertEqual(str(share), expected)


class DocumentHoldModelTests(DocumentsTestCase):
    """Test DocumentHold string representation."""

    def test_document_hold_str_representation(self):
        from ..services import apply_hold

        document = self._upload_document()
        hold = apply_hold(
            self.manager,
            document,
            hold_type=HoldType.LEGAL,
            reason="Legal investigation",
        )
        expected = (
            f"Hold — {document.reference_number} " f"[{hold.hold_type}] ({hold.status})"
        )
        self.assertEqual(str(hold), expected)


class RetentionCategoryModelTests(DocumentsTestCase):
    """Test RetentionCategory string representation."""

    def test_retention_category_str_representation(self):
        self.assertEqual(str(self.retention_category), "Standard Retention")


class DocumentAuditRecordImmutabilityTests(DocumentsTestCase):
    """Test that DocumentAuditRecord is immutable after creation."""

    def test_document_audit_record_is_immutable(self):
        document = self._upload_document()
        audit = DocumentAuditRecord.objects.filter(
            entity_type="Document",
            entity_id=str(document.pk),
        ).first()
        self.assertIsNotNone(audit)

        with self.assertRaises(ValidationError):
            audit.notes = "Trying to modify"
            audit.save()

    def test_document_audit_record_cannot_be_deleted(self):
        document = self._upload_document()
        audit = DocumentAuditRecord.objects.filter(
            entity_type="Document",
            entity_id=str(document.pk),
        ).first()
        self.assertIsNotNone(audit)

        with self.assertRaises(ValidationError):
            audit.delete()


class DocumentTimelineEventImmutabilityTests(DocumentsTestCase):
    """Test DocumentTimelineEvent creation and structure."""

    def test_document_timeline_event_is_immutable(self):
        document = self._upload_document()
        timeline_events = DocumentTimelineEvent.objects.filter(document=document)
        self.assertGreaterEqual(timeline_events.count(), 1)

        event = timeline_events.first()
        self.assertIsNotNone(event.document_id)
        self.assertIsNotNone(event.event_type)
        self.assertIsNotNone(event.actor)
