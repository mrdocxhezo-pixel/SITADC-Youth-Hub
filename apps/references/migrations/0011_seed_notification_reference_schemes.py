"""Add the ``notifications``/``announcements`` modules and seed Phase 25 schemes."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations, models

SCHEMES = (
    (
        "notification",
        "Notification",
        "notifications",
        "notification",
        "NTF",
        "Phase 25 reference scheme for notifications.",
    ),
    (
        "announcement",
        "Announcement",
        "announcements",
        "announcement",
        "ANN",
        "Phase 25 reference scheme for announcements.",
    ),
)


def seed_notification_schemes(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    for code, name, module, record_type, prefix, description in SCHEMES:
        ReferenceNumberScheme.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "description": description,
                "module": module,
                "record_type": record_type,
                "prefix": prefix,
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
        ("references", "0010_seed_meeting_reference_schemes"),
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
                ],
                db_index=True,
                max_length=60,
                verbose_name="Module",
            ),
        ),
        migrations.RunPython(seed_notification_schemes, migrations.RunPython.noop),
    ]
