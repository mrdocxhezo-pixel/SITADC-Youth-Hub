"""Seed the base Phase 17 beneficiary record reference scheme.

The migration 0006 seeded the beneficiary operation sub-schemes but not the
authoritative beneficiary profile scheme (code ``beneficiary``), which is the
default scheme for the ``beneficiaries`` module.  This migration backfills it
so every installation has a consistent numbering context regardless of whether
``seed_reference_data`` has been run.
"""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations


def seed_beneficiary_record_scheme(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    ReferenceNumberScheme.objects.update_or_create(
        code="beneficiary",
        defaults={
            "name": "Beneficiary",
            "description": "Phase 17 reference scheme for beneficiary records.",
            "module": "beneficiaries",
            "record_type": "beneficiary",
            "prefix": "BEN",
            "pattern": "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
            "organization_code": "SITADC",
            "sequence_length": 6,
            "start_value": 1,
            "reset_period": "NEVER",
            "is_default_for_module": True,
            "is_default_for_record_type": True,
            "is_fallback": False,
            "status": "ACTIVE",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("references", "0006_seed_beneficiary_reference_schemes")]
    operations = [
        migrations.RunPython(seed_beneficiary_record_scheme, migrations.RunPython.noop)
    ]
