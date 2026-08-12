"""Seed data for Category K — Partnership templates."""

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

CATEGORY_K_TEMPLATES: list[dict] = [
    {
        "code": "K1",
        "title": "Stakeholder Mapping Report",
        "description": "Report mapping stakeholders, their interests and influence.",
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
                "name": "Stakeholders",
                "code": "stakeholders",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Stakeholders",
                        "code": "stakeholders",
                        "fields": [
                            {"label": "Stakeholder Name", "code": "stakeholder_name", "field_type": T, "required": True},
                            {"label": "Organization", "code": "organization", "field_type": T},
                            {"label": "Category", "code": "category", "field_type": DD, "options": ["Government", "NGO", "Private Sector", "Community", "Academic", "International", "Other"], "required": True},
                            {"label": "Interest Level", "code": "interest_level", "field_type": DD, "options": ["High", "Medium", "Low"], "required": True},
                            {"label": "Influence Level", "code": "influence_level", "field_type": DD, "options": ["High", "Medium", "Low"], "required": True},
                            {"label": "Current Relationship", "code": "current_relationship", "field_type": DD, "options": ["Strong", "Good", "Neutral", "Weak", "None"]},
                            {"label": "Potential Contribution", "code": "potential_contribution", "field_type": MT},
                            {"label": "Engagement Strategy", "code": "engagement_strategy", "field_type": MT},
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
                            {"label": "Total Stakeholders", "code": "total_stakeholders", "field_type": INT, "is_calculated": True, "formula": "count(stakeholders)"},
                            {"label": "Key Partners", "code": "key_partners", "field_type": MT},
                            {"label": "Engagement Priorities", "code": "engagement_priorities", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "K2",
        "title": "Partnership Register",
        "description": "Register of all partnerships with details and status.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Partnerships",
                "code": "partnerships",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Partnerships",
                        "code": "partnerships",
                        "fields": [
                            {"label": "Partner Name", "code": "partner_name", "field_type": T, "required": True},
                            {"label": "Contact Person", "code": "contact_person", "field_type": T},
                            {"label": "Email", "code": "email", "field_type": T},
                            {"label": "Phone", "code": "phone", "field_type": T},
                            {"label": "Partnership Type", "code": "partnership_type", "field_type": DD, "options": ["Implementation", "Technical", "Financial", "Advocacy", "Research", "Other"], "required": True},
                            {"label": "Start Date", "code": "start_date", "field_type": DT, "required": True},
                            {"label": "End Date", "code": "end_date", "field_type": DT},
                            {"label": "MoU on File", "code": "mou_on_file", "field_type": CB},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Active", "Completed", "Suspended", "Terminated"], "required": True},
                            {"label": "Key Contact", "code": "key_contact", "field_type": T},
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
                            {"label": "Total Partnerships", "code": "total_partnerships", "field_type": INT, "is_calculated": True, "formula": "count(partnerships)"},
                            {"label": "Active Partnerships", "code": "active_partnerships", "field_type": INT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "K3",
        "title": "Partnership Performance Report",
        "description": "Report evaluating the performance of partnerships.",
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
                "name": "Partnership Evaluations",
                "code": "partnership-evaluations",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Partnership Evaluations",
                        "code": "partnership-evaluations",
                        "fields": [
                            {"label": "Partner Name", "code": "partner_name", "field_type": T, "required": True},
                            {"label": "Contribution to Objectives", "code": "contribution", "field_type": DD, "options": ["Significant", "Moderate", "Minimal", "None"], "required": True},
                            {"label": "Reliability", "code": "reliability", "field_type": DD, "options": ["Excellent", "Good", "Average", "Poor"]},
                            {"label": "Communication", "code": "communication", "field_type": DD, "options": ["Excellent", "Good", "Average", "Poor"]},
                            {"label": "Value for Money", "code": "value_for_money", "field_type": DD, "options": ["Excellent", "Good", "Average", "Poor"]},
                            {"label": "Overall Rating", "code": "overall_rating", "field_type": DD, "options": ["Excellent", "Good", "Satisfactory", "Needs Improvement"], "required": True},
                            {"label": "Key Achievements", "code": "key_achievements", "field_type": MT},
                            {"label": "Challenges", "code": "challenges", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": MT},
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
                            {"label": "Overall Partnership Health", "code": "partnership_health", "field_type": DD, "options": ["Strong", "Good", "Moderate", "Concerning"]},
                            {"label": "Strategic Recommendations", "code": "strategic_recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "K4",
        "title": "Memorandum of Understanding Tracking Report",
        "description": "Report tracking MoUs, their status and renewal dates.",
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
                "name": "MoUs",
                "code": "mous",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "MoUs",
                        "code": "mous",
                        "fields": [
                            {"label": "Partner Organization", "code": "partner_org", "field_type": T, "required": True},
                            {"label": "MoU Title", "code": "mou_title", "field_type": T, "required": True},
                            {"label": "Signing Date", "code": "signing_date", "field_type": DT, "required": True},
                            {"label": "Expiry Date", "code": "expiry_date", "field_type": DT, "required": True},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Active", "Expired", "Under Renewal", "Terminated"], "required": True},
                            {"label": "Scope", "code": "scope", "field_type": MT},
                            {"label": "Key Obligations", "code": "key_obligations", "field_type": MT},
                            {"label": "Days Until Expiry", "code": "days_until_expiry", "field_type": INT, "is_calculated": True, "formula": "expiry_date - today"},
                            {"label": "MoU Document", "code": "mou_document", "field_type": DOC},
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
                            {"label": "Total MoUs", "code": "total_mous", "field_type": INT, "is_calculated": True, "formula": "count(mous)"},
                            {"label": "Active MoUs", "code": "active_mous", "field_type": INT},
                            {"label": "Expiring Soon", "code": "expiring_soon", "field_type": INT},
                            {"label": "Action Required", "code": "action_required", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "K5",
        "title": "Stakeholder Engagement Report",
        "description": "Report on stakeholder engagement activities and outcomes.",
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
                "name": "Engagement Activities",
                "code": "engagement-activities",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Engagement Activities",
                        "code": "engagement-activities",
                        "fields": [
                            {"label": "Stakeholder", "code": "stakeholder", "field_type": T, "required": True},
                            {"label": "Activity Type", "code": "activity_type", "field_type": DD, "options": ["Meeting", "Workshop", "Consultation", "Site Visit", "Report", "Communication", "Other"], "required": True},
                            {"label": "Date", "code": "date", "field_type": DT, "required": True},
                            {"label": "Purpose", "code": "purpose", "field_type": MT},
                            {"label": "Outcome", "code": "outcome", "field_type": MT},
                            {"label": "Follow-up Actions", "code": "followup_actions", "field_type": MT},
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
                            {"label": "Total Engagements", "code": "total_engagements", "field_type": INT, "is_calculated": True, "formula": "count(activities)"},
                            {"label": "Stakeholder Feedback", "code": "stakeholder_feedback", "field_type": MT},
                            {"label": "Relationship Status", "code": "relationship_status", "field_type": DD, "options": ["Improving", "Stable", "Declining"]},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "K6",
        "title": "Corporate Partnership Report",
        "description": "Report on corporate partnerships, CSR engagements and private sector collaboration.",
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
                "name": "Corporate Partners",
                "code": "corporate-partners",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Corporate Partners",
                        "code": "corporate-partners",
                        "fields": [
                            {"label": "Company Name", "code": "company_name", "field_type": T, "required": True},
                            {"label": "Industry", "code": "industry", "field_type": T},
                            {"label": "Contact Person", "code": "contact_person", "field_type": T},
                            {"label": "Partnership Type", "code": "partnership_type", "field_type": DD, "options": ["CSR", "Sponsorship", "Pro Bono", "Cause Marketing", "Employee Volunteering", "Other"], "required": True},
                            {"label": "Value/Contribution", "code": "value_contribution", "field_type": DEC},
                            {"label": "Start Date", "code": "start_date", "field_type": DT},
                            {"label": "End Date", "code": "end_date", "field_type": DT},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Active", "Completed", "Expired", "Pending"]},
                            {"label": "Key Deliverables", "code": "key_deliverables", "field_type": MT},
                            {"label": "Impact", "code": "impact", "field_type": MT},
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
                            {"label": "Total Corporate Partners", "code": "total_partners", "field_type": INT, "is_calculated": True, "formula": "count(corporate_partners)"},
                            {"label": "Total Value", "code": "total_value", "field_type": DEC, "is_calculated": True, "formula": "sum(value_contribution)"},
                            {"label": "Active Partnerships", "code": "active_partnerships", "field_type": INT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
]
