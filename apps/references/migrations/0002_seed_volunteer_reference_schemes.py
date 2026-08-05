"""Seed reference schemes required by Volunteer Management."""

from django.db import migrations


def seed_volunteer_reference_schemes(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    schemes = (
        ("volunteer", "Volunteer", "volunteer", "VOL", True),
        (
            "volunteer_application",
            "Volunteer Application",
            "application",
            "VAP",
            False,
        ),
        (
            "volunteer_recruitment",
            "Volunteer Recruitment Campaign",
            "recruitment",
            "VRC",
            False,
        ),
    )
    for code, name, record_type, prefix, module_default in schemes:
        ReferenceNumberScheme.objects.update_or_create(
            module="volunteers",
            record_type=record_type,
            prefix=prefix,
            defaults={
                "code": code,
                "name": name,
                "description": f"Centralized references for {name.lower()} records.",
                "organization_code": "SITADC",
                "pattern": "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
                "sequence_length": 6,
                "start_value": 1,
                "reset_period": "NEVER",
                "status": "ACTIVE",
                "is_default_for_module": module_default,
                "is_default_for_record_type": True,
                "is_fallback": False,
                "is_active": True,
            },
        )


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("references", "0001_initial")]

    operations = [
        migrations.RunPython(
            seed_volunteer_reference_schemes,
            migrations.RunPython.noop,
        )
    ]
