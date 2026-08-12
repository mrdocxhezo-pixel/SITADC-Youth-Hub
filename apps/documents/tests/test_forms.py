"""Form-level tests for the Document Management module."""

from __future__ import annotations

from ..forms import (
    DocumentCategoryForm,
    DocumentFolderForm,
    DocumentMetadataForm,
    DocumentSearchForm,
    DocumentUploadForm,
)
from .base import DocumentsTestCase


class DocumentUploadFormTests(DocumentsTestCase):
    """Test DocumentUploadForm validation."""

    def test_document_upload_form_valid(self):
        file_obj = self._make_file()
        form = DocumentUploadForm(
            data={
                "title": "Test Upload Form",
                "description": "Description",
                "confidentiality_level": "INTERNAL",
            },
            files={"file": file_obj},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_document_upload_form_no_file_invalid(self):
        form = DocumentUploadForm(
            data={
                "title": "Missing File",
                "confidentiality_level": "INTERNAL",
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_document_upload_form_title_required(self):
        file_obj = self._make_file()
        form = DocumentUploadForm(
            data={
                "confidentiality_level": "INTERNAL",
            },
            files={"file": file_obj},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_document_upload_form_with_category(self):
        file_obj = self._make_file()
        form = DocumentUploadForm(
            data={
                "title": "With Category",
                "category": self.category.pk,
                "confidentiality_level": "INTERNAL",
            },
            files={"file": file_obj},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_document_upload_form_with_tags(self):
        file_obj = self._make_file()
        form = DocumentUploadForm(
            data={
                "title": "With Tags",
                "tags": [self.tag.pk],
                "confidentiality_level": "INTERNAL",
            },
            files={"file": file_obj},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_document_upload_form_with_keywords(self):
        file_obj = self._make_file()
        form = DocumentUploadForm(
            data={
                "title": "With Keywords",
                "keywords": "test, document, upload",
                "confidentiality_level": "INTERNAL",
            },
            files={"file": file_obj},
        )
        self.assertTrue(form.is_valid(), form.errors)


class DocumentMetadataFormTests(DocumentsTestCase):
    """Test DocumentMetadataForm validation."""

    def test_document_metadata_form_valid(self):
        document = self._upload_document()
        form = DocumentMetadataForm(
            data={
                "title": "Updated Title",
                "short_title": "Updated",
                "description": "Updated description",
                "confidentiality_level": "INTERNAL",
                "keywords": "keyword1, keyword2",
            },
            instance=document,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_document_metadata_form_empty_title_invalid(self):
        document = self._upload_document()
        form = DocumentMetadataForm(
            data={
                "title": "",
                "confidentiality_level": "INTERNAL",
            },
            instance=document,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)


class DocumentFolderFormTests(DocumentsTestCase):
    """Test DocumentFolderForm validation."""

    def test_document_folder_form_valid(self):
        form = DocumentFolderForm(
            data={
                "name": "New Folder",
                "description": "Test folder",
                "sort_order": 1,
                "confidentiality_level": "INTERNAL",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_document_folder_form_empty_name_invalid(self):
        form = DocumentFolderForm(
            data={
                "name": "",
                "sort_order": 1,
                "confidentiality_level": "INTERNAL",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class DocumentCategoryFormTests(DocumentsTestCase):
    """Test DocumentCategoryForm validation."""

    def test_document_category_form_valid(self):
        form = DocumentCategoryForm(
            data={
                "code": "finance",
                "name": "Finance",
                "description": "Finance documents",
                "sort_order": 1,
                "default_confidentiality": "INTERNAL",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_document_category_form_empty_code_invalid(self):
        form = DocumentCategoryForm(
            data={
                "code": "",
                "name": "Finance",
                "sort_order": 1,
                "default_confidentiality": "INTERNAL",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("code", form.errors)

    def test_document_category_form_empty_name_invalid(self):
        form = DocumentCategoryForm(
            data={
                "code": "finance",
                "name": "",
                "sort_order": 1,
                "default_confidentiality": "INTERNAL",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class DocumentSearchFormTests(DocumentsTestCase):
    """Test DocumentSearchForm validation."""

    def test_document_search_form_valid(self):
        form = DocumentSearchForm(data={"q": "test search"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_document_search_form_empty_valid(self):
        form = DocumentSearchForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_document_search_form_with_filters(self):
        form = DocumentSearchForm(
            data={
                "q": "report",
                "category": self.category.pk,
                "document_type": self.doc_type.pk,
                "status": "UPLOADED",
                "confidentiality_level": "INTERNAL",
                "sort_by": "-created_at",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
