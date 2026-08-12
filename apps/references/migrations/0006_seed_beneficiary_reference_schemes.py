"""Seed centralized Phase 17 beneficiary reference schemes."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

SCHEMES = (
    ("household", "Household", "HHL"),
    ("beneficiary_group", "Beneficiary Group", "GRP"),
    ("beneficiary_enrollment", "Beneficiary Enrollment", "ENR"),
    ("beneficiary_participation", "Beneficiary Participation", "PRT"),
    ("beneficiary_assessment", "Beneficiary Assessment", "ASS"),
    ("beneficiary_referral", "Beneficiary Referral", "RFL"),
    ("beneficiary_service", "Service Delivery", "SRV"),
    ("beneficiary_case_note", "Case Note", "CSE"),
    ("beneficiary_support_plan", "Support Plan", "SPL"),
    ("beneficiary_exit", "Beneficiary Exit", "EXT"),
    ("beneficiary_transfer", "Beneficiary Transfer", "TRF"),
    ("beneficiary_document", "Beneficiary Document", "BND"),
    ("beneficiary_consent", "Beneficiary Consent", "CNS"),
    ("beneficiary_safeguarding", "Safeguarding Record", "SFG"),
    ("beneficiary_outcome", "Beneficiary Outcome", "OUT"),
    ("beneficiary_feedback", "Beneficiary Feedback", "FDB"),
)


def seed_beneficiary_schemes(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    for code, name, prefix in SCHEMES:
        ReferenceNumberScheme.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "description": f"Phase 17 reference scheme for {name.lower()} records.",
                "module": "beneficiaries",
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
    dependencies = [("references", "0005_seed_program_reference_schemes")]
    operations = [
        migrations.RunPython(seed_beneficiary_schemes, migrations.RunPython.noop)
    ]
