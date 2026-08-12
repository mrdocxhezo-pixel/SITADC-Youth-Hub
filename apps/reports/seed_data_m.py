"""Seed data for Category M — Quality Assurance templates."""

from __future__ import annotations

T = "TEXT"
MT = "MULTILINE_TEXT"
RT = "RICH_TEXT"
INT = "INTEGER"
DEC = "DECIMAL"
PCT = "PERCENTAGE"
DT = "DATE"
TM = "TIME"
DD = "DROPDOWN"
CB = "CHECKBOX"
DOC = "DOCUMENT"
IMG = "IMAGE"
VID = "VIDEO"
SIG = "SIGNATURE"
USR = "USER_SELECTOR"

CATEGORY_M_TEMPLATES: list[dict] = [
    {
        "code": "M1",
        "title": "Internal Quality Assessment",
        "description": "Internal assessment of program and organizational quality.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Assessment Info",
                "code": "assessment-info",
                "groups": [
                    {
                        "name": "Assessment Info",
                        "code": "assessment-info",
                        "fields": [
                            {"label": "Assessment Title", "code": "assessment_title", "field_type": T, "required": True},
                            {"label": "Assessment Date", "code": "assessment_date", "field_type": DT, "required": True},
                            {"label": "Assessor", "code": "assessor", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Quality Areas",
                "code": "quality-areas",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Quality Areas",
                        "code": "quality-areas",
                        "fields": [
                            {"label": "Quality Area", "code": "quality_area", "field_type": DD, "options": ["Planning", "Implementation", "M&E", "Reporting", "Financial Management", "HR Management", "Governance", "Other"], "required": True},
                            {"label": "Criteria", "code": "criteria", "field_type": MT, "required": True},
                            {"label": "Rating", "code": "rating", "field_type": DD, "options": ["Excellent", "Good", "Satisfactory", "Needs Improvement", "Poor"], "required": True},
                            {"label": "Evidence", "code": "evidence", "field_type": MT},
                            {"label": "Strengths", "code": "strengths", "field_type": MT},
                            {"label": "Areas for Improvement", "code": "improvement_areas", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Recommendations",
                "code": "recommendations",
                "groups": [
                    {
                        "name": "Recommendations",
                        "code": "recommendations",
                        "fields": [
                            {"label": "Overall Quality Score", "code": "overall_score", "field_type": DEC},
                            {"label": "Priority Recommendations", "code": "priority_recommendations", "field_type": RT, "required": True},
                            {"label": "Action Plan", "code": "action_plan", "field_type": MT},
                            {"label": "Next Assessment Date", "code": "next_assessment_date", "field_type": DT},
                            {"label": "Signed By", "code": "signed_by", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "M2",
        "title": "Compliance Checklist",
        "description": "Checklist for assessing compliance with organizational policies and standards.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Checklist Info",
                "code": "checklist-info",
                "groups": [
                    {
                        "name": "Checklist Info",
                        "code": "checklist-info",
                        "fields": [
                            {"label": "Assessment Period", "code": "assessment_period", "field_type": T, "required": True},
                            {"label": "Assessor", "code": "assessor", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Compliance Items",
                "code": "compliance-items",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Compliance Items",
                        "code": "compliance-items",
                        "fields": [
                            {"label": "Area", "code": "area", "field_type": T, "required": True},
                            {"label": "Requirement", "code": "requirement", "field_type": MT, "required": True},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Compliant", "Partially Compliant", "Non-Compliant", "N/A"], "required": True},
                            {"label": "Evidence", "code": "evidence", "field_type": MT},
                            {"label": "Gap Description", "code": "gap_description", "field_type": MT},
                            {"label": "Corrective Action", "code": "corrective_action", "field_type": MT},
                            {"label": "Responsible Person", "code": "responsible_person", "field_type": T},
                            {"label": "Target Date", "code": "target_date", "field_type": DT},
                        ],
                    }
                ],
            },
            {
                "name": "Summary",
                "code": "summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Total Items", "code": "total_items", "field_type": INT, "is_calculated": True, "formula": "count(items)"},
                            {"label": "Compliant Items", "code": "compliant_items", "field_type": INT},
                            {"label": "Compliance Rate", "code": "compliance_rate", "field_type": PCT, "is_calculated": True, "formula": "compliant_items / total_items * 100"},
                            {"label": "Key Gaps", "code": "key_gaps", "field_type": MT},
                            {"label": "Priority Actions", "code": "priority_actions", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "M3",
        "title": "Process Audit Report",
        "description": "Report from auditing specific organizational processes.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Audit Info",
                "code": "audit-info",
                "groups": [
                    {
                        "name": "Audit Info",
                        "code": "audit-info",
                        "fields": [
                            {"label": "Process Audited", "code": "process_audited", "field_type": T, "required": True},
                            {"label": "Audit Date", "code": "audit_date", "field_type": DT, "required": True},
                            {"label": "Auditor", "code": "auditor", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Audit Findings",
                "code": "audit-findings",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Audit Findings",
                        "code": "audit-findings",
                        "fields": [
                            {"label": "Process Step", "code": "process_step", "field_type": T, "required": True},
                            {"label": "Expected Standard", "code": "expected_standard", "field_type": MT, "required": True},
                            {"label": "Actual Practice", "code": "actual_practice", "field_type": MT, "required": True},
                            {"label": "Compliance", "code": "compliance", "field_type": DD, "options": ["Compliant", "Partially Compliant", "Non-Compliant"], "required": True},
                            {"label": "Risk Level", "code": "risk_level", "field_type": DD, "options": ["High", "Medium", "Low"]},
                            {"label": "Recommendation", "code": "recommendation", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Summary",
                "code": "summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Overall Compliance", "code": "overall_compliance", "field_type": PCT},
                            {"label": "Critical Findings", "code": "critical_findings", "field_type": INT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                            {"label": "Action Plan", "code": "action_plan", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "M4",
        "title": "Service Quality Report",
        "description": "Report on the quality of services delivered to beneficiaries.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Service Areas",
                "code": "service-areas",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Service Areas",
                        "code": "service-areas",
                        "fields": [
                            {"label": "Service Area", "code": "service_area", "field_type": T, "required": True},
                            {"label": "Target Standard", "code": "target_standard", "field_type": MT},
                            {"label": "Actual Performance", "code": "actual_performance", "field_type": MT},
                            {"label": "Rating", "code": "rating", "field_type": DD, "options": ["Excellent", "Good", "Satisfactory", "Needs Improvement", "Poor"], "required": True},
                            {"label": "Client Feedback", "code": "client_feedback", "field_type": MT},
                            {"label": "Improvement Actions", "code": "improvement_actions", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Satisfaction Survey",
                "code": "satisfaction-survey",
                "groups": [
                    {
                        "name": "Satisfaction Survey",
                        "code": "satisfaction-survey",
                        "fields": [
                            {"label": "Overall Satisfaction Score", "code": "satisfaction_score", "field_type": DEC},
                            {"label": "Response Rate", "code": "response_rate", "field_type": PCT},
                            {"label": "Net Promoter Score", "code": "nps", "field_type": DEC},
                            {"label": "Key Complaints", "code": "key_complaints", "field_type": MT},
                            {"label": "Key Compliments", "code": "key_compliments", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "M5",
        "title": "Corrective Action Report",
        "description": "Report tracking corrective actions from quality assessments.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Corrective Actions",
                "code": "corrective-actions",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Corrective Actions",
                        "code": "corrective-actions",
                        "fields": [
                            {"label": "Source", "code": "source", "field_type": DD, "options": ["Quality Assessment", "Audit", "Complaint", "Incident", "Other"], "required": True},
                            {"label": "Issue Description", "code": "issue_description", "field_type": MT, "required": True},
                            {"label": "Root Cause", "code": "root_cause", "field_type": MT},
                            {"label": "Corrective Action", "code": "corrective_action", "field_type": MT, "required": True},
                            {"label": "Responsible Person", "code": "responsible_person", "field_type": T, "required": True},
                            {"label": "Target Date", "code": "target_date", "field_type": DT, "required": True},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Open", "In Progress", "Completed", "Overdue"], "required": True},
                            {"label": "Evidence of Completion", "code": "evidence", "field_type": DOC},
                        ],
                    }
                ],
            },
            {
                "name": "Summary",
                "code": "summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Total Actions", "code": "total_actions", "field_type": INT, "is_calculated": True, "formula": "count(actions)"},
                            {"label": "Completed Actions", "code": "completed_actions", "field_type": INT},
                            {"label": "Completion Rate", "code": "completion_rate", "field_type": PCT, "is_calculated": True, "formula": "completed_actions / total_actions * 100"},
                            {"label": "Overdue Actions", "code": "overdue_actions", "field_type": INT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "M6",
        "title": "Continuous Improvement Report",
        "description": "Report on continuous improvement initiatives and outcomes.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Reporting Year", "code": "reporting_year", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Improvement Initiatives",
                "code": "improvement-initiatives",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Improvement Initiatives",
                        "code": "improvement-initiatives",
                        "fields": [
                            {"label": "Initiative", "code": "initiative", "field_type": T, "required": True},
                            {"label": "Area", "code": "area", "field_type": T, "required": True},
                            {"label": "Description", "code": "description", "field_type": MT, "required": True},
                            {"label": "Implementation Date", "code": "implementation_date", "field_type": DT},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Planned", "In Progress", "Completed", "Evaluated"]},
                            {"label": "Outcome", "code": "outcome", "field_type": MT},
                            {"label": "Impact", "code": "impact", "field_type": DD, "options": ["High", "Medium", "Low"]},
                        ],
                    }
                ],
            },
            {
                "name": "Lessons Learned",
                "code": "lessons-learned",
                "groups": [
                    {
                        "name": "Lessons Learned",
                        "code": "lessons-learned",
                        "fields": [
                            {"label": "Key Lessons", "code": "key_lessons", "field_type": RT, "required": True},
                            {"label": "Best Practices", "code": "best_practices", "field_type": RT},
                            {"label": "Recommendations for Next Year", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
]
