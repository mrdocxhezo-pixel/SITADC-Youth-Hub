"""Service-level tests for the Document Management module."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied

from ..constants import (
    CheckoutStatus,
    DocumentStatus,
)
from ..exceptions import (
    DocumentArchiveError,
    DocumentCheckoutError,
    DocumentManagementError,
    DocumentShareError,
    DocumentVersionError,
    DocumentWorkflowError,
)
from ..models import (
    DocumentAuditRecord,
    DocumentTimelineEvent,
)
from .base import DocumentsTestCase


class UploadDocumentTests(DocumentsTestCase):
    """Test document upload service."""

    def test_upload_document(self):
        document = self._upload_document()
        self.assertIsNotNone(document.pk)
        self.assertEqual(document.status, DocumentStatus.UPLOADED)

        version = document.versions.filter(is_current=True).first()
        self.assertIsNotNone(version)
        self.assertEqual(version.version_number, 1)
        self.assertTrue(version.is_current)

        audit = DocumentAuditRecord.objects.filter(
            entity_type="Document",
            entity_id=str(document.pk),
        ).first()
        self.assertIsNotNone(audit)

        timeline = DocumentTimelineEvent.objects.filter(document=document)
        self.assertGreaterEqual(timeline.count(), 1)

    def test_upload_document_with_folder(self):
        document = self._upload_document(folder=self.folder)
        self.assertEqual(document.folder, self.folder)

    def test_upload_document_with_tags(self):
        document = self._upload_document(tags=[self.tag])
        self.assertIn(self.tag, document.tags.all())

    def test_upload_document_sets_correct_metadata(self):
        document = self._upload_document()
        self.assertEqual(document.file_extension, "pdf")
        self.assertIn("pdf", document.mime_type)
        self.assertGreater(document.file_size, 0)
        self.assertIsNotNone(document.checksum)

    def test_upload_document_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            self._upload_document(user=self.viewer)

    def test_upload_document_unauthenticated(self):
        from ..services import upload_document

        file_obj = self._make_file()
        with self.assertRaises(PermissionDenied):
            upload_document(
                user=None,
                file_obj=file_obj,
                title="No Auth",
            )


class UpdateDocumentMetadataTests(DocumentsTestCase):
    """Test document metadata update service."""

    def test_update_document_metadata(self):
        from ..services import update_document_metadata

        document = self._upload_document()
        updated = update_document_metadata(
            self.manager,
            document,
            title="Updated Title",
            description="Updated description",
        )
        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.description, "Updated description")

    def test_update_document_metadata_records_audit(self):
        from ..services import update_document_metadata

        document = self._upload_document()
        update_document_metadata(self.manager, document, title="Changed")

        audit = DocumentAuditRecord.objects.filter(
            entity_type="Document",
            entity_id=str(document.pk),
            action="METADATA_CHANGED",
        ).first()
        self.assertIsNotNone(audit)

    def test_update_metadata_requires_permission(self):
        from ..services import update_document_metadata

        document = self._upload_document()
        with self.assertRaises(PermissionDenied):
            update_document_metadata(self.viewer, document, title="Hacked")


class UploadNewVersionTests(DocumentsTestCase):
    """Test new version upload service."""

    def test_upload_new_version(self):
        from ..services import upload_new_version

        document = self._upload_document()
        new_file = self._make_file("v2.pdf", b"%PDF-1.4 version 2 content")
        version = upload_new_version(
            self.manager, document, new_file, change_summary="Updated content"
        )
        self.assertEqual(version.version_number, 2)
        self.assertTrue(version.is_current)
        document.refresh_from_db()
        self.assertEqual(document.current_version_number, 2)

    def test_upload_new_version_previous_not_current(self):
        from ..services import upload_new_version

        document = self._upload_document()
        v1 = document.versions.filter(is_current=True).first()
        new_file = self._make_file("v2.pdf", b"%PDF-1.4 version 2")
        upload_new_version(self.manager, document, new_file)
        v1.refresh_from_db()
        self.assertFalse(v1.is_current)

    def test_upload_new_version_archived_document_raises(self):
        from ..services import archive_document, upload_new_version

        document = self._upload_document()
        archive_document(self.manager, document)
        new_file = self._make_file("v3.pdf", b"%PDF-1.4 version 3")
        with self.assertRaises(DocumentVersionError):
            upload_new_version(self.manager, document, new_file)


class CheckoutTests(DocumentsTestCase):
    """Test checkout/checkin service."""

    def test_checkout_document(self):
        from ..services import checkout_document

        document = self._upload_document()
        checkout = checkout_document(self.manager, document, checkout_reason="Editing")
        self.assertEqual(checkout.status, CheckoutStatus.ACTIVE)
        self.assertEqual(checkout.checked_out_by, self.manager)

    def test_checkin_document(self):
        from ..services import checkin_document, checkout_document

        document = self._upload_document()
        checkout = checkout_document(self.manager, document)
        version = checkin_document(self.manager, checkout, checkin_notes="Done")
        self.assertIsNotNone(version)
        checkout.refresh_from_db()
        self.assertEqual(checkout.status, CheckoutStatus.RETURNED)

    def test_checkout_already_checked_out_raises(self):
        from ..services import checkout_document

        document = self._upload_document()
        checkout_document(self.manager, document)
        with self.assertRaises(DocumentCheckoutError):
            checkout_document(self.officer, document)

    def test_checkin_without_file_returns_current_version(self):
        from ..services import checkin_document, checkout_document

        document = self._upload_document()
        checkout = checkout_document(self.manager, document)
        version = checkin_document(self.manager, checkout, file_obj=None)
        self.assertIsNotNone(version)
        self.assertTrue(version.is_current)


class WorkflowTests(DocumentsTestCase):
    """Test document workflow transitions."""

    def test_submit_for_review(self):
        from ..services import submit_for_review

        document = self._upload_document()
        submitted = submit_for_review(self.manager, document)
        self.assertEqual(submitted.status, DocumentStatus.PENDING_REVIEW)
        self.assertEqual(submitted.approval_status, "PENDING_REVIEW")

    def test_approve_document(self):
        from ..services import approve_document, submit_for_review

        document = self._upload_document()
        submit_for_review(self.manager, document)
        document.status = DocumentStatus.PENDING_APPROVAL
        document.save(update_fields=["status"])
        approved = approve_document(self.manager, document)
        self.assertEqual(approved.status, DocumentStatus.APPROVED)
        self.assertEqual(approved.approval_status, "APPROVED")
        self.assertEqual(approved.approved_by, self.manager)

    def test_reject_document(self):
        from ..services import review_document, submit_for_review

        document = self._upload_document()
        submit_for_review(self.manager, document)
        returned = review_document(
            self.manager, document, approve=False, comments="Needs work"
        )
        self.assertEqual(returned.status, DocumentStatus.RETURNED_FOR_CORRECTION)

    def test_publish_document(self):
        from ..services import approve_document, publish_document, submit_for_review

        document = self._upload_document()
        submit_for_review(self.manager, document)
        document.status = DocumentStatus.PENDING_APPROVAL
        document.save(update_fields=["status"])
        approve_document(self.manager, document)
        published = publish_document(self.manager, document)
        self.assertEqual(published.status, DocumentStatus.PUBLISHED)

    def test_unpublish_document(self):
        from ..services import (
            approve_document,
            publish_document,
            submit_for_review,
            unpublish_document,
        )

        document = self._upload_document()
        submit_for_review(self.manager, document)
        document.status = DocumentStatus.PENDING_APPROVAL
        document.save(update_fields=["status"])
        approve_document(self.manager, document)
        publish_document(self.manager, document)
        unpublished = unpublish_document(self.manager, document)
        self.assertEqual(unpublished.status, DocumentStatus.APPROVED)

    def test_submit_from_invalid_status_raises(self):
        from ..services import submit_for_review

        document = self._upload_document()
        document.status = DocumentStatus.APPROVED
        document.save(update_fields=["status"])
        with self.assertRaises(DocumentWorkflowError):
            submit_for_review(self.manager, document)


class ArchiveRestoreTests(DocumentsTestCase):
    """Test document archival and restoration."""

    def test_archive_document(self):
        from ..services import archive_document

        document = self._upload_document()
        archived = archive_document(self.manager, document, reason="End of project")
        self.assertEqual(archived.status, DocumentStatus.ARCHIVED)
        self.assertTrue(archived.is_archived)
        self.assertIsNotNone(archived.archived_at)

    def test_restore_document(self):
        from ..services import archive_document, restore_document

        document = self._upload_document()
        archive_document(self.manager, document)
        restored = restore_document(self.manager, document)
        self.assertNotEqual(restored.status, DocumentStatus.ARCHIVED)
        self.assertFalse(restored.is_archived)

    def test_archive_already_archived_raises(self):
        from ..services import archive_document

        document = self._upload_document()
        archive_document(self.manager, document)
        with self.assertRaises(DocumentArchiveError):
            archive_document(self.manager, document)

    def test_restore_not_archived_raises(self):
        from ..services import restore_document

        document = self._upload_document()
        with self.assertRaises(DocumentArchiveError):
            restore_document(self.manager, document)


class ShareTests(DocumentsTestCase):
    """Test document sharing service."""

    def test_share_document(self):
        from ..services import share_document

        document = self._upload_document()
        share = share_document(
            self.manager, document, self.viewer, permission_level="VIEW"
        )
        self.assertIsNotNone(share.pk)
        self.assertTrue(share.is_active)
        self.assertEqual(share.shared_with_user, self.viewer)

    def test_revoke_share(self):
        from ..services import revoke_share, share_document

        document = self._upload_document()
        share = share_document(self.manager, document, self.viewer)
        revoke_share(self.manager, share)
        share.refresh_from_db()
        self.assertFalse(share.is_active)
        self.assertIsNotNone(share.revoked_at)
        self.assertEqual(share.revoked_by, self.manager)

    def test_revoke_already_revoked_raises(self):
        from ..services import revoke_share, share_document

        document = self._upload_document()
        share = share_document(self.manager, document, self.viewer)
        revoke_share(self.manager, share)
        with self.assertRaises(DocumentShareError):
            revoke_share(self.manager, share)


class SoftDeleteTests(DocumentsTestCase):
    """Test soft delete and restore."""

    def test_soft_delete_document(self):
        from ..services import delete_document

        document = self._upload_document()
        delete_document(self.manager, document)
        document.refresh_from_db()
        self.assertTrue(document.is_deleted)
        self.assertIsNotNone(document.deleted_at)
        self.assertEqual(document.deleted_by, self.manager)

    def test_restore_deleted_document(self):
        from ..services import delete_document, restore_deleted_document

        document = self._upload_document()
        delete_document(self.manager, document)
        restore_deleted_document(self.manager, document)
        document.refresh_from_db()
        self.assertFalse(document.is_deleted)
        self.assertIsNone(document.deleted_at)

    def test_delete_already_deleted_raises(self):
        from ..services import delete_document

        document = self._upload_document()
        delete_document(self.manager, document)
        with self.assertRaises(DocumentManagementError):
            delete_document(self.manager, document)

    def test_restore_not_deleted_raises(self):
        from ..services import restore_deleted_document

        document = self._upload_document()
        with self.assertRaises(DocumentManagementError):
            restore_deleted_document(self.manager, document)


class FolderTests(DocumentsTestCase):
    """Test folder creation service."""

    def test_create_folder(self):
        from ..services import create_folder

        folder = create_folder(self.manager, name="Project Files")
        self.assertIsNotNone(folder.pk)
        self.assertEqual(folder.name, "Project Files")
        self.assertIsNotNone(folder.reference_number)
        self.assertIsNotNone(folder.slug)


class CategoryTests(DocumentsTestCase):
    """Test category creation service."""

    def test_create_category(self):
        from ..services import create_category

        category = create_category(
            self.manager, code="finance", name="Finance Documents"
        )
        self.assertIsNotNone(category.pk)
        self.assertEqual(category.code, "finance")
        self.assertEqual(category.name, "Finance Documents")
        self.assertTrue(category.is_active)
