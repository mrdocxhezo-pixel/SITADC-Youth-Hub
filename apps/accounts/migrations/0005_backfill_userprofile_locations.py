"""
Backfill the new geographic FK fields from the existing free-text values.

Existing ``province`` / ``district`` text values are matched (case-insensitive,
by name) against the centralized locations hierarchy and copied into the new
``*_location`` FK fields. Records whose text value does not match a known
location are left unset (historical text is preserved) rather than destroyed.
"""

from django.db import migrations


def backfill_user_profile(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")
    Province = apps.get_model("locations", "Province")
    District = apps.get_model("locations", "District")

    province_by_name = {
        p.name.strip().lower(): p for p in Province.objects.all()
    }
    district_by_name = {
        d.name.strip().lower(): d for d in District.objects.all()
    }

    # Province first.
    for profile in UserProfile.objects.exclude(province="").exclude(
        province_location__isnull=False
    ):
        key = profile.province.strip().lower()
        if key in province_by_name:
            profile.province_location = province_by_name[key]
            profile.save(update_fields=["province_location"])

    # District second.
    for profile in UserProfile.objects.exclude(district="").exclude(
        district_location__isnull=False
    ):
        key = profile.district.strip().lower()
        if key in district_by_name:
            profile.district_location = district_by_name[key]
            profile.save(update_fields=["district_location"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_userprofile_district_location_and_more"),
        ("locations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill_user_profile, noop),
    ]
