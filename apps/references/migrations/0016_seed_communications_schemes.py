"""Seed communication reference number schemes (Phase 30)."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

COMMUNICATIONS_SCHEMES = [
    {
        "code": "communications_communication",
        "name": "Communication",
        "record_type": "communication",
        "prefix": "COM",
    },
    {
        "code": "communications_announcement",
        "name": "Announcement",
        "record_type": "announcement",
        "prefix": "ANN",
    },
    {
        "code": "communications_news",
        "name": "News Article",
        "record_type": "news",
        "prefix": "NWS",
    },
    {
        "code": "communications_newsletter",
        "name": "Newsletter",
        "record_type": "newsletter",
        "prefix": "NWL",
    },
    {
        "code": "communications_press_release",
        "name": "Press Release",
        "record_type": "press_release",
        "prefix": "PRS",
    },
    {
        "code": "communications_campaign",
        "name": "Campaign",
        "record_type": "campaign",
        "prefix": "CAM",
    },
    {
        "code": "communications_website_page",
        "name": "Website Page",
        "record_type": "website_page",
        "prefix": "WEB",
    },
    {
        "code": "communications_event_communication",
        "name": "Event Communication",
        "record_type": "event_communication",
        "prefix": "EVC",
    },
    {
        "code": "communications_publication",
        "name": "Publication",
        "record_type": "publication",
        "prefix": "PUB",
    },
    {
        "code": "communications_media",
        "name": "Media Asset",
        "record_type": "media",
        "prefix": "MED",
    },
    {
        "code": "communications_brand",
        "name": "Brand Asset",
        "record_type": "brand",
        "prefix": "BRD",
    },
]


def seed_communications_schemes(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    for scheme in COMMUNICATIONS_SCHEMES:
        ReferenceNumberScheme.objects.update_or_create(
            code=scheme["code"],
            defaults={
                "name": scheme["name"],
                "description": f"Phase 30 reference scheme for {scheme['name'].lower()} records.",
                "module": "communications",
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
        ("references", "0015_alter_referencenumberscheme_module"),
    ]

    operations = [
        migrations.RunPython(seed_communications_schemes, migrations.RunPython.noop),
    ]