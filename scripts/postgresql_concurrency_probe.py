"""Probe stakeholder write concurrency against PostgreSQL only."""

from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.postgresql_acceptance")

import django

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.db import close_old_connections, connection  # noqa: E402

from apps.accounts.constants import AccountStatus  # noqa: E402
from apps.stakeholders.models import Stakeholder  # noqa: E402
from apps.stakeholders.services import StakeholderService  # noqa: E402


def _create_stakeholder(user_id, run_id: str, index: int) -> str:
    close_old_connections()
    try:
        user = get_user_model().objects.get(pk=user_id)
        stakeholder = StakeholderService(user=user).create(
            legal_name=f"PostgreSQL Concurrency Probe {run_id} {index:02d}"
        )
        return stakeholder.reference_number
    finally:
        close_old_connections()


def _update_stakeholder(user_id, stakeholder_id, index: int) -> None:
    close_old_connections()
    try:
        user = get_user_model().objects.get(pk=user_id)
        stakeholder = Stakeholder.objects.get(pk=stakeholder_id)
        StakeholderService(user=user).update(
            stakeholder,
            relationship_challenges=f"Concurrent update {index:02d}",
        )
    finally:
        close_old_connections()


def main() -> None:
    if connection.vendor != "postgresql":
        raise RuntimeError("This probe must run against PostgreSQL.")

    User = get_user_model()
    user, _ = User.objects.update_or_create(
        email="phase14-postgresql-probe@example.test",
        defaults={
            "username": "phase14-postgresql-probe",
            "first_name": "PostgreSQL",
            "last_name": "Probe",
            "status": AccountStatus.ACTIVE,
            "email_verified": True,
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
        },
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])

    run_id = uuid4().hex[:8]

    with ThreadPoolExecutor(max_workers=8) as executor:
        references = list(
            executor.map(
                lambda index: _create_stakeholder(user.pk, run_id, index), range(20)
            )
        )

    if len(references) != 20 or len(set(references)) != 20:
        raise RuntimeError("Concurrent reference issuance was not unique.")

    target = Stakeholder.objects.get(
        legal_name=f"PostgreSQL Concurrency Probe {run_id} 00"
    )
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda index: _update_stakeholder(user.pk, target.pk, index),
                range(20),
            )
        )

    target.refresh_from_db()
    print(
        "PostgreSQL concurrency probe passed: "
        f"{len(references)} unique creates, 20 serialized updates, "
        f"final value={target.relationship_challenges!r}."
    )


if __name__ == "__main__":
    main()
