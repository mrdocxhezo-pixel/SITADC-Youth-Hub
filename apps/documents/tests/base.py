"""Shared fixtures for Document Management module tests."""

from __future__ import annotations

from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import InMemoryUploadedFile

# Python 3.14 + Django 5.0.7 compatibility: fix Context.__copy__
from django.template.context import Context as _Ctx
from django.test import TestCase

from apps.accounts.constants import AccountStatus
from apps.rbac.authorization import clear_permission_cache

from ..constants import (
    ConfidentialityLevel,
    DocumentPermissions,
)
from ..models import (
    DocumentCategory,
    DocumentFolder,
    DocumentTag,
    DocumentType,
    RetentionCategory,
)

if not hasattr(_Ctx, "_patched_copy"):

    def _patched_copy(self):
        dup = object.__new__(self.__class__)
        dup.__dict__.update(self.__dict__)
        dup.dicts = self.dicts[:]
        return dup

    _Ctx.__copy__ = _patched_copy
    _Ctx._patched_copy = True

User = get_user_model()


class DocumentsTestCase(TestCase):
    """Set up default users, permissions, and seed data for document tests."""

    password = "TestPass123!"

    @classmethod
    def setUpTestData(cls):
        from django.apps import apps
        from django.contrib.auth.management import create_permissions

        for app_config in apps.get_app_configs():
            app_config.models_module = True
            create_permissions(app_config, verbosity=0)

        from apps.references.constants import ReferenceModules, SequenceResetPeriod
        from apps.references.models import ReferenceNumberScheme

        ReferenceNumberScheme.objects.get_or_create(
            code="document",
            defaults={
                "name": "Document Reference",
                "module": ReferenceModules.DOCUMENTS,
                "prefix": "DOC",
                "sequence_length": 6,
                "reset_period": SequenceResetPeriod.NEVER,
                "is_active": True,
            },
        )

        # Create seed data for categories, types, folders, tags, retention
        cls.category = DocumentCategory.objects.create(
            code="general",
            name="General Documents",
            description="General purpose documents",
            created_by=None,
            is_active=True,
            sort_order=1,
        )
        cls.doc_type = DocumentType.objects.create(
            code="POL",
            name="Policy",
            description="Policy documents",
            category=cls.category,
            requires_approval=True,
            requires_versioning=True,
            created_by=None,
            is_active=True,
        )
        cls.folder = DocumentFolder.objects.create(
            reference_number="FOLDER-001",
            name="Root Folder",
            slug="root-folder",
            description="Root document folder",
            is_active=True,
            created_by=None,
            updated_by=None,
        )
        cls.tag = DocumentTag.objects.create(
            name="Important",
            slug="important",
            description="Important documents",
            created_by=None,
            is_active=True,
        )
        cls.retention_category = RetentionCategory.objects.create(
            code="standard",
            name="Standard Retention",
            description="7 year retention",
            retention_period_days=2555,
            created_by=None,
            is_active=True,
        )

        # Create users
        cls.admin = cls._create_user("admin")
        cls.admin.is_superuser = True
        cls.admin.is_staff = True
        cls.admin.save()

        cls.manager = cls._create_user("manager")
        cls.officer = cls._create_user("officer")
        cls.viewer = cls._create_user("viewer")
        cls.outsider = cls._create_user("outsider")

        # Get or create content type for documents app
        ct, _ = ContentType.objects.get_or_create(
            app_label="documents", model="document"
        )

        # Define all document permissions
        all_doc_perm_codes = [
            DocumentPermissions.VIEW,
            DocumentPermissions.VIEW_OWN,
            DocumentPermissions.VIEW_UNIT,
            DocumentPermissions.VIEW_SENSITIVE,
            DocumentPermissions.VIEW_CONFIDENTIAL,
            DocumentPermissions.UPLOAD,
            DocumentPermissions.CREATE,
            DocumentPermissions.UPDATE_METADATA,
            DocumentPermissions.UPLOAD_VERSION,
            DocumentPermissions.CHECKOUT,
            DocumentPermissions.CHECKIN,
            DocumentPermissions.CANCEL_CHECKOUT,
            DocumentPermissions.SUBMIT,
            DocumentPermissions.REVIEW,
            DocumentPermissions.RETURN_FOR_CORRECTION,
            DocumentPermissions.APPROVE,
            DocumentPermissions.PUBLISH,
            DocumentPermissions.UNPUBLISH,
            DocumentPermissions.ARCHIVE,
            DocumentPermissions.RESTORE,
            DocumentPermissions.REQUEST_DISPOSAL,
            DocumentPermissions.APPROVE_DISPOSAL,
            DocumentPermissions.DOWNLOAD,
            DocumentPermissions.PRINT,
            DocumentPermissions.SHARE_INTERNAL,
            DocumentPermissions.SHARE_EXTERNAL,
            DocumentPermissions.MANAGE_CATEGORIES,
            DocumentPermissions.MANAGE_TYPES,
            DocumentPermissions.MANAGE_FOLDERS,
            DocumentPermissions.MANAGE_TAGS,
            DocumentPermissions.MANAGE_RETENTION,
            DocumentPermissions.VIEW_HISTORY,
            DocumentPermissions.VIEW_AUDIT,
        ]

        # Create Permission objects — use the full RBAC code as the codename
        perms = {}
        for code in all_doc_perm_codes:
            perm, _ = Permission.objects.get_or_create(
                codename=code,
                content_type=ct,
                defaults={"name": f"Can {code}"},
            )
            perms[code] = perm

        # Manager gets most permissions
        cls.manager.user_permissions.add(
            perms[DocumentPermissions.VIEW],
            perms[DocumentPermissions.UPLOAD],
            perms[DocumentPermissions.CREATE],
            perms[DocumentPermissions.UPDATE_METADATA],
            perms[DocumentPermissions.UPLOAD_VERSION],
            perms[DocumentPermissions.CHECKOUT],
            perms[DocumentPermissions.CHECKIN],
            perms[DocumentPermissions.CANCEL_CHECKOUT],
            perms[DocumentPermissions.SUBMIT],
            perms[DocumentPermissions.REVIEW],
            perms[DocumentPermissions.RETURN_FOR_CORRECTION],
            perms[DocumentPermissions.APPROVE],
            perms[DocumentPermissions.PUBLISH],
            perms[DocumentPermissions.UNPUBLISH],
            perms[DocumentPermissions.ARCHIVE],
            perms[DocumentPermissions.RESTORE],
            perms[DocumentPermissions.REQUEST_DISPOSAL],
            perms[DocumentPermissions.APPROVE_DISPOSAL],
            perms[DocumentPermissions.DOWNLOAD],
            perms[DocumentPermissions.PRINT],
            perms[DocumentPermissions.SHARE_INTERNAL],
            perms[DocumentPermissions.MANAGE_CATEGORIES],
            perms[DocumentPermissions.MANAGE_TYPES],
            perms[DocumentPermissions.MANAGE_FOLDERS],
            perms[DocumentPermissions.MANAGE_TAGS],
            perms[DocumentPermissions.MANAGE_RETENTION],
            perms[DocumentPermissions.VIEW_HISTORY],
            perms[DocumentPermissions.VIEW_AUDIT],
        )
        cls.officer.user_permissions.add(
            perms[DocumentPermissions.VIEW],
            perms[DocumentPermissions.UPLOAD],
            perms[DocumentPermissions.CREATE],
            perms[DocumentPermissions.UPDATE_METADATA],
            perms[DocumentPermissions.UPLOAD_VERSION],
            perms[DocumentPermissions.CHECKOUT],
            perms[DocumentPermissions.CHECKIN],
            perms[DocumentPermissions.SUBMIT],
            perms[DocumentPermissions.DOWNLOAD],
            perms[DocumentPermissions.SHARE_INTERNAL],
        )

        # Viewer gets view + download only
        cls.viewer.user_permissions.add(
            perms[DocumentPermissions.VIEW],
            perms[DocumentPermissions.DOWNLOAD],
        )

        # Clear permission caches
        for user in [cls.admin, cls.manager, cls.officer, cls.viewer, cls.outsider]:
            clear_permission_cache(user)

    @classmethod
    def _create_user(cls, stem: str) -> User:
        return User.objects.create_user(
            email=f"{stem}@example.com",
            username=f"{stem}@example.com",
            first_name=stem.title(),
            last_name="Tester",
            status=AccountStatus.ACTIVE,
            password=cls.password,
        )

    def login_as(self, user):
        """Authenticate a test user."""
        return self.client.login(email=user.email, password=self.password)

    def grant_permissions(self, user, *codenames: str):
        perms = [Permission.objects.get(codename=code) for code in codenames]
        user.user_permissions.add(*perms)
        clear_permission_cache(user)

    @staticmethod
    def _make_file(
        filename: str = "test_document.pdf",
        content: bytes = b"%PDF-1.4 fake pdf content",
        content_type: str = "application/pdf",
    ) -> InMemoryUploadedFile:
        """Create an InMemoryUploadedFile for testing."""
        file_obj = BytesIO(content)
        return InMemoryUploadedFile(
            file=file_obj,
            field_name="file",
            name=filename,
            content_type=content_type,
            size=len(content),
            charset=None,
        )

    @staticmethod
    def _make_uploaded_file(
        filename: str = "test_document.pdf",
        content: bytes = b"%PDF-1.4 fake pdf content",
    ):
        """Alias for _make_file for clarity."""
        return DocumentsTestCase._make_file(filename, content)

    def _upload_document(self, user=None, **overrides):
        """Helper to upload a document via the service layer."""
        from ..services import upload_document

        user = user or self.manager
        file_obj = self._make_file()
        defaults = {
            "user": user,
            "file_obj": file_obj,
            "title": "Test Document",
            "description": "A test document",
            "category": self.category,
            "document_type": self.doc_type,
            "folder": self.folder,
            "confidentiality_level": ConfidentialityLevel.INTERNAL,
            "tags": [self.tag],
        }
        defaults.update(overrides)
        return upload_document(**defaults)
