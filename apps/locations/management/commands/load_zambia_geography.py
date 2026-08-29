"""
Idempotently load the Zambia geographic hierarchy from ``zambia_geography.json``.

Run with::

    python manage.py load_zambia_geography

The command is safe to run repeatedly:
  * records are matched by stable admin ``code`` identifiers;
  * existing records are updated in place (name, active status);
  * missing records are created;
  * records present in the database but absent from the seed file are
    soft-deactivated (``is_active=False``) rather than deleted, preserving
    references from historical records.

Optional flags::

    --schema-only   Only create/update the Country + Provinces.
    --no-deactivate Do not deactivate geographic records absent from the seed.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.locations.models import (
    Constituency,
    Country,
    District,
    Province,
    Ward,
)

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "zambia_geography.json"


class Command(BaseCommand):
    help = "Load or update the Zambia geographic hierarchy from seed data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--schema-only",
            action="store_true",
            help="Only load countries and provinces (skip districts/constituencies/wards).",
        )
        parser.add_argument(
            "--no-deactivate",
            action="store_true",
            help="Do not deactivate seed-absent records.",
        )

    def _save(self, obj):
        obj.save()

    @transaction.atomic
    def handle(self, *args, **options):
        schema_only = options["schema_only"]
        deactivate = not options["no_deactivate"]

        with open(DATA_FILE, encoding="utf-8") as fh:
            seed = json.load(fh)

        verbosity = int(options.get("verbosity", 1))

        country, country_created = Country.objects.update_or_create(
            code="ZM",
            defaults={"name": seed.get("country", "Zambia"), "is_active": True},
        )
        created = {"provinces": 0, "districts": 0, "constituencies": 0, "wards": 0}
        updated = {"provinces": 0, "districts": 0, "constituencies": 0, "wards": 0}

        for prov_seed in seed["provinces"]:
            province, created_p = Province.objects.update_or_create(
                country=country,
                code=prov_seed["code"],
                defaults={"name": prov_seed["name"], "is_active": True},
            )
            if created_p:
                created["provinces"] += 1
            else:
                updated["provinces"] += 1

            if schema_only:
                continue

            for dist_seed in prov_seed.get("districts", []):
                district, created_d = District.objects.update_or_create(
                    province=province,
                    code=dist_seed["code"],
                    defaults={"name": dist_seed["name"], "is_active": True},
                )
                if created_d:
                    created["districts"] += 1
                else:
                    updated["districts"] += 1

                for con_seed in dist_seed.get("constituencies", []):
                    constituency, created_c = Constituency.objects.update_or_create(
                        district=district,
                        code=con_seed["code"],
                        defaults={"name": con_seed["name"], "is_active": True},
                    )
                    if created_c:
                        created["constituencies"] += 1
                    else:
                        updated["constituencies"] += 1

                    for ward_seed in con_seed.get("wards", []):
                        ward, created_w = Ward.objects.update_or_create(
                            constituency=constituency,
                            code=ward_seed["code"],
                            defaults={"name": ward_seed["name"], "is_active": True},
                        )
                        if created_w:
                            created["wards"] += 1
                        else:
                            updated["wards"] += 1

        if deactivate:
            deactivated = self._deactivate_absent(seed, schema_only=schema_only)
        else:
            deactivated = 0

        if verbosity:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Loaded {country.name}: "
                    f"{created['provinces'] + updated['provinces']} provinces, "
                    f"{created['districts'] + updated['districts']} districts, "
                    f"{created['constituencies'] + updated['constituencies']} constituencies, "
                    f"{created['wards'] + updated['wards']} wards."
                )
            )
            self.stdout.write(
                f"Created: {created}  |  Updated: {updated}  |  Deactivated: {deactivated}"
            )

    def _deactivate_absent(self, seed, schema_only=False):
        """Soft-deactivate records that exist in the DB but not in the seed."""
        deactivated = 0

        seed_prov_codes = {p["code"] for p in seed["provinces"]}
        for province in Province.objects.filter(is_active=True):
            if province.code not in seed_prov_codes:
                province.is_active = False
                province.save(update_fields=["is_active"])
                deactivated += 1
            elif schema_only:
                continue
            else:
                seed_dist = next(
                    (p for p in seed["provinces"] if p["code"] == province.code),
                    None,
                )
                if seed_dist is None:
                    continue
                dist_codes = {d["code"] for d in seed_dist.get("districts", [])}
                for district in province.districts.filter(is_active=True):
                    if district.code not in dist_codes:
                        district.is_active = False
                        district.save(update_fields=["is_active"])
                        deactivated += 1
                        continue
                    seed_con = next(
                        (d for d in seed_dist["districts"] if d["code"] == district.code),
                        None,
                    )
                    if not seed_con:
                        continue
                    con_codes = {c["code"] for c in seed_con.get("constituencies", [])}
                    for constituency in district.constituencies.filter(is_active=True):
                        if constituency.code not in con_codes:
                            constituency.is_active = False
                            constituency.save(update_fields=["is_active"])
                            deactivated += 1
                            continue
                        seed_ward = next(
                            (
                                c
                                for c in seed_con["constituencies"]
                                if c["code"] == constituency.code
                            ),
                            None,
                        )
                        if not seed_ward:
                            continue
                        ward_codes = {w["code"] for w in seed_ward.get("wards", [])}
                        for ward in constituency.wards.filter(is_active=True):
                            if ward.code not in ward_codes:
                                ward.is_active = False
                                ward.save(update_fields=["is_active"])
                                deactivated += 1
        return deactivated
