"""Permission-aware selector tests for beneficiary data."""

from apps.beneficiaries.constants import ConfidentialityLevel
from apps.beneficiaries.models import BeneficiaryDocument
from apps.beneficiaries.selectors import (
    user_can_access_beneficiary,
    visible_beneficiaries,
    visible_beneficiary_documents,
)

from .base import BeneficiaryTestCase


class VisibleBeneficiarySelectorTests(BeneficiaryTestCase):
    def test_manager_sees_all_non_archived_records(self):
        internal = self.create_beneficiary(
            confidentiality=ConfidentialityLevel.CONFIDENTIAL
        )
        archived = self.create_beneficiary(is_archived=True)
        visible_ids = set(
            visible_beneficiaries(self.manager).values_list("pk", flat=True)
        )
        self.assertEqual(visible_ids, {internal.pk})
        self.assertIn(
            archived.pk,
            visible_beneficiaries(self.manager, include_archived=True).values_list(
                "pk", flat=True
            ),
        )

    def test_view_permission_user_sees_only_records_in_scope(self):
        assigned = self.create_beneficiary(primary_responsible_officer=self.viewer)
        self.create_beneficiary()
        self.grant_permissions(self.viewer, "beneficiaries.view")
        self.assertEqual(list(visible_beneficiaries(self.viewer)), [assigned])

    def test_created_by_scopes_view_permission(self):
        mine = self.create_beneficiary(created_by=self.viewer, updated_by=self.viewer)
        self.create_beneficiary()
        self.grant_permissions(self.viewer, "beneficiaries.view")
        self.assertEqual(list(visible_beneficiaries(self.viewer)), [mine])

    def test_unauthenticated_user_sees_nothing(self):
        self.create_beneficiary()
        self.assertEqual(visible_beneficiaries(None).count(), 0)

    def test_user_without_any_permission_sees_nothing(self):
        self.create_beneficiary()
        self.assertEqual(visible_beneficiaries(self.outsider).count(), 0)

    def test_view_confidential_can_see_confidential_but_not_restricted(self):
        confidential = self.create_beneficiary(
            confidentiality=ConfidentialityLevel.CONFIDENTIAL
        )
        restricted = self.create_beneficiary(
            confidentiality=ConfidentialityLevel.RESTRICTED
        )
        self.grant_permissions(self.viewer, "beneficiaries.view_confidential")
        visible_ids = set(
            visible_beneficiaries(self.viewer).values_list("pk", flat=True)
        )
        self.assertEqual(visible_ids, {confidential.pk})
        self.assertNotIn(restricted.pk, visible_ids)


class ObjectAccessSelectorTests(BeneficiaryTestCase):
    def test_user_can_access_assigned_record(self):
        beneficiary = self.create_beneficiary(primary_responsible_officer=self.viewer)
        self.grant_permissions(self.viewer, "beneficiaries.view")
        self.assertTrue(user_can_access_beneficiary(self.viewer, beneficiary))

    def test_user_cannot_access_out_of_scope_record(self):
        beneficiary = self.create_beneficiary()
        self.grant_permissions(self.viewer, "beneficiaries.view")
        self.assertFalse(user_can_access_beneficiary(self.viewer, beneficiary))

    def test_manager_can_access_archived_record_with_flag(self):
        beneficiary = self.create_beneficiary(is_archived=True)
        self.assertTrue(
            user_can_access_beneficiary(
                self.manager, beneficiary, include_archived=True
            )
        )


class VisibleDocumentSelectorTests(BeneficiaryTestCase):
    def _document(self, beneficiary):
        return BeneficiaryDocument.objects.create(
            beneficiary=beneficiary,
            reference_number=f"BND-TEST-{self._beneficiary_sequence:04d}",
            title="Consent scan",
            document_type=self.taxonomy("DOCUMENT_TYPE"),
            file="beneficiaries/documents/consent.pdf",
            file_name="consent.pdf",
            file_size=10,
            uploaded_by=self.manager,
            created_by=self.manager,
            updated_by=self.manager,
        )

    def test_documents_fail_closed_without_permission(self):
        beneficiary = self.create_beneficiary()
        self._document(beneficiary)
        self.assertEqual(
            visible_beneficiary_documents(self.viewer, beneficiary).count(), 0
        )

    def test_document_manage_user_sees_scoped_documents(self):
        beneficiary = self.create_beneficiary(created_by=self.viewer)
        doc = self._document(beneficiary)
        self.grant_permissions(
            self.viewer, "beneficiaries.view", "beneficiaries.manage_documents"
        )
        self.assertEqual(
            list(visible_beneficiary_documents(self.viewer, beneficiary)), [doc]
        )
