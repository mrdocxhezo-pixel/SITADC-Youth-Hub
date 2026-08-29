"""
Backfill the new geographic FK fields on VolunteerProfile from existing text.

Existing ``region`` / ``district`` / ``community`` text values are matched
(case-insensitive, by name) against the centralized locations hierarchy and
copied into the new ``*_location`` FK fields. Unmatched historical values are
preserved as text and left unset on the FK fields.
"""

from django.db import migrations

LEVEL_PAIRS = [
    # (text field, location field, model, lookup)
    ("region", "province_location"),
    ("district", "district_location"),
    ("community", "constituency_location"),
    ("community", "ward_location"),
]


def backfill(apps, schema_editor):
    VolunteerProfile = apps.get_model("volunteers", "VolunteerProfile")
    Province = apps.get_model("locations", "Province")
    District = apps.get_model("locations", "District")
    Constituency = apps.get_model("locations", "Constituency")
    Ward = apps.get_model("locations", "Ward")

    province_by = {p.name.strip().lower(): p for p in Province.objects.all()}
    district_by = {d.name.strip().lower(): d for d in District.objects.all()}
    constituency_by = {
        c.name.strip().lower(): c for c in Constituency.objects.all()
    }
    ward_by = {w.name.strip().lower(): w for w in Ward.objects.all()}

    for profile in VolunteerProfile.objects.all().iterator(chunk_size=500):
        changes = []
        if profile.region and not profile.province_location:
            key = profile.region.strip().lower()
            if key in province_by:
                profile.province_location = province_by[key]
                changes.append("province_location")
        if profile.district and not profile.district_location:
            key = profile.district.strip().lower()
            if key in district_by:
                profile.district_location = district_by[key]
                changes.append("district_location")
        if profile.community:
            if not profile.constituency_location:
                key = profile.community.strip().lower()
                if key in constituency_by:
                    profile.constituency_location = constituency_by[key]
                    changes.append("constituency_location")
            if not profile.ward_location:
                key = profile.community.strip().lower()
                if key in ward_by:
                    profile.ward_location = ward_by[key]
                    changes.append("ward_location")
        if changes:
            profile.save(update_fields=changes)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("volunteers", "0005_volunteerprofile_constituency_location_and_more"),
        ("locations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
