"""
Backfill the new geographic FK fields on Stakeholder from existing text.

Matches province_or_region / district / community against the centralized
locations hierarchy. Unmatched historical text is preserved.
"""

from django.db import migrations


def backfill(apps, schema_editor):
    Stakeholder = apps.get_model("stakeholders", "Stakeholder")
    Province = apps.get_model("locations", "Province")
    District = apps.get_model("locations", "District")
    Ward = apps.get_model("locations", "Ward")

    province_by = {p.name.strip().lower(): p for p in Province.objects.all()}
    district_by = {d.name.strip().lower(): d for d in District.objects.all()}
    ward_by = {w.name.strip().lower(): w for w in Ward.objects.all()}

    for obj in Stakeholder.objects.all().iterator(chunk_size=500):
        changes = []
        if obj.province_or_region and not obj.province_location:
            key = obj.province_or_region.strip().lower()
            if key in province_by:
                obj.province_location = province_by[key]
                changes.append("province_location")
        if obj.district and not obj.district_location:
            key = obj.district.strip().lower()
            if key in district_by:
                obj.district_location = district_by[key]
                changes.append("district_location")
        if obj.community and not obj.ward_location:
            key = obj.community.strip().lower()
            if key in ward_by:
                obj.ward_location = ward_by[key]
                changes.append("ward_location")
        if changes:
            obj.save(update_fields=changes)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("stakeholders", "0002_stakeholder_district_location_and_more"),
        ("locations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
