"""Permission helper and confidentiality-aware selector tests."""

from django.contrib.auth.models import AnonymousUser

from apps.registers.constants import ConfidentialityLevel
from apps.registers.permissions import (
    user_can_act_on_entries,
    user_can_export,
    user_can_manage_registers,
    user_can_view_confidential,
    user_can_view_registers,
)
from apps.registers.selectors import (
    category_queryset,
    entry_queryset,
    register_queryset,
    template_queryset,
    user_can_access_entry,
    user_can_access_register,
    visible_entries,
    visible_registers,
)

from .base import RegistersTestCase


class PermissionHelperTests(RegistersTestCase):
    def setUp(self):
        super().setUp()
        self.confidential_viewer = self.create_user("confidential_viewer")
        self.grant_permissions(
            self.confidential_viewer,
            "registers.view",
            "registers.view_confidential",
        )

    def test_user_can_view_registers(self):
        self.assertTrue(user_can_view_registers(self.manager))
        self.assertTrue(user_can_view_registers(self.viewer))
        self.assertFalse(user_can_view_registers(self.outsider))

    def test_user_can_manage_registers(self):
        self.assertTrue(user_can_manage_registers(self.manager))
        self.assertFalse(user_can_manage_registers(self.viewer))

    def test_user_can_export(self):
        self.assertTrue(user_can_export(self.manager))
        self.assertTrue(user_can_export(self.officer))
        self.assertFalse(user_can_export(self.viewer))

    def test_view_confidential_requires_flag(self):
        self.assertTrue(user_can_view_confidential(self.manager))
        self.assertFalse(user_can_view_confidential(self.viewer))
        self.assertTrue(user_can_view_confidential(self.confidential_viewer))

    def test_user_can_act_on_entries(self):
        self.assertTrue(user_can_act_on_entries(self.officer))
        self.assertFalse(user_can_act_on_entries(self.viewer))


class SelectorTests(RegistersTestCase):
    def setUp(self):
        super().setUp()
        self.confidential_viewer = self.create_user("confidential_viewer")
        self.grant_permissions(
            self.confidential_viewer,
            "registers.view",
            "registers.view_confidential",
        )
        self.public_entry = self.create_register_entry()
        self.confidential_entry = self.make_confidential_entry()

    def test_querysets_fail_closed_for_outsider(self):
        self.assertFalse(register_queryset(self.outsider).exists())
        self.assertFalse(entry_queryset(self.outsider).exists())
        self.assertFalse(category_queryset(self.outsider).exists())
        self.assertFalse(template_queryset(self.outsider).exists())

    def test_unauthenticated_user_sees_nothing(self):
        anonymous = AnonymousUser()
        self.assertFalse(visible_registers(anonymous).exists())
        self.assertFalse(visible_entries(anonymous).exists())

    def test_visible_entries_hide_confidential(self):
        visible = visible_entries(self.viewer)
        visible_pks = list(visible.values_list("pk", flat=True))
        self.assertNotIn(self.confidential_entry.pk, visible_pks)
        self.assertEqual(visible.filter(pk=self.public_entry.pk).count(), 1)

    def test_confidential_visible_with_permission(self):
        visible = visible_entries(self.confidential_viewer)
        visible_pks = list(visible.values_list("pk", flat=True))
        self.assertIn(self.confidential_entry.pk, visible_pks)

    def test_confidential_register_hidden(self):
        category = self.create_category("Confidential", "confidential", "CFD")
        register = self.create_register(category, self.manager)
        register.confidentiality = ConfidentialityLevel.CONFIDENTIAL
        register.save(update_fields=["confidentiality"])
        self.assertNotIn(
            register.pk,
            list(visible_registers(self.viewer).values_list("pk", flat=True)),
        )
        self.assertIn(
            register.pk,
            list(
                visible_registers(self.confidential_viewer).values_list("pk", flat=True)
            ),
        )

    def test_user_can_access_entry(self):
        self.assertTrue(user_can_access_entry(self.viewer, self.public_entry))
        self.assertFalse(user_can_access_entry(self.viewer, self.confidential_entry))
        self.assertTrue(
            user_can_access_entry(self.confidential_viewer, self.confidential_entry)
        )

    def test_user_can_access_register(self):
        self.assertTrue(user_can_access_register(self.viewer, self.register))
        self.assertFalse(user_can_access_register(self.outsider, self.register))
