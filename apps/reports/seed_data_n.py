"""Seed data for Category N — Risk and Compliance templates."""

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

CATEGORY_N_TEMPLATES: list[dict] = [
    {
        "code": "N1",
        "title": "Risk Register",
        "description": "Register of organizational risks with assessment and mitigation plans.",
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
                "name": "Risks",
                "code": "risks",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Risks",
                        "code": "risks",
                        "fields": [
                            {"label": "Risk Description", "code": "risk_description", "field_type": MT, "required": True},
                            {"label": "Risk Category", "code": "risk_category", "field_type": DD, "options": ["Strategic", "Operational", "Financial", "Compliance", "Reputational", "Safety", "IT", "Other"], "required": True},
                            {"label": "Likelihood", "code": "likelihood", "field_type": DD, "options": ["Very High", "High", "Medium", "Low", "Very Low"], "required": True},
                            {"label": "Impact", "code": "impact", "field_type": DD, "options": ["Very High", "High", "Medium", "Low", "Very Low"], "required": True},
                            {"label": "Risk Score", "code": "risk_score", "field_type": DEC, "is_calculated": True, "formula": "likelihood * impact"},
                            {"label": "Risk Level", "code": "risk_level", "field_type": DD, "options": ["Critical", "High", "Medium", "Low"], "required": True},
                            {"label": "Mitigation Measures", "code": "mitigation_measures", "field_type": MT, "required": True},
                            {"label": "Risk Owner", "code": "risk_owner", "field_type": T, "required": True},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Open", "Mitigated", "Closed", "Accepted"]},
                            {"label": "Review Date", "code": "review_date", "field_type": DT},
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
                            {"label": "Total Risks", "code": "total_risks", "field_type": INT, "is_calculated": True, "formula": "count(risks)"},
                            {"label": "Critical Risks", "code": "critical_risks", "field_type": INT},
                            {"label": "High Risks", "code": "high_risks", "field_type": INT},
                            {"label": "Medium Risks", "code": "medium_risks", "field_type": INT},
                            {"label": "Low Risks", "code": "low_risks", "field_type": INT},
                            {"label": "Risk Overview", "code": "risk_overview", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "N2",
        "title": "Incident Report",
        "description": "Report documenting organizational incidents and responses.",
        "reporting_frequency": "ONE_OFF",
        "access_restricted": True,
        "sections": [
            {
                "name": "Incident Info",
                "code": "incident-info",
                "groups": [
                    {
                        "name": "Incident Info",
                        "code": "incident-info",
                        "fields": [
                            {"label": "Incident Reference", "code": "incident_ref", "field_type": T, "required": True},
                            {"label": "Date of Incident", "code": "incident_date", "field_type": DT, "required": True},
                            {"label": "Time", "code": "incident_time", "field_type": TM},
                            {"label": "Location", "code": "location", "field_type": T, "required": True},
                            {"label": "Reported By", "code": "reported_by", "field_type": T, "required": True},
                            {"label": "Report Date", "code": "report_date", "field_type": DT, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Incident Details",
                "code": "incident-details",
                "groups": [
                    {
                        "name": "Incident Details",
                        "code": "incident-details",
                        "fields": [
                            {"label": "Incident Type", "code": "incident_type", "field_type": DD, "options": ["Safety", "Security", "Health", "Property Damage", "Data Breach", "Fraud", "Harassment", "Other"], "required": True},
                            {"label": "Description", "code": "description", "field_type": MT, "required": True},
                            {"label": "People Involved", "code": "people_involved", "field_type": MT},
                            {"label": "Witnesses", "code": "witnesses", "field_type": MT},
                            {"label": "Injuries", "code": "injuries", "field_type": MT},
                            {"label": "Damage/Loss", "code": "damage_loss", "field_type": MT},
                            {"label": "Immediate Actions Taken", "code": "immediate_actions", "field_type": MT, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Investigation",
                "code": "investigation",
                "groups": [
                    {
                        "name": "Investigation",
                        "code": "investigation",
                        "fields": [
                            {"label": "Root Cause", "code": "root_cause", "field_type": MT},
                            {"label": "Contributing Factors", "code": "contributing_factors", "field_type": MT},
                            {"label": "Corrective Actions", "code": "corrective_actions", "field_type": MT},
                            {"label": "Preventive Measures", "code": "preventive_measures", "field_type": MT},
                            {"label": "Responsible Person", "code": "responsible_person", "field_type": T},
                            {"label": "Target Date", "code": "target_date", "field_type": DT},
                        ],
                    }
                ],
            },
            {
                "name": "Closure",
                "code": "closure",
                "access_restricted": True,
                "groups": [
                    {
                        "name": "Closure",
                        "code": "closure",
                        "fields": [
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Open", "Investigating", "Closed"], "required": True},
                            {"label": "Lessons Learned", "code": "lessons_learned", "field_type": MT},
                            {"label": "Report Approved By", "code": "approved_by", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "N3",
        "title": "Safeguarding Report",
        "description": "Report on safeguarding concerns, investigations and actions.",
        "reporting_frequency": "ONE_OFF",
        "access_restricted": True,
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Report Reference", "code": "report_ref", "field_type": T, "required": True},
                            {"label": "Date Reported", "code": "date_reported", "field_type": DT, "required": True},
                            {"label": "Reported By", "code": "reported_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Concern Details",
                "code": "concern-details",
                "groups": [
                    {
                        "name": "Concern Details",
                        "code": "concern-details",
                        "fields": [
                            {"label": "Type of Concern", "code": "concern_type", "field_type": DD, "options": ["Child Abuse", "Exploitation", "Harassment", "Discrimination", "Neglect", "Other"], "required": True},
                            {"label": "Description", "code": "description", "field_type": MT, "required": True},
                            {"label": "Person Affected", "code": "person_affected", "field_type": T},
                            {"label": "Relationship to Organization", "code": "relationship", "field_type": T},
                            {"label": "Location", "code": "location", "field_type": T},
                            {"label": "Date of Incident", "code": "incident_date", "field_type": DT},
                            {"label": "Immediate Actions", "code": "immediate_actions", "field_type": MT, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Investigation",
                "code": "investigation",
                "groups": [
                    {
                        "name": "Investigation",
                        "code": "investigation",
                        "fields": [
                            {"label": "Investigation Status", "code": "investigation_status", "field_type": DD, "options": ["Not Started", "In Progress", "Completed"]},
                            {"label": "Findings", "code": "findings", "field_type": MT},
                            {"label": "Actions Taken", "code": "actions_taken", "field_type": MT},
                            {"label": "Referral Made", "code": "referral_made", "field_type": CB},
                            {"label": "Referral Organization", "code": "referral_organization", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Closure",
                "code": "closure",
                "access_restricted": True,
                "groups": [
                    {
                        "name": "Closure",
                        "code": "closure",
                        "fields": [
                            {"label": "Outcome", "code": "outcome", "field_type": DD, "options": ["Substantiated", "Unsubstantiated", "Partially Substantiated", "Withdrawn"]},
                            {"label": "Follow-up Required", "code": "followup_required", "field_type": CB},
                            {"label": "Report Approved By", "code": "approved_by", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "N4",
        "title": "Complaints Register",
        "description": "Register of all complaints received and their resolution status.",
        "reporting_frequency": "QUARTERLY",
        "access_restricted": True,
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
                "name": "Complaints",
                "code": "complaints",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Complaints",
                        "code": "complaints",
                        "fields": [
                            {"label": "Complaint Reference", "code": "complaint_ref", "field_type": T, "required": True},
                            {"label": "Date Received", "code": "date_received", "field_type": DT, "required": True},
                            {"label": "Source", "code": "source", "field_type": DD, "options": ["Beneficiary", "Staff", "Volunteer", "Partner", "Community", "Anonymous", "Other"], "required": True},
                            {"label": "Category", "code": "category", "field_type": DD, "options": ["Service Quality", "Staff Conduct", "Program Design", "Accessibility", "Discrimination", "Safety", "Other"], "required": True},
                            {"label": "Description", "code": "description", "field_type": MT, "required": True},
                            {"label": "Severity", "code": "severity", "field_type": DD, "options": ["High", "Medium", "Low"], "required": True},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Received", "Acknowledged", "Investigating", "Resolved", "Escalated", "Closed"], "required": True},
                            {"label": "Investigation Notes", "code": "investigation_notes", "field_type": MT},
                            {"label": "Resolution", "code": "resolution", "field_type": MT},
                            {"label": "Date Resolved", "code": "date_resolved", "field_type": DT},
                            {"label": "Complainant Satisfaction", "code": "complainant_satisfaction", "field_type": DD, "options": ["Satisfied", "Neutral", "Dissatisfied"]},
                        ],
                    }
                ],
            },
            {
                "name": "Summary",
                "code": "summary",
                "access_restricted": True,
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Total Complaints", "code": "total_complaints", "field_type": INT, "is_calculated": True, "formula": "count(complaints)"},
                            {"label": "Resolved Complaints", "code": "resolved_complaints", "field_type": INT},
                            {"label": "Resolution Rate", "code": "resolution_rate", "field_type": PCT, "is_calculated": True, "formula": "resolved_complaints / total_complaints * 100"},
                            {"label": "Average Resolution Time", "code": "avg_resolution_time", "field_type": T},
                            {"label": "Trends", "code": "trends", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "N5",
        "title": "Whistleblower Report",
        "description": "Report on whistleblower disclosures and investigations.",
        "reporting_frequency": "ONE_OFF",
        "access_restricted": True,
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Report Reference", "code": "report_ref", "field_type": T, "required": True},
                            {"label": "Date Received", "code": "date_received", "field_type": DT, "required": True},
                            {"label": "Received By", "code": "received_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Disclosure",
                "code": "disclosure",
                "groups": [
                    {
                        "name": "Disclosure",
                        "code": "disclosure",
                        "fields": [
                            {"label": "Type of Misconduct", "code": "misconduct_type", "field_type": DD, "options": ["Fraud", "Corruption", "Financial Irregularity", "Policy Violation", "Safety Violation", "Environmental", "Other"], "required": True},
                            {"label": "Description", "code": "description", "field_type": MT, "required": True},
                            {"label": "Persons Involved", "code": "persons_involved", "field_type": MT},
                            {"label": "Date of Alleged Misconduct", "code": "misconduct_date", "field_type": DT},
                            {"label": "Evidence Provided", "code": "evidence_provided", "field_type": MT},
                            {"label": "Anonymous", "code": "anonymous", "field_type": CB},
                        ],
                    }
                ],
            },
            {
                "name": "Investigation",
                "code": "investigation",
                "groups": [
                    {
                        "name": "Investigation",
                        "code": "investigation",
                        "fields": [
                            {"label": "Investigation Status", "code": "investigation_status", "field_type": DD, "options": ["Not Started", "In Progress", "Completed"]},
                            {"label": "Investigator", "code": "investigator", "field_type": T},
                            {"label": "Findings", "code": "findings", "field_type": MT},
                            {"label": "Actions Taken", "code": "actions_taken", "field_type": MT},
                            {"label": "Outcome", "code": "outcome", "field_type": DD, "options": ["Substantiated", "Unsubstantiated", "Partially Substantiated"]},
                        ],
                    }
                ],
            },
            {
                "name": "Closure",
                "code": "closure",
                "access_restricted": True,
                "groups": [
                    {
                        "name": "Closure",
                        "code": "closure",
                        "fields": [
                            {"label": "Lessons Learned", "code": "lessons_learned", "field_type": MT},
                            {"label": "Policy Changes Needed", "code": "policy_changes", "field_type": MT},
                            {"label": "Report Approved By", "code": "approved_by", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "N6",
        "title": "Ethics Report",
        "description": "Report on ethical considerations and compliance in programs.",
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
                "name": "Ethics Areas",
                "code": "ethics-areas",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Ethics Areas",
                        "code": "ethics-areas",
                        "fields": [
                            {"label": "Area", "code": "area", "field_type": DD, "options": ["Research Ethics", "Beneficiary Rights", "Staff Conduct", "Conflict of Interest", "Data Privacy", "Environmental Ethics", "Other"], "required": True},
                            {"label": "Policy", "code": "policy", "field_type": MT},
                            {"label": "Compliance Status", "code": "compliance_status", "field_type": DD, "options": ["Compliant", "Partially Compliant", "Non-Compliant"], "required": True},
                            {"label": "Issues Identified", "code": "issues_identified", "field_type": MT},
                            {"label": "Actions Taken", "code": "actions_taken", "field_type": MT},
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
                            {"label": "Overall Ethics Rating", "code": "ethics_rating", "field_type": DD, "options": ["Strong", "Adequate", "Needs Improvement", "Weak"]},
                            {"label": "Key Concerns", "code": "key_concerns", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "N7",
        "title": "Compliance Report",
        "description": "Report on compliance with laws, regulations and organizational policies.",
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
                "name": "Compliance Areas",
                "code": "compliance-areas",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Compliance Areas",
                        "code": "compliance-areas",
                        "fields": [
                            {"label": "Area", "code": "area", "field_type": DD, "options": ["Legal", "Regulatory", "Donor Requirements", "Organizational Policy", "Labor Law", "Tax", "Environmental", "Other"], "required": True},
                            {"label": "Requirement", "code": "requirement", "field_type": MT, "required": True},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Compliant", "Partially Compliant", "Non-Compliant", "N/A"], "required": True},
                            {"label": "Evidence", "code": "evidence", "field_type": MT},
                            {"label": "Gaps", "code": "gaps", "field_type": MT},
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
                            {"label": "Overall Compliance Score", "code": "overall_compliance", "field_type": PCT},
                            {"label": "Critical Non-Compliances", "code": "critical_non_compliance", "field_type": INT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                            {"label": "Approved By", "code": "approved_by", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
]
