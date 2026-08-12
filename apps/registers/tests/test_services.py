"""Transactional service behaviour and RBAC enforcement tests."""

from django.core.exceptions import PermissionDenied, ValidationError

from apps.registers.constants import (
    RegisterActivityAction,
    RegisterApprovalStatus,
    RegisterEntryStatus,
    RegisterStatus,
)
from apps.registers.models import RegisterActivity, RegisterReview, RegisterVersion
from apps.registers.services import (
    RegisterCategoryService,
    RegisterEntryService,
    RegisterService,
    RegisterTemplateService,
    RegisterValidationService,
)

from .base import RegistersTestCase


class RegisterCategoryServiceTests(RegistersTestCase):
    def test_create_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            RegisterCategoryService(user=self.viewer).execute(
                name="Denied", code="denied", number_prefix="DEN"
            )

    def test_update_records_activity(self):
        category = self.create_category("Assets", "assets", "AST")
        RegisterCategoryService(user=self.manager).execute(
            instance=category,
            name="Asset Registers",
            code=category.code,
            number_prefix="AST",
        )
        category.refresh_from_db()
        self.assertEqual(category.name, "Asset Registers")


class RegisterServiceTests(RegistersTestCase):
    def test_create_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            RegisterService(user=self.viewer).execute(
                name="Denied",
                code="denied_register",
                category=self.category,
                owner=self.viewer,
            )

    def test_create_assigns_reference_and_activity(self):
        register = self.create_register(self.category, self.manager)
        self.assertTrue(register.reference_number.startswith("SITADC/REG/"))
        self.assertTrue(
            RegisterActivity.objects.filter(
                register=register, action=RegisterActivityAction.CREATED
            ).exists()
        )

    def test_archive_and_restore(self):
        register = self.create_register(self.category, self.manager)
        RegisterService(user=self.manager).archive(instance=register)
        register.refresh_from_db()
        self.assertEqual(register.status, RegisterStatus.ARCHIVED)
        RegisterService(user=self.manager).restore(instance=register)
        register.refresh_from_db()
        self.assertEqual(register.status, RegisterStatus.ACTIVE)

    def test_archive_requires_archive_permission(self):
        register = self.create_register(self.category, self.manager)
        with self.assertRaises(PermissionDenied):
            RegisterService(user=self.viewer).archive(instance=register)


class RegisterTemplateServiceTests(RegistersTestCase):
    def setUp(self):
        super().setUp()
        self.template_officer = self.create_user("template_officer")
        self.grant_permissions(
            self.template_officer, "registers.create", "registers.view"
        )

    def test_create_template(self):
        template = RegisterTemplateService(user=self.template_officer).execute(
            name="Membership Intake",
            code="membership_intake",
            register=self.register,
            fields=[
                {
                    "key": "code",
                    "label": "Code",
                    "type": "TEXT",
                    "required": True,
                }
            ],
            validation_rules=[
                {"code": "code_required", "field": "code", "rule": "required"}
            ],
        )
        self.assertEqual(template.register, self.register)
        self.assertEqual(template.fields[0]["key"], "code")


