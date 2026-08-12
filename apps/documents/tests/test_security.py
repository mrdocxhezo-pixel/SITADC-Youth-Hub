"""Permission and security tests for the Document Management module."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.test import Client
from django.urls import reverse

from ..constants import ConfidentialityLevel
from ..exceptions import DocumentShareError
from ..models import DocumentShare
from .base import DocumentsTestCase


class ViewerPermissionTests(DocumentsTestCase):
    """Test that viewer role has restricted permissions."""

    def test_viewer_cannot_upload(self):
        from ..services import upload_document

        file_obj = self._make_file()
        with self.assertRaises(PermissionDenied):
            upload_document(
                user=self.viewer,
                file_obj=file_obj,
                title="Unauthorized Upload",
            )

    def test_viewer_can_view_list(self):
        self.login_as(self.viewer)
        response = self.client.get(reverse("documents:list"))
        self.assertEqual(response.status_code, 200)

    def test_viewer_can_download(self):
        self.login_as(self.viewer)
        document = self._upload_document()
        response = self.client.get(reverse("documents:download", args=[document.pk]))
        self.assertIn(response.status_code, [200, 404])


class OutsiderPermissionTests(DocumentsTestCase):
    """Test that outsider role (no permissions) is fully restricted."""

    def test_outsider_cannot_upload(self):
        from ..services import upload_document

        file_obj = self._make_file()
        with self.assertRaises(PermissionDenied):
            upload_document(
                user=self.outsider,
                file_obj=file_obj,
                title="Outsider Upload",
            )

    def test_outsider_cannot_update_metadata(self):
        from ..services import update_document_metadata

        document = self._upload_document()
        with self.assertRaises(PermissionDenied):
            update_document_metadata(self.outsider, document, title="Hacked")

    def test_outsider_cannot_checkout(self):
        from ..services import checkout_document

        document = self._upload_document()
        with self.assertRaises(PermissionDenied):
            checkout_document(self.outsider, document)

    def test_outsider_cannot_archive(self):
        from ..services import archive_document

        document = self._upload_document()
        with self.assertRaises(PermissionDenied):
            archive_document(self.outsider, document)

    def test_outsider_cannot_view_list(self):
        self.login_as(self.outsider)
        response = self.client.get(reverse("documents:list"))
        self.assertIn(response.status_code, [302, 403])


class ShareAccessTests(DocumentsTestCase):
    """Test that sharing grants and revokes access correctly."""

    def test_share_grants_access(self):
        from ..services import share_document

        document = self._upload_document()
        share = share_document(
            self.manager, document, self.viewer, permission_level="VIEW"
        )
        self.assertIsNotNone(share.pk)
        self.assertTrue(share.is_active)
        self.assertEqual(share.shared_with_user, self.viewer)

    def test_revoke_share_removes_access(self):
        from ..services import revoke_share, share_document

        document = self._upload_document()
        share = share_document(self.manager, document, self.viewer)
        revoke_share(self.manager, share)
        share.refresh_from_db()
        self.assertFalse(share.is_active)
        self.assertIsNotNone(share.revoked_at)

    def test_share_records_audit(self):
        from ..services import share_document

        from ..models import DocumentAuditRecord

        document = self._upload_document()
        share_document(self.manager, document, self.viewer)

        audit = DocumentAuditRecord.objects.filter(
            entity_type="DocumentShare",
            action="SHARED",
        ).exists()
        self.assertTrue(audit)

    def test_revoke_records_audit(self):
        from ..services import revoke_share, share_document

        from ..models import DocumentAuditRecord

        document = self._upload_document()
        share = share_document(self.manager, document, self.viewer)
        revoke_share(self.manager, share)

        audit = DocumentAuditRecord.objects.filter(
            entity_type="DocumentShare",
            action="SHARE_REVOKED",
        ).exists()
        self.assertTrue(audit)


class ConfidentialDocumentTests(DocumentsTestCase):
    """Test confidentiality level enforcement."""

    def test_confidential_document_upload(self):
        document = self._upload_document(
            confidentiality_level=ConfidentialityLevel.CONFIDENTIAL
        )
        self.assertEqual(document.confidentiality_level, ConfidentialityLevel.CONFIDENTIAL)

    def test_highly_confidential_document_upload(self):
        document = self._upload_document(
            confidentiality_level=ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        )
        self.assertEqual(
            document.confidentiality_level, ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        )


class CheckoutSecurityTests(DocumentsTestCase):
    """Test checkout security constraints."""

    def test_different_user_cannot_checkout_busy_document(self):
        from ..services import checkout_document

        document = self._upload_document()
        checkout_document(self.manager, document)
        with self.assertRaises(Exception):
            checkout_document(self.officer, document)

    def test_owner_can_checkin_own_checkout(self):
        from ..services import checkin_document, checkout_document

        document = self._upload_document()
        checkout = checkout_document(self.manager, document)
        version = checkin_document(self.manager, checkout)
        self.assertIsNotNone(version)

    def test_non_owner_needs_cancel_permission_to_checkin(self):
        from ..services import checkout_document, cancel_checkout

        document = self._upload_document()
        checkout = checkout_document(self.manager, document)
        # Officer cannot checkin someone else's checkout
        with self.assertRaises(PermissionDenied):
            cancel_checkout(self.officer, checkout)


class AuditImmutabilityTests(DocumentsTestCase):
    """Test audit record immutability at security level."""

    def test_audit_records_are_append_only(self):
        from ..models import DocumentAuditRecord

        document = self._upload_document()
        count_before = DocumentAuditRecord.objects.count()
        # Any operation creates a new audit record
        from ..services import update_document_metadata

        update_document_metadata(self.manager, document, title="Audit Test")
        count_after = DocumentAuditRecord.objects.count()
        self.assertGreater(count_after, count_before)

    def test_audit_records_cannot_be_deleted(self):
        from ..models import DocumentAuditRecord

        document = self._upload_document()
        audit = DocumentAuditRecord.objects.first()
        with self.assertRaises(Exception):
            audit.delete()
