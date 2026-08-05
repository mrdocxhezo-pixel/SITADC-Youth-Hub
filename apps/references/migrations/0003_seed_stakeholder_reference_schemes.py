"""Seed centralized Phase 14 stakeholder reference schemes."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

SCHEMES = (
    ("stakeholder", "Stakeholder", "STK"),
    ("stakeholder_engagement", "Stakeholder Engagement", "SEG"),
    ("stakeholder_agreement", "Stakeholder Agreement", "SAG"),
    ("stakeholder_commitment", "Stakeholder Commitment", "SCM"),
    ("stakeholder_contribution", "Stakeholder Contribution", "SCN"),
    ("stakeholder_assessment", "Stakeholder Assessment", "SAS"),
    ("stakeholder_performance", "Stakeholder Performance", "SPF"),
    ("stakeholder_due_diligence", "Stakeholder Due Diligence", "SDD"),
)


def seed_stakeholder_schemes(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    for code, name, prefix in SCHEMES:
        ReferenceNumberScheme.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "description": f"Phase 14 reference scheme for {name.lower()} records.",
                "module": "partners",
                "record_type": code,
                "prefix": prefix,
                "pattern": "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
                "organization_code": "SITADC",
                "sequence_length": 6,
                "start_value": 1,
                "reset_period": "NEVER",
                "is_default_for_module": code == "stakeholder",
                "is_default_for_record_type": True,
                "is_fallback": False,
                "status": "ACTIVE",
                "is_active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("references", "0002_seed_volunteer_reference_schemes")]
    operations = [
        migrations.RunPython(seed_stakeholder_schemes, migrations.RunPython.noop)
    ]
