"""Seed reference data for the Document Management module."""

from __future__ import annotations

from django.db import transaction

from apps.documents.models import (
    DocumentCategory,
    DocumentSettings,
    DocumentType,
    RetentionCategory,
)


@transaction.atomic
def seed_document_categories():
    """Create default document categories."""
    categories = [
        (
            "GOV",
            "Governance",
            "Governance documents including constitution, bylaws, and board documents",
            1,
        ),
        (
            "LEAD",
            "Leadership",
            "Leadership documents, appointment letters, and performance reviews",
            2,
        ),
        ("MEM", "Membership", "Membership applications, certificates, and records", 3),
        (
            "VOL",
            "Volunteers",
            "Volunteer applications, agreements, and training records",
            4,
        ),
        ("PROG", "Programs", "Program plans, reports, and implementation documents", 5),
        (
            "PROJ",
            "Projects",
            "Project proposals, plans, budgets, and closure documents",
            6,
        ),
        (
            "BEN",
            "Beneficiaries",
            "Beneficiary registration, consent, and outcome documents",
            7,
        ),
        (
            "MEAL",
            "MEAL",
            "Monitoring, evaluation, accountability, and learning documents",
            8,
        ),
        (
            "FIN",
            "Finance",
            "Financial statements, budgets, receipts, and audit reports",
            9,
        ),
        (
            "PROC",
            "Procurement",
            "Purchase requests, orders, contracts, and delivery notes",
            10,
        ),
        (
            "PART",
            "Partnerships",
            "MoUs, partnership agreements, and stakeholder correspondence",
            11,
        ),
        (
            "HR",
            "Human Resources",
            "Employment contracts, appointment letters, and HR records",
            12,
        ),
        (
            "TRAIN",
            "Training",
            "Training materials, certificates, and attendance records",
            13,
        ),
        (
            "COMM",
            "Communications",
            "Newsletters, press releases, and branding materials",
            14,
        ),
        ("LEGAL", "Legal", "Legal documents, contracts, and compliance records", 15),
        ("POL", "Policies", "Organizational policies and procedures", 16),
        ("RPT", "Reports", "Organizational reports and submissions", 17),
        ("EVID", "Evidence", "Evidence attachments and supporting documents", 18),
        ("MEDIA", "Media", "Images, videos, and audio recordings", 19),
        ("TPL", "Templates", "Document templates and forms", 20),
        (
            "ARCH",
            "Archived Records",
            "Historical and archived organizational records",
            21,
        ),
    ]

    created_count = 0
    for code, name, description, order in categories:
        _, created = DocumentCategory.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "description": description,
                "sort_order": order,
                "is_active": True,
            },
        )
        if created:
            created_count += 1
    return created_count


@transaction.atomic
def seed_document_types():
    """Create default document types."""
    types = [
        ("POL", "Policy", "POL", True, True),
        ("PROC", "Procedure", "POL", True, True),
        ("GUIDE", "Guideline", "POL", False, True),
        ("MANUAL", "Manual", "POL", True, True),
        ("STRAT", "Strategy", "GOV", True, True),
        ("PLAN", "Plan", "PROG", True, True),
        ("RPT", "Report", "RPT", True, True),
        ("REG", "Register", "GOV", False, False),
        ("MIN", "Meeting Minutes", "GOV", False, True),
        ("AGENDA", "Agenda", "GOV", False, False),
        ("MOU", "Memorandum of Understanding", "PART", True, True),
        ("AGR", "Agreement", "PART", True, True),
        ("CONTR", "Contract", "LEGAL", True, True),
        ("PROP", "Proposal", "PROJ", True, True),
        ("GRANT", "Grant Document", "FIN", True, True),
        ("BUDGET", "Budget", "FIN", True, True),
        ("FIN_REC", "Financial Record", "FIN", False, True),
        ("RECEIPT", "Receipt", "FIN", False, False),
        ("ATT", "Attendance Sheet", "TRAIN", False, False),
        ("BEN_LIST", "Beneficiary List", "BEN", False, True),
        ("MON_TOOL", "Monitoring Tool", "MEAL", True, True),
        ("EVAL", "Evaluation Report", "MEAL", True, True),
        ("RESEARCH", "Research Document", "MEAL", True, True),
        ("TRAIN_MAT", "Training Material", "TRAIN", False, True),
        ("CERT", "Certificate", "HR", False, False),
        ("APPT", "Appointment Letter", "HR", True, False),
        ("MEM_DOC", "Membership Document", "MEM", False, True),
        ("VOL_DOC", "Volunteer Document", "VOL", False, True),
        ("ID_DOC", "Identity Document", "HR", False, False),
        ("SAFEGUARD", "Safeguarding Record", "LEGAL", True, True),
        ("INCIDENT", "Incident Record", "LEGAL", True, True),
        ("PHOTO", "Photograph", "MEDIA", False, False),
        ("VIDEO", "Video", "MEDIA", False, False),
        ("AUDIO", "Audio Recording", "MEDIA", False, False),
        ("PRES", "Presentation", "COMM", False, True),
        ("SPREAD", "Spreadsheet", "FIN", False, True),
        ("FORM", "Form", "TPL", False, False),
        ("LETTER", "Letter", "COMM", False, True),
        ("EVID_ATT", "Evidence Attachment", "EVID", False, True),
    ]

    created_count = 0
    for code, name, category_code, requires_approval, requires_versioning in types:
        category = DocumentCategory.objects.filter(code=category_code).first()
        _, created = DocumentType.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "category": category,
                "requires_approval": requires_approval,
                "requires_versioning": requires_versioning,
                "is_active": True,
            },
        )
        if created:
            created_count += 1
    return created_count


