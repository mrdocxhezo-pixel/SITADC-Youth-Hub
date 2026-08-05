"""Seed the volunteer disciplinary reference scheme."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations


def seed_volunteer_disciplinary_scheme(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    ReferenceNumberScheme.objects.update_or_create(
        module="volunteers",
        record_type="disciplinary",
        prefix="VDC",
        defaults={
            "code": "volunteer_disciplinary",
            "name": "Volunteer Disciplinary Record",
            "description": "Centralized references for volunteer disciplinary records.",
            "organization_code": "SITADC",
            "pattern": "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
            "sequence_length": 6,
            "start_value": 1,
            "reset_period": "NEVER",
            "status": "ACTIVE",
            "is_default_for_module": False,
            "is_default_for_record_type": True,
            "is_fallback": False,
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("references", "0003_seed_stakeholder_reference_schemes")]

    operations = [
        migrations.RunPython(
            seed_volunteer_disciplinary_scheme,
            migrations.RunPython.noop,
        )
    ]
