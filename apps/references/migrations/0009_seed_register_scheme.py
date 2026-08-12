"""Add the ``registers`` module choice and seed the register entry scheme."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations, models


def seed_register_entry_scheme(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    ReferenceNumberScheme.objects.update_or_create(
        code="register_entry",
        defaults={
            "name": "Register Entry",
            "description": "Phase 23 reference scheme for organizational register entries.",
            "module": "registers",
            "record_type": "entry",
            "prefix": "REG",
            "pattern": "{ORG}/REG/{PREFIX}/{YEAR}/{SEQUENCE}",
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
        ("references", "0008_alter_referencenumberscheme_module"),
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
                ],
                db_index=True,
                max_length=60,
                verbose_name="Module",
            ),
        ),
        migrations.RunPython(
            seed_register_entry_scheme, migrations.RunPython.noop
        ),
    ]
