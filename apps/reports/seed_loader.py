"""Idempotent loader for report builder default data, settings, and templates.

Seeds:
  - 16 report categories (A through P)
  - 143 report templates with sections, field groups, and dynamic fields
  - ReportTemplateSettings singleton
"""

from __future__ import annotations

from typing import Any

from django.db import transaction

from .constants import FieldType, ReportingFrequency, ReportTemplateStatus
from .models import (
    DynamicField,
    FieldGroup,
    FieldOption,
    ReportCategory,
    ReportTemplate,
    ReportTemplateSettings,
    ReportTemplateVersion,
    TemplateSection,
)
from .seed_data import DEFAULT_REPORT_CATEGORIES


def _combine_all_templates() -> list[dict]:
    """Import and merge all category template lists."""
    from .seed_data_b import CATEGORY_B_TEMPLATES
    from .seed_data_c import CATEGORY_C_TEMPLATES
    from .seed_data_d import CATEGORY_D_TEMPLATES
    from .seed_data_e import CATEGORY_E_TEMPLATES
    from .seed_data_f import CATEGORY_F_TEMPLATES
    from .seed_data_g import CATEGORY_G_TEMPLATES
    from .seed_data_h import CATEGORY_H_TEMPLATES
    from .seed_data_i import CATEGORY_I_TEMPLATES
    from .seed_data_j import CATEGORY_J_TEMPLATES
    from .seed_data_k import CATEGORY_K_TEMPLATES
    from .seed_data_l import CATEGORY_L_TEMPLATES
    from .seed_data_m import CATEGORY_M_TEMPLATES
    from .seed_data_n import CATEGORY_N_TEMPLATES
    from .seed_data_o import CATEGORY_O_TEMPLATES
    from .seed_data_p import CATEGORY_P_TEMPLATES
    from .seed_template_data import REPORT_TEMPLATES

    all_templates: list[dict] = []
    all_templates.extend(REPORT_TEMPLATES)  # Category A
    all_templates.extend(CATEGORY_B_TEMPLATES)
    all_templates.extend(CATEGORY_C_TEMPLATES)
    all_templates.extend(CATEGORY_D_TEMPLATES)
    all_templates.extend(CATEGORY_E_TEMPLATES)
    all_templates.extend(CATEGORY_F_TEMPLATES)
    all_templates.extend(CATEGORY_G_TEMPLATES)
    all_templates.extend(CATEGORY_H_TEMPLATES)
    all_templates.extend(CATEGORY_I_TEMPLATES)
    all_templates.extend(CATEGORY_J_TEMPLATES)
    all_templates.extend(CATEGORY_K_TEMPLATES)
    all_templates.extend(CATEGORY_L_TEMPLATES)
    all_templates.extend(CATEGORY_M_TEMPLATES)
    all_templates.extend(CATEGORY_N_TEMPLATES)
    all_templates.extend(CATEGORY_O_TEMPLATES)
    all_templates.extend(CATEGORY_P_TEMPLATES)
    return all_templates


def _resolve_category(code: str) -> ReportCategory:
    """Map a template code prefix (e.g. 'A1' -> 'A') to the ReportCategory."""
    prefix = "".join(c for c in code if c.isalpha()).upper()
    return ReportCategory.objects.get(code=prefix)


def _field_type(field_type_str: str) -> str:
    """Ensure the field type string is a valid FieldType choice."""
    valid = {choice[0] for choice in FieldType.choices}
    if field_type_str in valid:
        return field_type_str
    return FieldType.TEXT


