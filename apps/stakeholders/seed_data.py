"""Declarative default taxonomies, score dimensions, and reference schemes."""

from __future__ import annotations

from decimal import Decimal

from apps.references.constants import ReferenceModules, SequenceResetPeriod

from .constants import (
    AgreementStatus,
    CommitmentStatus,
    ConfidentialityLevel,
    EngagementType,
    ReferenceDataKind,
    RiskLevel,
    StakeholderStatus,
)


def _rows(kind, names):
    return tuple(
        {
            "kind": kind,
            "code": code,
            "name": name,
            "order": order,
            "metadata": metadata,
        }
        for order, (code, name, metadata) in enumerate(names, start=1)
    )


def _choice_rows(kind, choices):
    return _rows(
        kind,
        tuple(
            (str(value).lower().replace("_", "-"), str(label), {"value": value})
            for value, label in choices
        ),
    )


DEFAULT_REFERENCE_DATA = (
    *_rows(
        ReferenceDataKind.CATEGORY,
        (
            ("government", "Government Institution", {}),
            ("development-partner", "Development Partner", {}),
            ("donor", "Donor", {}),
            ("sponsor", "Sponsor", {}),
            ("ngo", "Non-Governmental Organization", {}),
            ("cbo", "Community-Based Organization", {}),
            ("fbo", "Faith-Based Organization", {}),
            ("education", "Educational Institution", {}),
            ("private-sector", "Private Sector Organization", {}),
            ("media", "Media Organization", {}),
            ("research", "Research Institution", {}),
            ("service-provider", "Service Provider", {}),
            ("partner", "Partner", {}),
            ("implementing-partner", "Implementing Partner", {}),
            ("technical-partner", "Technical Partner", {}),
            ("strategic-partner", "Strategic Partner", {}),
            ("funding-partner", "Funding Partner", {}),
            ("corporate-partner", "Corporate Partner", {}),
            ("knowledge-partner", "Knowledge Partner", {}),
            ("media-partner", "Media Partner", {}),
            ("community-stakeholder", "Community Stakeholder", {}),
            ("beneficiary-representative", "Beneficiary Representative", {}),
            ("supplier", "Supplier", {}),
            ("vendor", "Vendor", {}),
            ("consultant", "Consultant", {}),
            ("prospect", "Prospect", {}),
            ("other", "Other", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.TYPE,
        (
            ("strategic", "Strategic Partner", {}),
            ("funding", "Funding Partner", {}),
            ("technical", "Technical Partner", {}),
            ("implementing", "Implementing Partner", {}),
            ("referral", "Referral Partner", {}),
            ("government", "Government Partner", {}),
            ("community", "Community Partner", {}),
            ("academic", "Academic Partner", {}),
            ("corporate", "Corporate Partner", {}),
            ("supplier", "Service Provider", {}),
            ("individual", "Individual", {}),
            ("organization", "Organization", {}),
            ("government-institution", "Government Institution", {}),
            ("community-institution", "Community Institution", {}),
            ("educational-institution", "Educational Institution", {}),
            ("health-institution", "Health Institution", {}),
            ("private-company", "Private Company", {}),
            ("ngo", "Non-Governmental Organization", {}),
            ("cbo", "Community-Based Organization", {}),
            ("fbo", "Faith-Based Organization", {}),
            ("development-agency", "Development Agency", {}),
            ("media-organization", "Media Organization", {}),
            ("research-institution", "Research Institution", {}),
            ("network", "Network", {}),
            ("coalition", "Coalition", {}),
            ("professional-association", "Professional Association", {}),
            ("consultant", "Consultant", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.CLASSIFICATION,
        (
            ("internal", "Internal", {}),
            ("external", "External", {}),
            ("primary", "Primary", {}),
            ("secondary", "Secondary", {}),
            ("strategic", "Strategic", {}),
            ("operational", "Operational", {}),
            ("advisory", "Advisory", {}),
            ("regulatory", "Regulatory", {}),
            ("funding", "Funding", {}),
            ("community", "Community", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.SECTOR,
        (
            ("education", "Education", {}),
            ("technology", "Technology and Digital Innovation", {}),
            ("health", "Health and Well-being", {}),
            ("entrepreneurship", "Entrepreneurship and Employment", {}),
            ("governance", "Governance and Civic Engagement", {}),
            ("environment", "Environment and Climate", {}),
            ("finance", "Finance", {}),
            ("community-development", "Community Development", {}),
            ("youth-development", "Youth Development", {}),
            ("mental-health", "Mental Health", {}),
            ("srhr", "Sexual and Reproductive Health and Rights", {}),
            ("agriculture", "Agriculture", {}),
            ("human-rights", "Human Rights", {}),
            ("research", "Research", {}),
            ("media", "Media", {}),
            ("social-protection", "Social Protection", {}),
            ("humanitarian-assistance", "Humanitarian Assistance", {}),
            ("vocational-training", "Vocational Training", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.FOCUS_AREA,
        (
            ("youth-empowerment", "Youth Empowerment", {}),
            ("digital-literacy", "Digital Literacy", {}),
            ("skills-development", "Skills Development", {}),
            ("leadership", "Youth Leadership", {}),
            ("health", "Health and Well-being", {}),
            ("innovation", "Innovation", {}),
            ("sustainability", "Sustainable Living", {}),
            ("education-literacy", "Education and Literacy", {}),
            (
                "entrepreneurship-innovation",
                "Entrepreneurship and Business Innovation",
                {},
            ),
            ("mentorship", "Youth Empowerment and Mentorship", {}),
            ("community-engagement", "Community Engagement", {}),
            ("climate-action", "Climate Action", {}),
            ("srhr", "Sexual and Reproductive Health and Rights", {}),
            ("vocational-training", "Skills Development and Vocational Training", {}),
            ("mental-health", "Mental Health and Well-being", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.SDG,
        tuple(
            (f"sdg-{number}", f"SDG {number}: {name}", {"number": number})
            for number, name in (
                (1, "No Poverty"),
                (3, "Good Health and Well-being"),
                (4, "Quality Education"),
                (5, "Gender Equality"),
                (8, "Decent Work and Economic Growth"),
                (9, "Industry, Innovation and Infrastructure"),
                (10, "Reduced Inequalities"),
                (13, "Climate Action"),
                (16, "Peace, Justice and Strong Institutions"),
                (17, "Partnerships for the Goals"),
            )
        ),
    ),
    *_rows(
        ReferenceDataKind.ENGAGEMENT_LEVEL,
        (
            ("inform", "Inform", {"rank": 1}),
            ("consult", "Consult", {"rank": 2}),
            ("involve", "Involve", {"rank": 3}),
            ("collaborate", "Collaborate", {"rank": 4}),
            ("empower", "Empower", {"rank": 5}),
            ("strategic-partnership", "Strategic Partnership", {"rank": 6}),
        ),
    ),
    *_rows(
        ReferenceDataKind.CONTRIBUTION_TYPE,
        (
            ("financial", "Financial Contribution", {}),
            ("in-kind", "In-kind Support", {}),
            ("technical", "Technical Assistance", {}),
            ("equipment", "Equipment Support", {}),
            ("training", "Training Support", {}),
            ("volunteer", "Volunteer Support", {}),
            ("advisory", "Advisory Services", {}),
            ("venue", "Venue", {}),
            ("transport", "Transport", {}),
            ("staff-time", "Staff Time", {}),
            ("mentorship", "Mentorship", {}),
            ("media-support", "Media Support", {}),
            ("data", "Data", {}),
            ("research", "Research", {}),
            ("materials", "Materials", {}),
            ("other", "Other Resources", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.AGREEMENT_TYPE,
        (
            ("mou", "Memorandum of Understanding", {}),
            ("partnership", "Partnership Agreement", {}),
            ("grant", "Grant Agreement", {}),
            ("sponsorship", "Sponsorship Agreement", {}),
            ("service", "Service Contract", {}),
            ("data-sharing", "Data Sharing Agreement", {}),
            ("letter", "Letter of Cooperation", {}),
            ("moa", "Memorandum of Agreement", {}),
            ("consultancy", "Consultancy Agreement", {}),
            ("collaboration", "Collaboration Agreement", {}),
            ("letter-intent", "Letter of Intent", {}),
            ("nda", "Non-Disclosure Agreement", {}),
            ("technical-assistance", "Technical Assistance Agreement", {}),
            ("framework", "Framework Agreement", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.RISK_CATEGORY,
        (
            ("strategic", "Strategic", {}),
            ("financial", "Financial", {}),
            ("legal", "Legal and Regulatory", {}),
            ("reputation", "Reputational", {}),
            ("safeguarding", "Safeguarding", {}),
            ("operational", "Operational", {}),
            ("data-protection", "Data Protection", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.DUE_DILIGENCE_CHECK,
        (
            ("legal-registration", "Legal Registration", {}),
            ("sanctions", "Sanctions and Watchlists", {}),
            ("financial", "Financial Capacity", {}),
            ("governance", "Governance", {}),
            ("safeguarding", "Safeguarding", {}),
            ("data-protection", "Data Protection", {}),
            ("references", "Reference Checks", {}),
            ("conflicts", "Conflict of Interest", {}),
        ),
    ),
    *_choice_rows(ReferenceDataKind.STATUS, StakeholderStatus.choices),
    *_choice_rows(
        ReferenceDataKind.CONFIDENTIALITY_LEVEL, ConfidentialityLevel.choices
    ),
    *_choice_rows(ReferenceDataKind.ENGAGEMENT_TYPE, EngagementType.choices),
    *_choice_rows(ReferenceDataKind.COMMITMENT_STATUS, CommitmentStatus.choices),
    *_choice_rows(ReferenceDataKind.AGREEMENT_STATUS, AgreementStatus.choices),
    *_choice_rows(ReferenceDataKind.RISK_LEVEL, RiskLevel.choices),
    *_rows(
        ReferenceDataKind.PRIORITY,
        (
            ("low", "Low", {}),
            ("medium", "Medium", {}),
            ("high", "High", {}),
            ("critical", "Critical", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.RELATIONSHIP_LEVEL,
        (
            ("new", "New", {}),
            ("developing", "Developing", {}),
            ("established", "Established", {}),
            ("strategic", "Strategic", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.OWNERSHIP_TYPE,
        (
            ("public", "Public", {}),
            ("private", "Private", {}),
            ("nonprofit", "Non-profit", {}),
            ("community", "Community-owned", {}),
            ("mixed", "Mixed", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.COMMUNICATION_TYPE,
        (
            ("email", "Email", {}),
            ("phone", "Phone Call", {}),
            ("letter", "Letter", {}),
            ("meeting", "Meeting", {}),
            ("video", "Video Call", {}),
            ("sms", "SMS", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.CONTACT_ROLE,
        (
            ("primary", "Primary Contact", {}),
            ("decision-maker", "Decision Maker", {}),
            ("technical", "Technical Contact", {}),
            ("finance", "Finance Contact", {}),
            ("safeguarding", "Safeguarding Contact", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.ASSESSMENT_SCALE,
        tuple(
            (str(value), f"{value} - {label}", {"score": value})
            for value, label in (
                (1, "Very Low"),
                (2, "Low"),
                (3, "Moderate"),
                (4, "High"),
                (5, "Very High"),
            )
        ),
    ),
    *_rows(
        ReferenceDataKind.PERFORMANCE_SCALE,
        tuple(
            (str(value), f"{value} - {label}", {"score": value})
            for value, label in (
                (1, "Unsatisfactory"),
                (2, "Needs Improvement"),
                (3, "Satisfactory"),
                (4, "Good"),
                (5, "Excellent"),
            )
        ),
    ),
)


DEFAULT_PERFORMANCE_DIMENSIONS = (
    ("engagement-frequency", "Engagement Frequency", Decimal("1.0000")),
    ("partnership-effectiveness", "Partnership Effectiveness", Decimal("2.0000")),
    ("commitment-fulfilment", "Commitment Fulfilment", Decimal("2.0000")),
    ("contribution-value", "Contribution Value", Decimal("1.0000")),
    ("meeting-participation", "Meeting Participation", Decimal("1.0000")),
    ("communication-responsiveness", "Communication Responsiveness", Decimal("1.0000")),
    ("joint-outcomes", "Joint Initiative Outcomes", Decimal("2.0000")),
)


DEFAULT_REFERENCE_SCHEMES = (
    ("stakeholder", "Stakeholder", "STK"),
    ("stakeholder_engagement", "Stakeholder Engagement", "SEG"),
    ("stakeholder_agreement", "Stakeholder Agreement", "SAG"),
    ("stakeholder_commitment", "Stakeholder Commitment", "SCM"),
    ("stakeholder_contribution", "Stakeholder Contribution", "SCN"),
    ("stakeholder_assessment", "Stakeholder Assessment", "SAS"),
    ("stakeholder_performance", "Stakeholder Performance", "SPF"),
    ("stakeholder_due_diligence", "Stakeholder Due Diligence", "SDD"),
)


def reference_scheme_defaults(code: str, name: str, prefix: str) -> dict:
    return {
        "name": name,
        "description": f"Phase 14 reference scheme for {name.lower()} records.",
        "module": ReferenceModules.PARTNERS,
        "record_type": code,
        "prefix": prefix,
        "pattern": "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
        "sequence_length": 6,
        "start_value": 1,
        "reset_period": SequenceResetPeriod.NEVER,
        "is_default_for_module": code == "stakeholder",
        "is_default_for_record_type": True,
        "is_fallback": False,
        "status": "ACTIVE",
        "is_active": True,
    }
