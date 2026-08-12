"""Declarative default taxonomies and reference schemes for program management."""

from __future__ import annotations

from apps.references.constants import ReferenceModules

from .constants import ReferenceDataKind


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


DEFAULT_REFERENCE_DATA = (
    *_rows(
        ReferenceDataKind.CATEGORY,
        (
            ("education-digital", "Education, Digital Literacy & Innovation", {}),
            (
                "entrepreneurship",
                "Entrepreneurship, Employability & Skills Development",
                {},
            ),
            (
                "leadership-civic",
                "Leadership, Civic Engagement & Community Development",
                {},
            ),
            ("health-wellbeing", "Health, Well-being & Youth Empowerment", {}),
            ("climate-action", "Climate Action & Environmental Sustainability", {}),
            ("research-innovation", "Research & Innovation", {}),
            ("advocacy-policy", "Advocacy & Policy Engagement", {}),
            ("org-capacity", "Organizational Capacity Development", {}),
            ("partnerships", "Strategic Partnerships & Resource Mobilization", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.PROJECT_CATEGORY,
        (
            ("community-development", "Community Development", {}),
            ("education", "Education", {}),
            ("digital-skills", "Digital Skills", {}),
            ("youth-empowerment", "Youth Empowerment", {}),
            ("entrepreneurship", "Entrepreneurship", {}),
            ("health", "Health", {}),
            ("climate-action", "Climate Action", {}),
            ("research", "Research", {}),
            ("capacity-building", "Capacity Building", {}),
            ("emergency-response", "Emergency Response", {}),
            ("advocacy", "Advocacy", {}),
            ("infrastructure", "Infrastructure", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.PILLAR,
        (
            ("youth-leadership", "Youth Leadership", {}),
            ("digital-transformation", "Digital Transformation", {}),
            ("economic-empowerment", "Economic Empowerment", {}),
            ("education-skills", "Education & Skills", {}),
            ("health-wellbeing", "Health & Wellbeing", {}),
            ("climate-sustainability", "Climate & Sustainability", {}),
            ("community-development", "Community Development", {}),
            ("advocacy-governance", "Advocacy & Governance", {}),
            ("institutional-strengthening", "Institutional Strengthening", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.SDG,
        (
            ("sdg-1", "SDG 1: No Poverty", {}),
            ("sdg-4", "SDG 4: Quality Education", {}),
            ("sdg-5", "SDG 5: Gender Equality", {}),
            ("sdg-8", "SDG 8: Decent Work & Economic Growth", {}),
            ("sdg-10", "SDG 10: Reduced Inequalities", {}),
            ("sdg-13", "SDG 13: Climate Action", {}),
            ("sdg-16", "SDG 16: Peace, Justice & Strong Institutions", {}),
            ("sdg-17", "SDG 17: Partnerships for the Goals", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.FUNDING_SOURCE,
        (
            ("internal", "Internal budget", {}),
            ("donor", "Donor funding", {}),
            ("grant", "Grant", {}),
            ("sponsorship", "Corporate sponsorship", {}),
            ("government", "Government funding", {}),
            ("partnership", "Partner contribution", {}),
            ("self-funded", "Self-funded / contributions", {}),
            ("in-kind", "In-kind support", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.BENEFICIARY_CATEGORY,
        (
            ("young-people", "Young people (15-35)", {}),
            ("youth-groups", "Youth groups & clubs", {}),
            ("women", "Women", {}),
            ("girls", "Girls", {}),
            ("students", "Students", {}),
            ("out-of-school", "Out-of-school youth", {}),
            ("entrepreneurs", "Young entrepreneurs", {}),
            ("communities", "Communities", {}),
            ("marginalized", "Marginalized groups", {}),
            ("pwd", "Persons with disabilities", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.RISK_CATEGORY,
        (
            ("strategic", "Strategic", {}),
            ("operational", "Operational", {}),
            ("financial", "Financial", {}),
            ("safeguarding", "Safeguarding", {}),
            ("reputational", "Reputational", {}),
            ("compliance", "Compliance & regulatory", {}),
            ("sustainability", "Sustainability", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.INDICATOR_TYPE,
        (
            ("output", "Output indicator", {}),
            ("outcome", "Outcome indicator", {}),
            ("impact", "Impact indicator", {}),
            ("process", "Process indicator", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.RESOURCE_TYPE,
        (
            ("human", "Human resources", {}),
            ("financial", "Financial resources", {}),
            ("equipment", "Equipment", {}),
            ("vehicles", "Vehicles", {}),
            ("facilities", "Facilities", {}),
            ("ict", "ICT resources", {}),
            ("materials", "Learning materials", {}),
            ("volunteers", "Volunteers", {}),
            ("consultants", "Consultants", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.DOCUMENT_TYPE,
        (
            ("concept-note", "Concept note", {}),
            ("proposal", "Project proposal", {}),
            ("work-plan", "Work plan", {}),
            ("budget", "Budget", {}),
            ("contract", "Contract", {}),
            ("mou", "Memorandum of understanding", {}),
            ("technical-report", "Technical report", {}),
            ("monitoring-report", "Monitoring report", {}),
            ("evaluation-report", "Evaluation report", {}),
            ("lessons-learned", "Lessons learned", {}),
            ("final-report", "Final report", {}),
            ("meeting-minutes", "Meeting minutes", {}),
            ("photo", "Photo", {}),
            ("video", "Video", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.LESSON_CATEGORY,
        (
            ("planning", "Planning", {}),
            ("implementation", "Implementation", {}),
            ("stakeholder-engagement", "Stakeholder engagement", {}),
            ("sustainability", "Sustainability", {}),
            ("partnerships", "Partnerships", {}),
            ("capacity", "Capacity building", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.EVIDENCE_TYPE,
        (
            ("photograph", "Photograph", {}),
            ("video", "Video", {}),
            ("attendance-register", "Attendance register", {}),
            ("participant-list", "Signed participant list", {}),
            ("meeting-minutes", "Meeting minutes", {}),
            ("monitoring-report", "Monitoring report", {}),
            ("evaluation-report", "Evaluation report", {}),
            ("financial-document", "Financial document", {}),
            ("receipt", "Receipt", {}),
            ("testimonial", "Beneficiary testimonial", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.BUDGET_CATEGORY,
        (
            ("personnel", "Personnel", {}),
            ("training", "Training", {}),
            ("travel", "Travel", {}),
            ("accommodation", "Accommodation", {}),
            ("equipment", "Equipment", {}),
            ("supplies", "Supplies", {}),
            ("logistics", "Logistics", {}),
            ("communications", "Communications", {}),
            ("monitoring", "Monitoring", {}),
            ("administration", "Administration", {}),
            ("contingency", "Contingency", {}),
            ("other", "Other approved costs", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.PROJECT_CLASSIFICATION,
        (
            ("community", "Community-led", {"area": "delivery"}),
            ("institution-led", "Institution-led", {"area": "delivery"}),
            ("donor-funded", "Donor-funded", {"area": "funding"}),
            ("self-funded", "Self-funded", {"area": "funding"}),
            ("partnership", "Partnership-delivered", {"area": "funding"}),
            ("regional", "Regional scope", {"area": "scope"}),
            ("district", "District scope", {"area": "scope"}),
            ("community-level", "Community-level scope", {"area": "scope"}),
            ("national", "National scope", {"area": "scope"}),
            ("innovation", "Innovation-driven", {"area": "approach"}),
            ("advocacy", "Advocacy-led", {"area": "approach"}),
            ("capacity-building", "Capacity-building", {"area": "approach"}),
            ("emergency", "Emergency response", {"area": "approach"}),
            ("research", "Research-driven", {"area": "approach"}),
            ("pilot", "Pilot / demonstration", {"area": "approach"}),
            ("scale-up", "Scale-up / replication", {"area": "approach"}),
        ),
    ),
)

DEFAULT_REFERENCE_SCHEMES = (
    ("work_plan", "Work Plan", "WPL"),
    ("activity", "Activity", "ACT"),
    ("task", "Task", "TSK"),
    ("milestone", "Milestone", "MSL"),
    ("deliverable", "Deliverable", "DLV"),
    ("risk", "Risk", "RSK"),
    ("issue", "Issue", "ISS"),
    ("change", "Change Request", "CHG"),
    ("evidence", "Evidence", "EVD"),
    ("program_beneficiary", "Program Beneficiary", "BNF"),
    ("wbs", "WBS Node", "WBS"),
)

PROGRAM_REFERENCE_SCHEME_MODULES = (
    ReferenceModules.PROGRAMS,
    ReferenceModules.PROJECTS,
)


def reference_scheme_defaults(code: str, name: str, prefix: str) -> dict:
    return {
        "name": name,
        "module": ReferenceModules.PROGRAMS,
        "record_type": code,
        "description": f"Centralized references for {name.lower()} records.",
        "prefix": prefix,
        "pattern": "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
        "organization_code": "SITADC",
        "sequence_length": 6,
        "start_value": 1,
        "reset_period": "NEVER",
        "status": "ACTIVE",
        "is_default_for_module": False,
        "is_default_for_record_type": True,
        "is_fallback": False,
        "is_active": True,
    }
