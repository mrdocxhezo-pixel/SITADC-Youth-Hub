"""
Backfill the new geographic FK fields on Beneficiary / BeneficiaryGroup from
existing text values (province_or_region / district / community / ward).

Unmatched historical text values are preserved rather than destroyed.
"""

from django.db import migrations


def backfill(apps, schema_editor):
    Beneficiary = apps.get_model("beneficiaries", "Beneficiary")
    BeneficiaryGroup = apps.get_model("beneficiaries", "BeneficiaryGroup")
    Province = apps.get_model("locations", "Province")
    District = apps.get_model("locations", "District")
    Ward = apps.get_model("locations", "Ward")

    province_by = {p.name.strip().lower(): p for p in Province.objects.all()}
    district_by = {d.name.strip().lower(): d for d in District.objects.all()}
    ward_by = {w.name.strip().lower(): w for w in Ward.objects.all()}

    for obj in Beneficiary.objects.all().iterator(chunk_size=500):
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
        # community / ward mapped to ward_location
        for text_field in ("community", "ward", "village"):
            value = getattr(obj, text_field, "")
            if value and not obj.ward_location:
                key = value.strip().lower()
                if key in ward_by:
                    obj.ward_location = ward_by[key]
                    changes.append("ward_location")
                    break
        if changes:
            obj.save(update_fields=changes)

    for group in BeneficiaryGroup.objects.all().iterator(chunk_size=500):
        changes = []
        if group.province_or_region and not group.province_location:
            key = group.province_or_region.strip().lower()
            if key in province_by:
                group.province_location = province_by[key]
                changes.append("province_location")
        if group.district and not group.district_location:
            key = group.district.strip().lower()
            if key in district_by:
                group.district_location = district_by[key]
                changes.append("district_location")
        if group.community and not group.ward_location:
            key = group.community.strip().lower()
            if key in ward_by:
                group.ward_location = ward_by[key]
                changes.append("ward_location")
        if changes:
            group.save(update_fields=changes)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("beneficiaries", "0002_beneficiary_constituency_location_and_more"),
        ("locations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
