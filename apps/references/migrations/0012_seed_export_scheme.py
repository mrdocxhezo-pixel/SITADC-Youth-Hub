"""Add the ``exports`` module choice and seed the export request scheme."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations, models


def seed_export_scheme(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    ReferenceNumberScheme.objects.update_or_create(
        code="export",
        defaults={
            "name": "Export Request",
            "description": "Phase 27 reference scheme for export requests.",
            "module": "exports",
            "record_type": "request",
            "prefix": "EXP",
            "pattern": "{ORG}-{PREFIX}-{YEAR}-{SEQUENCE}",
            "organization_code": "SITADC",
            "sequence_length": 6,
            "start_value": 1,
            "reset_period": "ANNUALLY",
            "is_default_for_module": True,
            "is_default_for_record_type": True,
            "is_fallback": False,
            "status": "ACTIVE",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("references", "0011_seed_notification_reference_schemes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="referencenumberscheme",
            name="module",
            field=models.CharField(
                choices=[
                    ("users", "Users"),
                    ("memberships", "Memberships"),
                    ("volunteers", "Volunteers"),
                    ("leaders", "Leaders"),
                    ("reports", "Reports"),
                    ("documents", "Documents"),
                    ("programs", "Programs"),
                    ("projects", "Projects"),
                    ("events", "Events"),
                    ("assets", "Assets"),
                    ("finance", "Finance"),
                    ("meetings", "Meetings"),
                    ("grants", "Grants"),
                    ("partners", "Partners"),
                    ("donors", "Donors"),
                    ("beneficiaries", "Beneficiaries"),
                    ("meal", "MEAL"),
                    ("registers", "Registers"),
                    ("calendars", "Calendars"),
                    ("notifications", "Notifications"),
                    ("announcements", "Announcements"),
                    ("exports", "Exports"),
                ],
                db_index=True,
                max_length=60,
                verbose_name="Module",
            ),
        ),
        migrations.RunPython(seed_export_scheme, migrations.RunPython.noop),
    ]
