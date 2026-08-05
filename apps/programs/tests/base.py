"""Shared deterministic fixtures for program tests."""

from __future__ import annotations

from datetime import date
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase

from apps.accounts.constants import AccountStatus
from apps.programs.models import (
    Program,
    ProgramReferenceData,
    ProgramStatusHistory,
    Project,
)
from apps.programs.seed_loader import seed_program_reference_data
from apps.programs.storage import private_program_storage
from apps.rbac.authorization import clear_permission_cache

User = get_user_model()


class ProgramTestCase(TestCase):
    """Seed taxonomies, numbering, users, and isolated private storage."""

    password = "TestPassword123!"

    @classmethod
    def setUpTestData(cls):
        call_command("seed_reference_schemes", verbosity=0)
        seed_program_reference_data()
        cls.manager = cls.create_test_user("manager")
        cls.owner = cls.create_test_user("owner")
        cls.viewer = cls.create_test_user("viewer")
        cls.outsider = cls.create_test_user("outsider")
        cls.manager.user_permissions.add(
            Permission.objects.get(codename="programmes.manage")
        )

    def setUp(self):
        super().setUp()
        self._program_sequence = 0
        self._project_sequence = 0
        self.private_media = TemporaryDirectory()
        self._original_storage_location = private_program_storage._location
        private_program_storage._location = self.private_media.name
        self._clear_storage_cache()
        self.addCleanup(self._restore_private_storage)

    def _clear_storage_cache(self):
        private_program_storage.__dict__.pop("base_location", None)
        private_program_storage.__dict__.pop("location", None)

    def _restore_private_storage(self):
        private_program_storage._location = self._original_storage_location
        self._clear_storage_cache()
        self.private_media.cleanup()

    @classmethod
    def create_test_user(cls, stem: str):
        return User.objects.create_user(
            email=f"{stem}@example.com",
            username=stem,
            first_name=stem.title(),
            last_name="Tester",
            status=AccountStatus.ACTIVE,
        )

    def create_user(self, stem: str):
        return self.create_test_user(stem)

    def grant_permissions(self, user, *codes: str):
        permissions = [Permission.objects.get(codename=code) for code in codes]
        user.user_permissions.add(*permissions)
        clear_permission_cache(user)

    def taxonomy(self, kind: str, code: str | None = None):
        queryset = ProgramReferenceData.objects.filter(kind=kind, active=True)
        if code:
            queryset = queryset.filter(code=code)
        return queryset.order_by("order", "name").first()

    @staticmethod
    def parse_dates(fields: dict) -> dict:
        for key in (
            "start_date",
            "end_date",
            "due_date",
            "completion_date",
            "target_date",
            "planned_date",
            "enrollment_date",
        ):
            if key in fields and isinstance(fields[key], str):
                fields[key] = date.fromisoformat(fields[key])
        return fields

    def create_program(self, **fields):
        self._program_sequence += 1
        sequence = self._program_sequence
        created_by = fields.pop("created_by", self.manager)
        fields = self.parse_dates(fields)
        defaults = {
            "reference_number": f"PRG-TEST-{sequence:04d}",
            "title": f"Program {sequence:04d}",
            "category": self.taxonomy("CATEGORY"),
            "status": fields.pop("status", "DRAFT"),
            "created_by": created_by,
            "updated_by": created_by,
        }
        defaults.update(fields)
        return Program.objects.create(**defaults)

    def create_project(self, program=None, **fields):
        self._project_sequence += 1
        sequence = self._project_sequence
        program = program or self.create_program()
        created_by = fields.pop("created_by", self.manager)
        fields = self.parse_dates(fields)
        defaults = {
            "program": program,
            "reference_number": f"PRJ-TEST-{sequence:04d}",
            "title": f"Project {sequence:04d}",
            "category": self.taxonomy("PROJECT_CATEGORY"),
            "status": fields.pop("status", "CONCEPT"),
            "created_by": created_by,
            "updated_by": created_by,
        }
        defaults.update(fields)
        return Project.objects.create(**defaults)

    @staticmethod
    def pdf_upload(name="evidence.pdf"):
        return SimpleUploadedFile(
            name, b"%PDF-1.4\n% test document\n", "application/pdf"
        )

    @staticmethod
    def create_status_history(program=None, project=None, **fields):
        model = ProgramStatusHistory
        if project is not None:
            from apps.programs.models import ProjectStatusHistory

            model = ProjectStatusHistory
        defaults = {
            "reason": "Test transition",
        }
        defaults.update(fields)
        if model is ProgramStatusHistory:
            defaults["program"] = program
        else:
            defaults["project"] = project
        return model.objects.create(**defaults)
