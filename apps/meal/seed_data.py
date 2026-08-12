"""Declarative default taxonomies and reference schemes for the MEAL module."""

from __future__ import annotations

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
        ReferenceDataKind.REPORTING_FREQUENCY,
        (
            ("daily", "Daily", {}),
            ("weekly", "Weekly", {}),
            ("monthly", "Monthly", {}),
            ("quarterly", "Quarterly", {}),
            ("semi-annual", "Semi-annual", {}),
            ("annual", "Annual", {}),
            ("continuous", "Continuous", {}),
            ("event-based", "Event-based", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.EVALUATION_TYPE,
        (
            ("baseline", "Baseline evaluation", {}),
            ("midline", "Midline evaluation", {}),
            ("endline", "Endline evaluation", {}),
            ("impact", "Impact evaluation", {}),
            ("process", "Process evaluation", {}),
            ("performance", "Performance evaluation", {}),
            ("external", "External evaluation", {}),
            ("internal", "Internal evaluation", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.DATA_SOURCE_TYPE,
        (
            ("attendance-register", "Attendance register", {}),
            ("beneficiary-register", "Beneficiary register", {}),
            ("household-survey", "Household survey", {}),
            ("monitoring-visit", "Monitoring visit", {}),
            ("training-register", "Training register", {}),
            ("financial-report", "Financial report", {}),
            ("project-report", "Project report", {}),
            ("community-feedback", "Community feedback", {}),
            ("mobile-collection", "Mobile data collection", {}),
            ("administrative-records", "Administrative records", {}),
            ("education-records", "Education records (authorized)", {}),
            ("health-records", "Health records (authorized)", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.COLLECTION_TOOL_TYPE,
        (
            ("digital-form", "Digital form", {}),
            ("survey-questionnaire", "Survey questionnaire", {}),
            ("observation-checklist", "Observation checklist", {}),
            ("interview-guide", "Interview guide", {}),
            ("fgd-tool", "Focus group discussion tool", {}),
            ("kii-template", "Key informant interview template", {}),
            ("mobile-form", "Mobile collection form", {}),
            ("attendance-register", "Attendance register", {}),
            ("assessment-tool", "Assessment tool", {}),
            ("evaluation-questionnaire", "Evaluation questionnaire", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.COLLECTION_METHOD,
        (
            ("direct-observation", "Direct observation", {}),
            ("face-to-face-interview", "Face-to-face interview", {}),
            ("telephone-interview", "Telephone interview", {}),
            ("self-administered-survey", "Self-administered survey", {}),
            ("focus-group-discussion", "Focus group discussion", {}),
            ("key-informant-interview", "Key informant interview", {}),
            ("document-review", "Document review", {}),
            ("mobile-data-collection", "Mobile data collection", {}),
            ("register-review", "Register review", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.DISAGGREGATION_DIMENSION,
        (
            ("gender", "Gender", {}),
            ("age-group", "Age group", {}),
            ("disability", "Disability", {}),
            ("district", "District", {}),
            ("community", "Community", {}),
            ("education-level", "Education level", {}),
            ("employment-status", "Employment status", {}),
            ("vulnerability", "Vulnerability", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.DATA_QUALITY_DIMENSION,
        (
            ("accuracy", "Accuracy", {}),
            ("completeness", "Completeness", {}),
            ("consistency", "Consistency", {}),
            ("reliability", "Reliability", {}),
            ("timeliness", "Timeliness", {}),
            ("precision", "Precision", {}),
            ("integrity", "Integrity", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.COMPLAINT_CATEGORY,
        (
            ("service-delivery", "Service delivery", {}),
            ("staff-conduct", "Staff conduct", {}),
            ("safeguarding", "Safeguarding concern", {}),
            ("beneficiary-selection", "Beneficiary selection", {}),
            ("resource-distribution", "Resource distribution", {}),
            ("communication", "Communication", {}),
            ("data-protection", "Data protection", {}),
            ("other", "Other", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.FEEDBACK_CATEGORY,
        (
            ("program-satisfaction", "Program satisfaction", {}),
            ("suggestion", "Suggestion", {}),
            ("training-quality", "Training quality", {}),
            ("materials", "Materials and resources", {}),
            ("staff-support", "Staff support", {}),
            ("other", "Other", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.SUGGESTION_CHANNEL,
        (
            ("suggestion-box", "Suggestion box", {}),
            ("hotline", "Hotline", {}),
            ("in-person", "In-person", {}),
            ("email", "Email", {}),
            ("sms", "SMS", {}),
            ("community-meeting", "Community meeting", {}),
            ("online-form", "Online form", {}),
            ("social-media", "Social media", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.LEARNING_CATEGORY,
        (
            ("lesson-learned", "Lesson learned", {}),
            ("innovation", "Innovation", {}),
            ("reflection", "Reflection session", {}),
            ("after-action-review", "After-action review", {}),
            ("success-story", "Success story", {}),
            ("knowledge-product", "Knowledge product", {}),
            ("other", "Other", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.LESSON_CATEGORY,
        (
            ("success", "Success", {}),
            ("challenge", "Challenge", {}),
            ("best-practice", "Best practice", {}),
            ("innovation", "Innovation", {}),
            ("recommendation", "Recommendation", {}),
            ("other", "Other", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.SCORECARD_PERIOD,
        (
            ("monthly", "Monthly", {}),
            ("quarterly", "Quarterly", {}),
            ("semi-annual", "Semi-annual", {}),
            ("annual", "Annual", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.INDICATOR_UNIT,
        (
            ("number", "Number", {}),
            ("percentage", "Percentage (%)", {}),
            ("ratio", "Ratio", {}),
            ("count", "Count", {}),
            ("score", "Score", {}),
            ("monetary", "Monetary (ZMW)", {}),
            ("days", "Days", {}),
            ("other", "Other", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.VERIFICATION_METHOD,
        (
            ("document-review", "Document review", {}),
            ("field-visit", "Field visit", {}),
            ("spot-check", "Spot check", {}),
            ("dqa", "Data quality assessment", {}),
            ("interview", "Interview verification", {}),
            ("third-party", "Third-party verification", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.OUTCOME_CATEGORY,
        (
            ("knowledge", "Improved knowledge", {}),
            ("skills", "Increased skills", {}),
            ("behaviour", "Behaviour change", {}),
            ("employment", "Employment opportunity", {}),
            ("livelihoods", "Improved livelihoods", {}),
            ("participation", "Community participation", {}),
            ("institutional", "Institutional strengthening", {}),
            ("other", "Other", {}),
        ),
    ),
    *_rows(
        ReferenceDataKind.GEOGRAPHIC_AREA,
        (
            ("national", "National", {}),
            ("provincial", "Provincial", {}),
            ("district", "District", {}),
            ("community", "Community", {}),
        ),
    ),
)


DEFAULT_REFERENCE_SCHEMES = (
    ("theory_of_change", "Theory of Change", "TOC"),
    ("results_framework", "Results Framework", "RFR"),
    ("logframe", "Logical Framework", "LGF"),
    ("indicator", "Indicator", "IND"),
    ("indicator_baseline", "Indicator Baseline", "BSL"),
    ("indicator_target", "Indicator Target", "TGT"),
    ("data_collection_plan", "Data Collection Plan", "DCP"),
    ("monitoring_plan", "Monitoring Plan", "MNP"),
    ("monitoring_visit", "Monitoring Visit", "MON"),
    ("evaluation", "Evaluation", "EVL"),
    ("dqa", "Data Quality Assessment", "DQA"),
    ("complaint", "Complaint", "CMP"),
    ("feedback", "Feedback", "FDB"),
    ("corrective_action", "Corrective Action", "CRA"),
    ("outcome_harvest", "Outcome Harvest", "OCH"),
    ("learning_log", "Learning Log", "LLG"),
    ("best_practice", "Best Practice", "BPR"),
    ("meal_lesson", "Lesson Learned", "LSN"),
    ("scorecard", "Performance Scorecard", "SCR"),
    ("meal_report", "MEAL Report", "MRL"),
    ("organizational_kpi", "Organizational KPI", "KPI"),
)
