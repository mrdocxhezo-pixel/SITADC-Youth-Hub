"""Seed centralized Phase 15 program reference schemes."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

SCHEMES = (
    ("work_plan", "Work Plan", "WPL"),
    ("activity", "Activity", "ACT"),
    ("task", "Task", "TSK"),
    ("milestone", "Milestone", "MSL"),
    ("deliverable", "Deliverable", "DLV"),
    ("risk", "Risk", "RSK"),
    ("issue", "Issue", "ISS"),
    ("change", "Change Request", "CHG"),
    ("evidence", "Evidence", "EVD"),
    ("program_beneficiary", "Program Beneficiary", "BNF"),
)


def seed_program_schemes(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    for code, name, prefix in SCHEMES:
        ReferenceNumberScheme.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "description": f"Phase 15 reference scheme for {name.lower()} records.",
                "module": "programs",
                "record_type": code,
                "prefix": prefix,
                "pattern": "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
                "organization_code": "SITADC",
                "sequence_length": 6,
                "start_value": 1,
                "reset_period": "NEVER",
                "is_default_for_module": False,
                "is_default_for_record_type": True,
                "is_fallback": False,
                "status": "ACTIVE",
                "is_active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("references", "0004_seed_volunteer_disciplinary_scheme")]
    operations = [
        migrations.RunPython(seed_program_schemes, migrations.RunPython.noop)
    ]
