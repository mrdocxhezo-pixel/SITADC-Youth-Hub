"""
Backfill the new geographic FK fields on membership models from existing text.

Covers MemberProfile, MembershipApplication and MembershipTransfer. Unmatched
historical text values are preserved rather than destroyed.
"""

from django.db import migrations


def backfill(apps, schema_editor):
    MemberProfile = apps.get_model("memberships", "MemberProfile")
    MembershipApplication = apps.get_model(
        "memberships", "MembershipApplication"
    )
    MembershipTransfer = apps.get_model("memberships", "MembershipTransfer")
    Province = apps.get_model("locations", "Province")
    District = apps.get_model("locations", "District")
    Ward = apps.get_model("locations", "Ward")

    province_by = {p.name.strip().lower(): p for p in Province.objects.all()}
    district_by = {d.name.strip().lower(): d for d in District.objects.all()}
    ward_by = {w.name.strip().lower(): w for w in Ward.objects.all()}

    for obj in MemberProfile.objects.all().iterator(chunk_size=500):
        changes = []
        if obj.province and not obj.province_location:
            key = obj.province.strip().lower()
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

    for obj in MembershipApplication.objects.all().iterator(chunk_size=500):
        changes = []
        if obj.province and not obj.province_location:
            key = obj.province.strip().lower()
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

    for obj in MembershipTransfer.objects.all().iterator(chunk_size=500):
        changes = []
        if obj.from_province and not obj.from_province_location:
            key = obj.from_province.strip().lower()
            if key in province_by:
                obj.from_province_location = province_by[key]
                changes.append("from_province_location")
        if obj.from_district and not obj.from_district_location:
            key = obj.from_district.strip().lower()
            if key in district_by:
                obj.from_district_location = district_by[key]
                changes.append("from_district_location")
        if obj.to_province and not obj.to_province_location:
            key = obj.to_province.strip().lower()
            if key in province_by:
                obj.to_province_location = province_by[key]
                changes.append("to_province_location")
        if obj.to_district and not obj.to_district_location:
            key = obj.to_district.strip().lower()
            if key in district_by:
                obj.to_district_location = district_by[key]
                changes.append("to_district_location")
        if changes:
            obj.save(update_fields=changes)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("memberships", "0002_memberprofile_district_location_and_more"),
        ("locations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