@transaction.atomic
def seed_retention_categories():
    """Create default retention categories."""
    categories = [
        (
            "PERM",
            "Permanent",
            "Permanent retention - never disposed",
            None,
            "CREATION",
            "NONE",
        ),
        (
            "7YR",
            "Seven Years",
            "Retain for 7 years from trigger date",
            2555,
            "APPROVAL",
            "DELETE",
        ),
        (
            "5YR",
            "Five Years",
            "Retain for 5 years from trigger date",
            1825,
            "APPROVAL",
            "DELETE",
        ),
        (
            "3YR",
            "Three Years",
            "Retain for 3 years from trigger date",
            1095,
            "CREATION",
            "DELETE",
        ),
        (
            "PROJ",
            "Project Life + 5 Years",
            "Retain for 5 years after project closure",
            1825,
            "PROJECT_CLOSURE",
            "DELETE",
        ),
        (
            "AGREEMENT",
            "Agreement Life + 7 Years",
            "Retain for 7 years after agreement termination",
            2555,
            "AGREEMENT_TERMINATION",
            "DELETE",
        ),
        (
            "FIN",
            "Financial Records",
            "Financial records per regulatory requirements",
            2555,
            "APPROVAL",
            "ARCHIVE",
        ),
        (
            "HR",
            "Personnel Records",
            "Human resource records per employment law",
            2555,
            "MEMBERSHIP_EXIT",
            "ARCHIVE",
        ),
        (
            "TEMP",
            "Temporary Working Documents",
            "Temporary documents with short retention",
            365,
            "LAST_ACTIVITY",
            "DELETE",
        ),
        (
            "SAFEGUARD",
            "Safeguarding Permanent",
            "Safeguarding records retained permanently",
            None,
            "CREATION",
            "NONE",
        ),
    ]

    created_count = 0
    for code, name, description, period_days, trigger, action in categories:
        _, created = RetentionCategory.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "description": description,
                "retention_period_days": period_days,
                "retention_trigger": trigger,
                "disposal_action": action,
                "is_active": True,
            },
        )
        if created:
            created_count += 1
    return created_count


@transaction.atomic
def seed_document_settings():
    """Create default document settings (singleton)."""
    if not DocumentSettings.objects.exists():
        DocumentSettings.objects.create(
            max_upload_size=20 * 1024 * 1024,  # 20 MB
            enable_checkout=True,
            enable_versioning=True,
            auto_increment_version=True,
            require_change_summary=False,
            default_confidentiality="INTERNAL",
            enable_external_sharing=False,
            enable_qr_codes=False,
            enable_barcodes=False,
            storage_path_prefix="documents",
        )
        return True
    return False


def seed_all():
    """Run all seed functions."""
    results = {
        "categories": seed_document_categories(),
        "types": seed_document_types(),
        "retention": seed_retention_categories(),
        "settings": seed_document_settings(),
    }
    return results