class RegisterEntryServiceTests(RegistersTestCase):
    def test_create_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            RegisterEntryService(user=self.viewer).execute(
                register=self.register,
                title="Denied entry",
            )

    def test_create_assigns_reference_and_version(self):
        entry = self.create_register_entry()
        self.assertTrue(entry.reference_number.startswith("SITADC/REG/MEM/"))
        self.assertEqual(RegisterVersion.objects.filter(entry=entry).count(), 1)
        self.assertEqual(entry.approval_status, RegisterApprovalStatus.DRAFT)

    def test_confidential_entry_guarded_from_updater(self):
        entry = self.make_confidential_entry()
        restricted = self.create_user("restricted_updater")
        self.grant_permissions(restricted, "registers.view", "registers.update")
        with self.assertRaises(PermissionDenied):
            RegisterEntryService(user=restricted).execute(
                instance=entry,
                register=entry.register,
                title="Tampered title",
            )

    def test_full_approval_workflow(self):
        entry = self.approve_through_workflow(self.create_register_entry())
        self.assertEqual(entry.approval_status, RegisterApprovalStatus.APPROVED)
        self.assertEqual(entry.status, RegisterEntryStatus.ACTIVE)
        self.assertEqual(entry.approved_by, self.officer)
        self.assertTrue(RegisterReview.objects.filter(entry=entry).exists())
        self.assertTrue(
            RegisterActivity.objects.filter(
                entry=entry, action=RegisterActivityAction.APPROVED
            ).exists()
        )

    def test_invalid_transition_rejected(self):
        entry = self.create_register_entry()
        with self.assertRaises(ValidationError):
            RegisterEntryService(user=self.officer).approve(instance=entry)

    def test_submit_requires_submit_permission(self):
        entry = self.create_register_entry()
        restricted = self.create_user("submit_restricted")
        self.grant_permissions(restricted, "registers.view", "registers.create")
        with self.assertRaises(PermissionDenied):
            RegisterEntryService(user=restricted).submit(instance=entry)

    def test_return_and_resubmit_cycle(self):
        entry = self.create_register_entry()
        service = RegisterEntryService(user=self.officer)
        service.submit(instance=entry)
        entry.refresh_from_db()
        service.start_review(instance=entry)
        entry.refresh_from_db()
        service.return_entry(instance=entry)
        entry.refresh_from_db()
        self.assertEqual(entry.approval_status, RegisterApprovalStatus.RETURNED)
        service.submit(instance=entry)
        entry.refresh_from_db()
        self.assertEqual(entry.approval_status, RegisterApprovalStatus.SUBMITTED)

    def test_archive_and_restore_entry(self):
        entry = self.create_register_entry()
        RegisterEntryService(user=self.officer).archive(instance=entry)
        entry.refresh_from_db()
        self.assertEqual(entry.status, RegisterEntryStatus.ARCHIVED)
        RegisterEntryService(user=self.officer).restore(instance=entry)
        entry.refresh_from_db()
        self.assertEqual(entry.status, RegisterEntryStatus.ACTIVE)


class RegisterValidationServiceTests(RegistersTestCase):
    def setUp(self):
        super().setUp()
        self.validation_officer = self.create_user("validation_officer")
        self.grant_permissions(
            self.validation_officer,
            "registers.create",
            "registers.update",
            "registers.view",
        )
        self.template = RegisterTemplateService(user=self.validation_officer).execute(
            name="Validated",
            code="validated_template",
            register=self.register,
            fields=[],
            validation_rules=[
                {
                    "code": "score_min",
                    "field": "score",
                    "rule": "min_value",
                    "value": 10,
                },
                {
                    "code": "title_required",
                    "field": "title",
                    "rule": "required",
                },
            ],
        )

    def test_validation_records_results(self):
        entry = RegisterEntryService(user=self.validation_officer).execute(
            register=self.register,
            title="Validated entry",
            template=self.template,
            field_data={"score": 20, "title": "Validated entry"},
        )
        results = RegisterValidationService(user=self.validation_officer).execute(
            instance=entry
        )
        self.assertEqual(len(results), 2)
        results_by_code = {r.rule_code: r for r in results}
        self.assertTrue(results_by_code["score_min"].passed)
        self.assertTrue(results_by_code["title_required"].passed)

    def test_failed_rule_recorded(self):
        entry = RegisterEntryService(user=self.validation_officer).execute(
            register=self.register,
            title="Low score",
            template=self.template,
            field_data={"score": 3},
        )
        results = RegisterValidationService(user=self.validation_officer).execute(
            instance=entry
        )
        results_by_code = {r.rule_code: r for r in results}
        self.assertFalse(results_by_code["score_min"].passed)
