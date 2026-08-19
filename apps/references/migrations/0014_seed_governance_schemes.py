"""Seed governance reference number schemes (Phase 29)."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

GOVERNANCE_SCHEMES = [
    {
        "code": "governance_policy",
        "name": "Policy",
        "record_type": "policy",
        "prefix": "POL",
    },
    {
        "code": "governance_risk",
        "name": "Risk Register",
        "record_type": "risk",
        "prefix": "RSK",
    },
    {
        "code": "governance_compliance",
        "name": "Compliance Requirement",
        "record_type": "compliance",
        "prefix": "CMP",
    },
    {
        "code": "governance_ethics",
        "name": "Ethics Case",
        "record_type": "ethics",
        "prefix": "ETH",
    },
    {
        "code": "governance_safeguarding",
        "name": "Safeguarding Case",
        "record_type": "safeguarding",
        "prefix": "SFG",
    },
    {
        "code": "governance_incident",
        "name": "Incident Report",
        "record_type": "incident",
        "prefix": "INC",
    },
    {
        "code": "governance_complaint",
        "name": "Complaint",
        "record_type": "complaint",
        "prefix": "CPL",
    },
    {
        "code": "governance_whistleblower",
        "name": "Whistleblower Report",
        "record_type": "whistleblower",
        "prefix": "WHB",
    },
    {
        "code": "governance_capa",
        "name": "Corrective & Preventive Action",
        "record_type": "capa",
        "prefix": "CAPA",
    },
    {
        "code": "governance_meeting",
        "name": "Governance Meeting",
        "record_type": "meeting",
        "prefix": "MTG",
    },
]


def seed_governance_schemes(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    for scheme in GOVERNANCE_SCHEMES:
        ReferenceNumberScheme.objects.update_or_create(
            code=scheme["code"],
            defaults={
                "name": scheme["name"],
                "description": f"Phase 29 reference scheme for {scheme['name'].lower()} records.",
                "module": "governance",
                "record_type": scheme["record_type"],
                "prefix": scheme["prefix"],
                "pattern": "{ORG}-{PREFIX}-{YEAR}-{SEQUENCE}",
                "organization_code": "SITADC",
                "sequence_length": 6,
                "start_value": 1,
                "reset_period": "ANNUALLY",
                "is_default_for_module": False,
                "is_default_for_record_type": True,
                "is_fallback": False,
                "status": "ACTIVE",
                "is_active": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("references", "0013_alter_referencenumberscheme_module"),
    ]

    operations = [
        migrations.RunPython(seed_governance_schemes, migrations.RunPython.noop),
    ]