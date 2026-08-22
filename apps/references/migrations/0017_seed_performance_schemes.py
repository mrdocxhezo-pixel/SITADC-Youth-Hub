"""Seed performance reference number schemes (Phase 34)."""

# ruff: noqa: RUF012 - Django migration attributes are declarative.

from django.db import migrations

PERFORMANCE_SCHEMES = [
    {
        "code": "performance_metric",
        "name": "Performance Metric",
        "record_type": "metric",
        "prefix": "PMET",
    },
    {
        "code": "performance_kpi",
        "name": "Performance KPI",
        "record_type": "kpi",
        "prefix": "PKPI",
    },
    {
        "code": "performance_benchmark",
        "name": "Performance Benchmark",
        "record_type": "benchmark",
        "prefix": "PBEN",
    },
    {
        "code": "performance_optimization",
        "name": "Performance Optimization",
        "record_type": "optimization",
        "prefix": "POPT",
    },
    {
        "code": "performance_cache",
        "name": "Cache Configuration",
        "record_type": "cache",
        "prefix": "PCH",
    },
    {
        "code": "performance_queue",
        "name": "Queue Monitoring",
        "record_type": "queue",
        "prefix": "PQUE",
    },
    {
        "code": "performance_database",
        "name": "Database Monitoring",
        "record_type": "database",
        "prefix": "PDB",
    },
    {
        "code": "performance_alert",
        "name": "Performance Alert",
        "record_type": "alert",
        "prefix": "PALT",
    },
    {
        "code": "performance_report",
        "name": "Performance Report",
        "record_type": "report",
        "prefix": "PRPT",
    },
]


def seed_performance_schemes(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    for scheme in PERFORMANCE_SCHEMES:
        ReferenceNumberScheme.objects.update_or_create(
            code=scheme["code"],
            defaults={
                "name": scheme["name"],
                "description": f"Phase 34 reference scheme for {scheme['name'].lower()} records.",
                "module": "performance",
                "record_type": scheme["record_type"],
                "prefix": scheme["prefix"],
                "pattern": "{PREFIX}-{YEAR}-{SEQUENCE:06d}",
                "organization_code": "SITADC",
                "sequence_length": 6,
                "is_active": True,
            },
        )


def unseed_performance_schemes(apps, schema_editor):
    ReferenceNumberScheme = apps.get_model("references", "ReferenceNumberScheme")
    ReferenceNumberScheme.objects.filter(code__in=[s["code"] for s in PERFORMANCE_SCHEMES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("references", "0016_seed_communications_schemes"),
    ]

    operations = [
        migrations.RunPython(seed_performance_schemes, unseed_performance_schemes),
    ]