@transaction.atomic
def _seed_template_schema(
    template: ReportTemplate, sections_data: list[dict]
) -> dict[str, int]:
    """Create sections, field groups, dynamic fields and options for a template."""
    stats = {"sections": 0, "groups": 0, "fields": 0, "options": 0}
    for s_idx, section_def in enumerate(sections_data):
        section, _ = TemplateSection.objects.update_or_create(
            template=template,
            code=section_def["code"],
            defaults={
                "name": section_def["name"],
                "sort_order": s_idx,
                "is_repeatable": section_def.get("is_repeatable", False),
            },
        )
        stats["sections"] += 1

        for g_idx, group_def in enumerate(section_def.get("groups", [])):
            group, _ = FieldGroup.objects.update_or_create(
                section=section,
                code=group_def["code"],
                defaults={
                    "name": group_def["name"],
                    "sort_order": g_idx,
                },
            )
            stats["groups"] += 1

            for f_idx, field_def in enumerate(group_def.get("fields", [])):
                ft = _field_type(field_def.get("field_type", "TEXT"))
                field, _ = DynamicField.objects.update_or_create(
                    group=group,
                    code=field_def["code"],
                    defaults={
                        "label": field_def["label"],
                        "field_type": ft,
                        "required": field_def.get("required", False),
                        "is_calculated": field_def.get("is_calculated", False),
                        "formula": field_def.get("formula", ""),
                        "is_repeatable": field_def.get("is_repeatable", False),
                        "sort_order": f_idx,
                    },
                )
                stats["fields"] += 1

                # Create dropdown options
                options = field_def.get("options", [])
                if options and ft in ("DROPDOWN", "MULTI_SELECT", "RADIO"):
                    # Remove stale options
                    existing_values = set(
                        field.options.values_list("value", flat=True)
                    )
                    new_values = {opt.lower().replace(" ", "_") for opt in options}
                    for opt_val in existing_values - new_values:
                        field.options.filter(value=opt_val).delete()

                    for o_idx, opt_label in enumerate(options):
                        opt_value = opt_label.lower().replace(" ", "_")
                        FieldOption.objects.update_or_create(
                            field=field,
                            value=opt_value,
                            defaults={
                                "label": opt_label,
                                "sort_order": o_idx,
                            },
                        )
                        stats["options"] += 1

    return stats


@transaction.atomic
def seed_report_builder_defaults() -> dict[str, int]:
    """Install default categories, settings, and all report templates."""
    stats = {
        "categories": 0,
        "settings": 0,
        "templates": 0,
        "sections": 0,
        "groups": 0,
        "fields": 0,
        "options": 0,
    }

    # 1. Seed categories
    for row in DEFAULT_REPORT_CATEGORIES:
        _, created = ReportCategory.objects.update_or_create(
            code=row["code"],
            defaults={
                "name": row["name"],
                "description": row["description"],
                "color": row["color"],
                "icon": row["icon"],
                "sort_order": row["sort_order"],
                "is_active": True,
            },
        )
        stats["categories"] += int(created)

    # 2. Seed settings singleton
    _, created = ReportTemplateSettings.objects.get_or_create(
        key="default",
        defaults={
            "is_active": True,
            "auto_save_interval_seconds": 60,
            "retention_default_days": 365,
        },
    )
    stats["settings"] += int(created)

    # 3. Seed templates and their schemas
    all_templates = _combine_all_templates()
    for tpl_def in all_templates:
        category = _resolve_category(tpl_def["code"])
        freq = tpl_def.get("reporting_frequency", "ONE_OFF")
        if freq not in dict(ReportingFrequency.choices):
            freq = "ONE_OFF"
        confidentiality = tpl_def.get("confidentiality", "INTERNAL")

        template, created = ReportTemplate.objects.update_or_create(
            code=tpl_def["code"],
            defaults={
                "reference_number": f"TPL-{tpl_def['code']}",
                "title": tpl_def["title"],
                "category": category,
                "description": tpl_def.get("description", ""),
                "reporting_frequency": freq,
                "confidentiality": confidentiality,
                "status": ReportTemplateStatus.PUBLISHED,
                "notes": (
                    "RESTRICTED ACCESS - Authorized personnel only"
                    if tpl_def.get("access_restricted")
                    else ""
                ),
            },
        )
        stats["templates"] += int(created)

        # Create version snapshot
        version, _ = ReportTemplateVersion.objects.update_or_create(
            template=template,
            version_number="1.0",
            defaults={
                "major": 1,
                "minor": 0,
                "is_current": True,
                "status": "PUBLISHED",
                "schema_snapshot": {
                    "sections": [
                        {"name": s["name"], "code": s["code"]}
                        for s in tpl_def.get("sections", [])
                    ],
                },
            },
        )
        template.current_version = version
        template.save(update_fields=["current_version"])

        # Seed schema (sections -> groups -> fields -> options)
        schema_stats = _seed_template_schema(
            template, tpl_def.get("sections", [])
        )
        stats["sections"] += schema_stats["sections"]
        stats["groups"] += schema_stats["groups"]
        stats["fields"] += schema_stats["fields"]
        stats["options"] += schema_stats["options"]

    return stats
