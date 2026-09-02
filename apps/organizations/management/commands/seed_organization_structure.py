"""
Idempotently seed the complete organizational catalogues: levels, classifications,
directorates, departments, program & technical management units, and standard positions.

Run with::

    python manage.py seed_organization_structure

The command is safe to run repeatedly; existing records are updated in place
and missing records are created without deleting or overwriting user data.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.leadership.seed_data import LEADERSHIP_POSITIONS
from apps.organizations.constants import PositionStatus, UnitStatus, UnitType
from apps.organizations.models import (
    OrganizationLevel,
    OrganizationUnit,
    Position,
    PositionClassification,
)
from apps.organizations.seed_data import (
    DEFAULT_CLASSIFICATIONS,
    DEFAULT_DEPARTMENTS,
    DEFAULT_DIRECTORATES,
    DEFAULT_LEVELS,
    DEFAULT_PTM_UNITS,
)


class Command(BaseCommand):
    help = "Seed organizational levels, classifications, units (directorates, departments, PTM), and positions."

    @transaction.atomic
    def handle(self, *args, **options):
        verbosity = int(options.get("verbosity", 1))

        # 1. Levels
        created_levels = 0
        levels_map = {}
        for level_seed in DEFAULT_LEVELS:
            level_obj, level_created = OrganizationLevel.objects.update_or_create(
                code=level_seed.code,
                defaults={
                    "name": level_seed.name,
                    "sort_order": level_seed.sort_order,
                    "description": level_seed.description,
                    "is_active": True,
                },
            )
            levels_map[level_seed.code] = level_obj
            if level_created:
                created_levels += 1

        # 2. Classifications
        created_classifications = 0
        classifications_map = {}
        for classification_seed in DEFAULT_CLASSIFICATIONS:
            class_obj, class_created = (
                PositionClassification.objects.update_or_create(
                    code=classification_seed.code,
                    defaults={
                        "name": classification_seed.name,
                        "sort_order": classification_seed.sort_order,
                        "description": classification_seed.description,
                        "is_active": True,
                    },
                )
            )
            classifications_map[classification_seed.code] = class_obj
            if class_created:
                created_classifications += 1

        # 3. Root Organization Unit (Head)
        gov_level = levels_map.get("governance") or OrganizationLevel.objects.first()
        root_unit, _ = OrganizationUnit.objects.update_or_create(
            identifier="ORG-HEAD",
            defaults={
                "name": "SITADC Youth Organization",
                "short_name": "SITADC",
                "level": gov_level,
                "unit_type": UnitType.GENERAL_ASSEMBLY,
                "description": "National apex organization body.",
                "status": UnitStatus.ACTIVE,
            },
        )

        units_by_identifier = {"ORG-HEAD": root_unit}

        # 4. Directorates (17 total)
        created_directorates = 0
        dir_level = levels_map.get("directorate") or gov_level
        for dir_seed in DEFAULT_DIRECTORATES:
            dir_unit, created = OrganizationUnit.objects.update_or_create(
                identifier=dir_seed.identifier,
                defaults={
                    "name": dir_seed.name,
                    "short_name": dir_seed.short_name,
                    "level": dir_level,
                    "parent": root_unit,
                    "unit_type": UnitType.DIRECTORATE,
                    "description": dir_seed.description,
                    "status": UnitStatus.ACTIVE,
                },
            )
            units_by_identifier[dir_seed.identifier] = dir_unit
            if created:
                created_directorates += 1

        # 5. Departments (10 total)
        created_departments = 0
        dept_level = levels_map.get("department") or dir_level
        for dept_seed in DEFAULT_DEPARTMENTS:
            parent_unit = (
                units_by_identifier.get(dept_seed.parent_identifier) or root_unit
            )
            dept_unit, created = OrganizationUnit.objects.update_or_create(
                identifier=dept_seed.identifier,
                defaults={
                    "name": dept_seed.name,
                    "short_name": dept_seed.short_name,
                    "level": dept_level,
                    "parent": parent_unit,
                    "unit_type": UnitType.DEPARTMENT,
                    "description": dept_seed.description,
                    "status": UnitStatus.ACTIVE,
                },
            )
            units_by_identifier[dept_seed.identifier] = dept_unit
            if created:
                created_departments += 1

        # 6. Program & Technical Management Units (11 total)
        created_ptm = 0
        ptm_level = levels_map.get("program_technical_management") or dept_level
        for ptm_seed in DEFAULT_PTM_UNITS:
            parent_unit = (
                units_by_identifier.get(ptm_seed.parent_identifier) or root_unit
            )
            ptm_unit, created = OrganizationUnit.objects.update_or_create(
                identifier=ptm_seed.identifier,
                defaults={
                    "name": ptm_seed.name,
                    "short_name": ptm_seed.short_name,
                    "level": ptm_level,
                    "parent": parent_unit,
                    "unit_type": UnitType.PROGRAM_TECHNICAL_MANAGEMENT,
                    "description": ptm_seed.description,
                    "status": UnitStatus.ACTIVE,
                },
            )
            units_by_identifier[ptm_seed.identifier] = ptm_unit
            if created:
                created_ptm += 1

        # 7. Standard Positions
        created_positions = 0
        for pos_seed in LEADERSHIP_POSITIONS:
            # Determine appropriate unit & classification
            target_unit = root_unit
            target_class = classifications_map.get("executive-leadership")

            level = pos_seed.level
            if level == "DIRECTORATE":
                target_unit = units_by_identifier.get("DIR-PROG-PROJ") or root_unit
                target_class = classifications_map.get("directorate-leadership")
            elif level == "DEPARTMENT":
                target_unit = units_by_identifier.get("DEPT-PPM") or root_unit
                target_class = classifications_map.get("department-leadership")
            elif level == "PROGRAM_TECHNICAL_MANAGEMENT":
                target_unit = units_by_identifier.get("PTM-PPC") or root_unit
                target_class = classifications_map.get("program-technical-management")
            elif level == "REGIONAL_COORDINATOR":
                target_class = classifications_map.get("regional-leadership")
            elif level == "DISTRICT_COORDINATOR":
                target_class = classifications_map.get("district-leadership")
            elif level == "COMMUNITY_COORDINATOR":
                target_class = classifications_map.get("community-leadership")
            elif level == "TEAM_LEADER":
                target_class = classifications_map.get("team-leadership")
            elif level == "VOLUNTEER_MEMBER":
                target_class = classifications_map.get("volunteer")

            pos_slug = slugify(pos_seed.title)
            # Ensure slug uniqueness
            pos_obj, created = Position.objects.update_or_create(
                slug=pos_slug,
                defaults={
                    "title": pos_seed.title,
                    "organizational_unit": target_unit,
                    "classification": target_class,
                    "responsibilities": pos_seed.description,
                    "status": PositionStatus.ACTIVE,
                },
            )
            if created:
                created_positions += 1

        if verbosity:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Organizational structure catalogues ready: {created_levels} levels, "
                    f"{created_classifications} classifications, {created_directorates} directorates, "
                    f"{created_departments} departments, {created_ptm} PTM units, "
                    f"and {created_positions} positions created/updated."
                )
            )
