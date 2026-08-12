"""Add the ``calendars`` module and seed Phase 24 reference number schemes."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations, models

SCHEMES = (
    (
        "calendar",
        "Calendar",
        "calendars",
        "calendar",
        "CAL",
        "Phase 24 reference scheme for organizational calendars.",
    ),
    (
        "event",
        "Event",
        "events",
        "event",
        "EVT",
        "Phase 24 reference scheme for calendar events.",
    ),
    (
        "meeting",
        "Meeting",
        "meetings",
        "meeting",
        "MTG",
        "Phase 24 reference scheme for meetings.",
    ),
    (
        "meeting_minutes",
        "Meeting Minutes",
        "meetings",
        "minutes",
        "MIN",
        "Phase 24 reference scheme for meeting minutes.",
    ),
    (
        "meeting_decision",
        "Meeting Decision",
        "meetings",
        "decision",
        "DEC",
        "Phase 24 reference scheme for meeting decisions.",
    ),
    (
        "meeting_action",
        "Meeting Action Item",
        "meetings",
        "action",
        "ACT",
        "Phase 24 reference scheme for meeting action items.",
    ),
)


def seed_meeting_schemes(apps, schema_editor):
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
        ("references", "0009_seed_register_scheme"),
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
                ],
                db_index=True,
                max_length=60,
                verbose_name="Module",
            ),
        ),
        migrations.RunPython(seed_meeting_schemes, migrations.RunPython.noop),
    ]
