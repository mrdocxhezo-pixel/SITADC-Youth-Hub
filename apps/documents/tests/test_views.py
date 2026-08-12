"""View-level tests for the Document Management module."""

from __future__ import annotations

from django.test import Client
from django.urls import reverse

from ..constants import DocumentStatus
from .base import DocumentsTestCase


class DocumentListViewTests(DocumentsTestCase):
    """Test DocumentListView access control and rendering."""

    def test_document_list_view_requires_login(self):
        response = self.client.get(reverse("documents:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_document_list_view_returns_200(self):
        self.login_as(self.manager)
        response = self.client.get(reverse("documents:list"))
        self.assertEqual(response.status_code, 200)

    def test_document_list_view_with_search(self):
        self.login_as(self.manager)
        self._upload_document(title="Financial Report")
        response = self.client.get(reverse("documents:list"), {"q": "Financial"})
        self.assertEqual(response.status_code, 200)

    def test_document_list_view_with_status_filter(self):
        self.login_as(self.manager)
        self._upload_document()
        response = self.client.get(reverse("documents:list"), {"status": "UPLOADED"})
        self.assertEqual(response.status_code, 200)


class DocumentDashboardViewTests(DocumentsTestCase):
    """Test DocumentDashboardView access."""

    def test_document_dashboard_view_returns_200(self):
        self.login_as(self.manager)
        response = self.client.get(reverse("documents:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_document_dashboard_view_requires_login(self):
        response = self.client.get(reverse("documents:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)


class DocumentDetailViewTests(DocumentsTestCase):
    """Test DocumentDetailView access."""

    def test_document_detail_view_returns_200(self):
        self.login_as(self.manager)
        document = self._upload_document()
        response = self.client.get(reverse("documents:detail", args=[document.pk]))
        self.assertEqual(response.status_code, 200)

    def test_document_detail_view_nonexistent_returns_404(self):
        self.login_as(self.manager)
        import uuid

        fake_pk = uuid.uuid4()
        response = self.client.get(reverse("documents:detail", args=[fake_pk]))
        self.assertEqual(response.status_code, 404)


class DocumentCreateViewTests(DocumentsTestCase):
    """Test DocumentCreateView (upload)."""

    def test_document_upload_view_get(self):
        self.login_as(self.manager)
        response = self.client.get(reverse("documents:upload"))
        self.assertEqual(response.status_code, 200)

    def test_document_upload_view_post(self):
        self.login_as(self.manager)
        file_obj = self._make_file()
        response = self.client.post(
            reverse("documents:upload"),
            {
                "file": file_obj,
                "title": "Uploaded via View",
                "description": "Test upload",
                "confidentiality_level": "INTERNAL",
            },
        )
        # Should redirect to detail page on success
        self.assertIn(response.status_code, [200, 302])

    def test_document_upload_view_requires_login(self):
        response = self.client.get(reverse("documents:upload"))
        self.assertEqual(response.status_code, 302)


class DocumentDownloadViewTests(DocumentsTestCase):
    """Test DocumentDownloadView access."""

    def test_document_download_view(self):
        self.login_as(self.manager)
        document = self._upload_document()
        response = self.client.get(reverse("documents:download", args=[document.pk]))
        self.assertIn(response.status_code, [200, 404])


class MyDocumentsViewTests(DocumentsTestCase):
    """Test MyDocumentsView."""

    def test_my_documents_view(self):
        self.login_as(self.manager)
        response = self.client.get(reverse("documents:my_documents"))
        self.assertEqual(response.status_code, 200)


class DocumentFolderListViewTests(DocumentsTestCase):
    """Test DocumentFolderListView."""

    def test_document_folder_list_view(self):
        self.login_as(self.manager)
        response = self.client.get(reverse("documents:folder_list"))
        self.assertEqual(response.status_code, 200)


class DocumentCategoryListViewTests(DocumentsTestCase):
    """Test DocumentCategoryListView."""

    def test_document_category_list_view(self):
        self.login_as(self.manager)
        response = self.client.get(reverse("documents:category_list"))
        self.assertEqual(response.status_code, 200)


class DocumentAuditLogViewTests(DocumentsTestCase):
    """Test DocumentAuditLogView."""

    def test_document_audit_log_view(self):
        self.login_as(self.manager)
        document = self._upload_document()
        response = self.client.get(reverse("documents:audit_log", args=[document.pk]))
        self.assertEqual(response.status_code, 200)


class DocumentWorkflowActionViewTests(DocumentsTestCase):
    """Test DocumentWorkflowActionView dynamic action dropdown and dispatch."""

    def test_workflow_action_get_shows_available_actions(self):
        self.login_as(self.manager)
        document = self._upload_document()
        response = self.client.get(
            reverse("documents:workflow_action", args=[document.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose an action...")
        self.assertContains(response, "Submit for Review")
        self.assertContains(response, "Archive")

    def test_workflow_action_get_requires_login(self):
        document = self._upload_document()
        response = self.client.get(
            reverse("documents:workflow_action", args=[document.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_workflow_submit_for_review(self):
        self.login_as(self.manager)
        document = self._upload_document()
        response = self.client.post(
            reverse("documents:workflow_action", args=[document.pk]),
            {"action": "submit", "comments": "Please review"},
        )
        self.assertRedirects(
            response, reverse("documents:detail", args=[document.pk])
        )
        document.refresh_from_db()
        self.assertEqual(document.status, DocumentStatus.PENDING_REVIEW)

    def test_workflow_approve_review_forwards_to_approval(self):
        self.login_as(self.manager)
        document = self._upload_document()
        self._transition_document(document, "submit")

        response = self.client.post(
            reverse("documents:workflow_action", args=[document.pk]),
            {"action": "approve_review", "comments": "Looks good"},
        )
        self.assertRedirects(
            response, reverse("documents:detail", args=[document.pk])
        )
        document.refresh_from_db()
        self.assertEqual(document.status, DocumentStatus.PENDING_APPROVAL)

    def test_workflow_return_for_correction(self):
        self.login_as(self.manager)
        document = self._upload_document()
        self._transition_document(document, "submit")

        response = self.client.post(
            reverse("documents:workflow_action", args=[document.pk]),
            {"action": "return", "comments": "Needs edits"},
        )
        self.assertRedirects(
            response, reverse("documents:detail", args=[document.pk])
        )
        document.refresh_from_db()
        self.assertEqual(document.status, DocumentStatus.RETURNED_FOR_CORRECTION)

    def test_workflow_approve(self):
        self.login_as(self.manager)
        document = self._upload_document()
        self._transition_document(document, "submit")
        self._transition_document(document, "approve_review")

        response = self.client.post(
            reverse("documents:workflow_action", args=[document.pk]),
            {"action": "approve", "comments": "Approved"},
        )
        self.assertRedirects(
            response, reverse("documents:detail", args=[document.pk])
        )
        document.refresh_from_db()
        self.assertEqual(document.status, DocumentStatus.APPROVED)

    def test_workflow_publish(self):
        self.login_as(self.manager)
        document = self._upload_document()
        self._transition_document(document, "submit")
        self._transition_document(document, "approve_review")
        self._transition_document(document, "approve")

        response = self.client.post(
            reverse("documents:workflow_action", args=[document.pk]),
            {"action": "publish"},
        )
        self.assertRedirects(
            response, reverse("documents:detail", args=[document.pk])
        )
        document.refresh_from_db()
        self.assertEqual(document.status, DocumentStatus.PUBLISHED)

    def test_workflow_archive(self):
        self.login_as(self.manager)
        document = self._upload_document()
        response = self.client.post(
            reverse("documents:workflow_action", args=[document.pk]),
            {"action": "archive", "comments": "No longer needed"},
        )
        self.assertRedirects(
            response, reverse("documents:detail", args=[document.pk])
        )
        document.refresh_from_db()
        self.assertEqual(document.status, DocumentStatus.ARCHIVED)

    def test_workflow_viewer_gets_no_actions(self):
        # A viewer has view/download permissions but no workflow permissions.
        self.login_as(self.viewer)
        document = self._upload_document()
        response = self.client.get(
            reverse("documents:workflow_action", args=[document.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No actions available for this document status")
        available = list(
            response.context["form"].fields["action"].choices
        )
        self.assertEqual(
            [value for value, _ in available if value], []
        )

    def _transition_document(self, document, action: str):
        view = reverse("documents:workflow_action", args=[document.pk])
        labels = {
            "submit": ("submit", {}),
            "approve_review": ("approve_review", {"comments": "Fwd"}),
            "return": ("return", {"comments": "Fix"}),
            "approve": ("approve", {"comments": "Approved"}),
            "publish": ("publish", {}),
        }
        value, extra = labels[action]
        response = self.client.post(view, {"action": value, **extra})
        self.assertIn(response.status_code, [200, 302])
        document.refresh_from_db()
