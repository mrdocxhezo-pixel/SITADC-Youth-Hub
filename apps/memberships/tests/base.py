"""
Shared test fixtures for the membership management module.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.memberships.seed_loader import seed_membership_configuration
from apps.references.constants import ReferenceModules
from apps.references.models import ReferenceNumberScheme

User = get_user_model()


class MembershipTestCase(TestCase):
    """Base test case that seeds the membership configuration and schemes."""

    def setUp(self):
        seed_membership_configuration()
        self._seed_schemes()
        self.admin = User.objects.create_user(
            email="admin@example.com",
            username="memberadmin",
            first_name="Admin",
            last_name="Member",
            is_staff=True,
            is_superuser=True,
        )
        self.user = User.objects.create_user(
            email="member@example.com",
            username="memberuser",
            first_name="Member",
            last_name="User",
        )

    def _seed_schemes(self):
        schemes = [
            ("member", "member", "MEM"),
            ("membership_application", "application", "APL"),
            ("membership_receipt", "receipt", "RCT"),
            ("membership_card", "card", "CRD"),
        ]
        for code, record_type, prefix in schemes:
            ReferenceNumberScheme.objects.get_or_create(
                module=ReferenceModules.MEMBERSHIPS,
                record_type=record_type,
                prefix=prefix,
                defaults={
                    "name": code,
                    "code": code,
                    "pattern": "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
                    "organization_code": "SITADC",
                    "sequence_length": 6,
                    "is_default_for_record_type": True,
                    "is_default_for_module": record_type == "member",
                    "status": "ACTIVE",
                },
            )
