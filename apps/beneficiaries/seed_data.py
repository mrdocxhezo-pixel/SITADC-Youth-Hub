"""Declarative default taxonomies and reference schemes for beneficiary management."""

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
            ("orphan-vulnerable", "Orphan & Vulnerable Child", {}),
            ("youth-unemployed", "Youth (Unemployed)", {}),
            ("youth-student", "Youth (Student)", {}),
            ("female-headed", "Female-Headed Household", {}),
            ("disability", "Person Living with Disability", {}),
            ("rural", "Rural Community Member", {}),
            ("urban-poor", "Urban Poor", {}),
            ("elderly", "Elderly Person", {}),
            ("chronic-illness", "Person with Chronic Illness", {}),
            ("other", "Other", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.VULNERABILITY,
        (
            ("poverty", "Extreme Poverty", {}),
            ("food-insecurity", "Food Insecurity", {}),
            ("orphan", "Orphaned", {}),
            ("child-headed", "Child-Headed Household", {}),
            ("disability", "Disability", {}),
            ("chronic-illness", "Chronic Illness", {}),
            ("refugee", "Refugee or Displaced", {}),
            ("abuse", "Abuse Survivor", {}),
            ("exploitation", "At Risk of Exploitation", {}),
            ("school-dropout", "School Dropout", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.DISABILITY,
        (
            ("physical", "Physical Impairment", {}),
            ("visual", "Visual Impairment", {}),
            ("hearing", "Hearing Impairment", {}),
            ("speech", "Speech Impairment", {}),
            ("intellectual", "Intellectual Disability", {}),
            ("psychosocial", "Psychosocial Disability", {}),
            ("multiple", "Multiple Disabilities", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.GENDER,
        (
            ("male", "Male", {}),
            ("female", "Female", {}),
            ("non-binary", "Non-binary", {}),
            ("prefer-not", "Prefer not to say", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.EDUCATION_LEVEL,
        (
            ("none", "No Formal Education", {}),
            ("primary", "Primary", {}),
            ("secondary", "Secondary", {}),
            ("certificate", "Certificate", {}),
            ("diploma", "Diploma", {}),
            ("degree", "Degree", {}),
            ("postgraduate", "Postgraduate", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.OCCUPATION,
        (
            ("student", "Student", {}),
            ("farming", "Farmer", {}),
            ("informal", "Informal Trader", {}),
            ("artisan", "Artisan", {}),
            ("unemployed", "Unemployed", {}),
            ("employed", "Formally Employed", {}),
            ("other", "Other", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.MARITAL_STATUS,
        (
            ("single", "Single", {}),
            ("married", "Married", {}),
            ("divorced", "Divorced", {}),
            ("widowed", "Widowed", {}),
            ("separated", "Separated", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.HOUSEHOLD_TYPE,
        (
            ("two-parent", "Two-Parent Family", {}),
            ("single-parent", "Single-Parent Family", {}),
            ("child-headed", "Child-Headed", {}),
            ("grandparent", "Grandparent-Led", {}),
            ("foster", "Foster Family", {}),
            ("sibling", "Sibling-Led", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.GROUP_TYPE,
        (
            ("savings", "Savings & Loan Group", {}),
            ("youth-club", "Youth Club", {}),
            ("women", "Women's Group", {}),
            ("farmers", "Farmer Cooperative", {}),
            ("training", "Skills Training Cohort", {}),
            ("advocacy", "Advocacy Group", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.ENROLLMENT_SOURCE,
        (
            ("community-outreach", "Community Outreach", {}),
            ("referral-partner", "Referral from Partner", {}),
            ("self-referral", "Self Referral", {}),
            ("school", "School-Based Identification", {}),
            ("government", "Government Referral", {}),
            ("volunteer", "Volunteer Identification", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.ENROLLMENT_TYPE,
        (
            ("individual", "Individual", {}),
            ("household", "Household", {}),
            ("group", "Group Enrollment", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.EXIT_REASON,
        (
            ("graduated", "Graduated", {}),
            ("relocated", "Relocated", {}),
            ("dropped", "Dropped Out", {}),
            ("deceased", "Deceased", {}),
            ("ineligible", "No Longer Eligible", {}),
            ("transferred", "Transferred", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.REFERRAL_TYPE,
        (
            ("health", "Health Services", {}),
            ("education", "Education Services", {}),
            ("protection", "Child Protection", {}),
            ("legal", "Legal Aid", {}),
            ("livelihood", "Livelihood Support", {}),
            ("psychosocial", "Psychosocial Support", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.SERVICE_TYPE,
        (
            ("school-fees", "School Fees Support", {}),
            ("scholarship", "Scholarship", {}),
            ("food", "Food Assistance", {}),
            ("healthcare", "Healthcare Support", {}),
            ("counseling", "Counselling", {}),
            ("mentorship", "Mentorship", {}),
            ("skills-training", "Skills Training", {}),
            ("startup-capital", "Start-up Capital", {}),
            ("school-supplies", "School Supplies", {}),
            ("legal-support", "Legal Support", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.CASE_NOTE_TYPE,
        (
            ("home-visit", "Home Visit", {}),
            ("case-conference", "Case Conference", {}),
            ("phone-contact", "Phone Contact", {}),
            ("school-visit", "School Visit", {}),
            ("crisis", "Crisis Intervention", {}),
            ("regular-update", "Regular Update", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.FOLLOW_UP_PURPOSE,
        (
            ("wellbeing", "Well-being Check", {}),
            ("school-attendance", "School Attendance", {}),
            ("service-uptake", "Service Uptake", {}),
            ("case-review", "Case Review", {}),
            ("home-visit", "Home Visit", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.SAFEGUARDING_CATEGORY,
        (
            ("physical-abuse", "Physical Abuse", {}),
            ("emotional-abuse", "Emotional Abuse", {}),
            ("sexual-abuse", "Sexual Abuse", {}),
            ("neglect", "Neglect", {}),
            ("exploitation", "Exploitation", {}),
            ("bullying", "Bullying", {}),
            ("child-labour", "Child Labour", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.DOCUMENT_TYPE,
        (
            ("national-id", "National ID", {}),
            ("birth-certificate", "Birth Certificate", {}),
            ("school-record", "School Record", {}),
            ("medical-record", "Medical Record", {}),
            ("consent-form", "Consent Form", {}),
            ("assessment-report", "Assessment Report", {}),
            ("enrollment-form", "Enrollment Form", {}),
            ("case-plan", "Case Plan", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.NEED_TYPE,
        (
            ("education", "Education", {}),
            ("health", "Health", {}),
            ("nutrition", "Nutrition", {}),
            ("protection", "Protection", {}),
            ("livelihood", "Livelihood", {}),
            ("psychosocial", "Psychosocial", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.OUTCOME_INDICATOR,
        (
            ("school-enrolled", "Enrolled in School", {}),
            ("academic-progress", "Improved Academic Performance", {}),
            ("health-improved", "Improved Health", {}),
            ("income-improved", "Improved Household Income", {}),
            ("skills-gained", "Skills Gained", {}),
            ("self-esteem", "Improved Self-esteem", {}),
            ("food-security", "Improved Food Security", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.ASSESSMENT_TYPE,
        (
            ("intake", "Intake Assessment", {}),
            ("needs", "Needs Assessment", {}),
            ("vulnerability", "Vulnerability Assessment", {}),
            ("home-environment", "Home Environment Assessment", {}),
            ("progress", "Progress Review", {}),
            ("exit", "Exit Assessment", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.COMMUNICATION_TYPE,
        (
            ("informational", "Informational", {}),
            ("reminder", "Reminder", {}),
            ("follow-up", "Follow-up", {}),
            ("notification", "Notification", {}),
            ("sensitive-info", "Sensitive Information", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.RELATIONSHIP,
        (
            ("head", "Head of Household", {}),
            ("spouse", "Spouse", {}),
            ("child", "Child", {}),
            ("grandchild", "Grandchild", {}),
            ("sibling", "Sibling", {}),
            ("parent", "Parent", {}),
            ("other-relative", "Other Relative", {}),
            ("non-relative", "Non-Relative", {}),
        ),
    ),
)

DEFAULT_REFERENCE_SCHEMES = (
    ("household", "Household", "HHL"),
    ("beneficiary_group", "Beneficiary Group", "GRP"),
    ("beneficiary_enrollment", "Beneficiary Enrollment", "ENR"),
    ("beneficiary_participation", "Beneficiary Participation", "PRT"),
    ("beneficiary_assessment", "Beneficiary Assessment", "ASS"),
    ("beneficiary_referral", "Beneficiary Referral", "RFL"),
    ("beneficiary_service", "Service Delivery", "SRV"),
    ("beneficiary_case_note", "Case Note", "CSE"),
    ("beneficiary_support_plan", "Support Plan", "SPL"),
    ("beneficiary_exit", "Beneficiary Exit", "EXT"),
    ("beneficiary_transfer", "Beneficiary Transfer", "TRF"),
    ("beneficiary_document", "Beneficiary Document", "BND"),
    ("beneficiary_consent", "Beneficiary Consent", "CNS"),
    ("beneficiary_safeguarding", "Safeguarding Record", "SFG"),
    ("beneficiary_outcome", "Beneficiary Outcome", "OUT"),
    ("beneficiary_feedback", "Beneficiary Feedback", "FDB"),
)

DEFAULT_REFERENCE_SCHEME_MODULE = ReferenceModules.BENEFICIARIES
