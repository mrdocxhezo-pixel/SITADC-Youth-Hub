"""Complete seed data for all 143 report templates (Categories A-P).

Each template defines its sections, field groups, and dynamic fields exactly
as specified in the Report Categories and Unique Templates document.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Field type shorthand aliases for readability
# ---------------------------------------------------------------------------
T = "TEXT"  # Short text
MT = "MULTILINE_TEXT"  # Textarea
RT = "RICH_TEXT"  # Rich text editor
INT = "INTEGER"
DEC = "DECIMAL"
CUR = "CURRENCY"
PCT = "PERCENTAGE"
DT = "DATE"
TM = "TIME"
DTM = "DATETIME"
DD = "DROPDOWN"  # Single select
MS = "MULTI_SELECT"  # Multi select
RD = "RADIO"  # Radio buttons
CB = "CHECKBOX"  # Checkbox / boolean
IMG = "IMAGE"
VID = "VIDEO"
DOC = "DOCUMENT"
SIG = "SIGNATURE"
TBL = "TABLE_GRID"
RG = "REPEATING_GROUP"
USR = "USER_SELECTOR"
PGM = "PROGRAM_SELECTOR"

# ---------------------------------------------------------------------------
# Template definitions — one dict per template
# ---------------------------------------------------------------------------

REPORT_TEMPLATES: list[dict] = [
    # =========================================================================
    # CATEGORY A — ORGANIZATIONAL GOVERNANCE
    # =========================================================================
    {
        "code": "A1",
        "title": "Annual Organizational Report",
        "description": "Comprehensive annual report covering all aspects of organizational performance.",
        "reporting_frequency": "ANNUAL",
        "confidentiality": "INTERNAL",
        "sections": [
            {
                "name": "Executive Summary",
                "code": "executive-summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {
                                "label": "Executive Summary",
                                "code": "executive_summary",
                                "field_type": RT,
                                "required": True,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Leadership Messages",
                "code": "leadership-messages",
                "groups": [
                    {
                        "name": "Board Chairperson",
                        "code": "board-chair",
                        "fields": [
                            {
                                "label": "Message from the Board Chairperson",
                                "code": "chair_message",
                                "field_type": RT,
                                "required": True,
                            },
                        ],
                    },
                    {
                        "name": "Executive Director",
                        "code": "exec-director",
                        "fields": [
                            {
                                "label": "Message from the Executive Director",
                                "code": "ed_message",
                                "field_type": RT,
                                "required": True,
                            },
                        ],
                    },
                ],
            },
            {
                "name": "Organization Overview",
                "code": "org-overview",
                "groups": [
                    {
                        "name": "Overview",
                        "code": "overview",
                        "fields": [
                            {
                                "label": "Organization Overview",
                                "code": "org_overview",
                                "field_type": RT,
                                "required": True,
                            },
                            {"label": "Vision", "code": "vision", "field_type": MT},
                            {"label": "Mission", "code": "mission", "field_type": MT},
                            {"label": "Values", "code": "values", "field_type": MT},
                            {
                                "label": "Annual Strategic Priorities",
                                "code": "strategic_priorities",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Key Achievements",
                "code": "achievements",
                "groups": [
                    {
                        "name": "Achievements",
                        "code": "achievements",
                        "fields": [
                            {
                                "label": "Key Achievements",
                                "code": "key_achievements",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Programs Implemented",
                                "code": "programs_implemented",
                                "field_type": RT,
                            },
                            {
                                "label": "Geographic Coverage",
                                "code": "geographic_coverage",
                                "field_type": MT,
                            },
                            {
                                "label": "Beneficiary Statistics",
                                "code": "beneficiary_statistics",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Governance and Membership",
                "code": "governance-membership",
                "groups": [
                    {
                        "name": "Updates",
                        "code": "updates",
                        "fields": [
                            {
                                "label": "Leadership and Governance Update",
                                "code": "leadership_update",
                                "field_type": RT,
                            },
                            {
                                "label": "Membership and Volunteer Update",
                                "code": "membership_update",
                                "field_type": RT,
                            },
                            {
                                "label": "Partnerships and Stakeholder Engagement",
                                "code": "partnerships",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Financial Summary",
                "code": "financial-summary",
                "groups": [
                    {
                        "name": "Finance",
                        "code": "finance",
                        "fields": [
                            {
                                "label": "Financial Summary",
                                "code": "financial_summary",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Resource Mobilization Performance",
                                "code": "resource_mobilization",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "MEAL and Learning",
                "code": "meal-learning",
                "groups": [
                    {
                        "name": "MEAL",
                        "code": "meal",
                        "fields": [
                            {
                                "label": "Monitoring and Evaluation Findings",
                                "code": "me_findings",
                                "field_type": RT,
                            },
                            {
                                "label": "Challenges",
                                "code": "challenges",
                                "field_type": RT,
                            },
                            {
                                "label": "Lessons Learned",
                                "code": "lessons_learned",
                                "field_type": RT,
                            },
                            {
                                "label": "Success Stories",
                                "code": "success_stories",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Forward Look",
                "code": "forward-look",
                "groups": [
                    {
                        "name": "Future",
                        "code": "future",
                        "fields": [
                            {
                                "label": "Risk Summary",
                                "code": "risk_summary",
                                "field_type": RT,
                            },
                            {
                                "label": "Sustainability Initiatives",
                                "code": "sustainability",
                                "field_type": RT,
                            },
                            {
                                "label": "Priorities for the Next Year",
                                "code": "next_year_priorities",
                                "field_type": RT,
                            },
                            {
                                "label": "Recommendations",
                                "code": "recommendations",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Supporting Evidence",
                "code": "evidence",
                "groups": [
                    {
                        "name": "Evidence",
                        "code": "evidence",
                        "fields": [
                            {
                                "label": "Supporting Evidence",
                                "code": "evidence_files",
                                "field_type": DOC,
                                "is_repeatable": True,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Approval and Sign-off",
                "code": "approval",
                "groups": [
                    {
                        "name": "Signatures",
                        "code": "signatures",
                        "fields": [
                            {
                                "label": "Prepared By",
                                "code": "prepared_by",
                                "field_type": USR,
                            },
                            {
                                "label": "Reviewed By",
                                "code": "reviewed_by",
                                "field_type": USR,
                            },
                            {
                                "label": "Approved By",
                                "code": "approved_by",
                                "field_type": USR,
                            },
                            {
                                "label": "Approval Date",
                                "code": "approval_date",
                                "field_type": DT,
                            },
                            {
                                "label": "Signature",
                                "code": "signature",
                                "field_type": SIG,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "A2",
        "title": "Governance Performance Report",
        "description": "Report on board composition, meetings, compliance and governance scorecard.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Board Composition",
                "code": "board-composition",
                "groups": [
                    {
                        "name": "Composition",
                        "code": "composition",
                        "fields": [
                            {
                                "label": "Governance Period",
                                "code": "governance_period",
                                "field_type": DT,
                            },
                            {
                                "label": "Board Composition",
                                "code": "board_composition",
                                "field_type": MT,
                            },
                            {
                                "label": "Board Diversity",
                                "code": "board_diversity",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Board Meetings",
                "code": "board-meetings",
                "groups": [
                    {
                        "name": "Meetings",
                        "code": "meetings",
                        "fields": [
                            {
                                "label": "Board Meetings Planned",
                                "code": "meetings_planned",
                                "field_type": INT,
                                "required": True,
                            },
                            {
                                "label": "Board Meetings Held",
                                "code": "meetings_held",
                                "field_type": INT,
                                "required": True,
                            },
                            {
                                "label": "Attendance Rate",
                                "code": "attendance_rate",
                                "field_type": PCT,
                                "is_calculated": True,
                                "formula": "meetings_held / meetings_planned * 100",
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Governance Performance",
                "code": "governance-performance",
                "groups": [
                    {
                        "name": "Performance",
                        "code": "performance",
                        "fields": [
                            {
                                "label": "Resolutions Passed",
                                "code": "resolutions_passed",
                                "field_type": INT,
                            },
                            {
                                "label": "Resolutions Implemented",
                                "code": "resolutions_implemented",
                                "field_type": INT,
                            },
                            {
                                "label": "Policy Reviews Completed",
                                "code": "policy_reviews",
                                "field_type": INT,
                            },
                            {
                                "label": "Compliance Status",
                                "code": "compliance_status",
                                "field_type": DD,
                                "options": [
                                    "Compliant",
                                    "Partially Compliant",
                                    "Non-Compliant",
                                ],
                            },
                            {
                                "label": "Board Committee Performance",
                                "code": "committee_performance",
                                "field_type": RT,
                            },
                            {
                                "label": "Governance Scorecard",
                                "code": "governance_scorecard",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Risk and Recommendations",
                "code": "risk-recommendations",
                "groups": [
                    {
                        "name": "Risk",
                        "code": "risk",
                        "fields": [
                            {
                                "label": "Conflict of Interest Declarations",
                                "code": "coi_declarations",
                                "field_type": INT,
                            },
                            {
                                "label": "Governance Risks",
                                "code": "governance_risks",
                                "field_type": RT,
                            },
                            {
                                "label": "Corrective Actions",
                                "code": "corrective_actions",
                                "field_type": RT,
                            },
                            {
                                "label": "Recommendations",
                                "code": "recommendations",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "A3",
        "title": "Board Meeting Minutes",
        "description": "Minutes for board meetings with agenda items, resolutions and action points.",
        "reporting_frequency": "ONE_OFF",
        "is_repeatable_sections": True,
        "sections": [
            {
                "name": "Meeting Details",
                "code": "meeting-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {
                                "label": "Meeting Number",
                                "code": "meeting_number",
                                "field_type": INT,
                                "required": True,
                            },
                            {
                                "label": "Meeting Date",
                                "code": "meeting_date",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Start Time",
                                "code": "start_time",
                                "field_type": TM,
                            },
                            {"label": "End Time", "code": "end_time", "field_type": TM},
                            {
                                "label": "Venue/Meeting Link",
                                "code": "venue",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Meeting Type",
                                "code": "meeting_type",
                                "field_type": DD,
                                "options": [
                                    "Regular",
                                    "Special",
                                    "Annual",
                                    "Emergency",
                                ],
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Attendance",
                "code": "attendance",
                "groups": [
                    {
                        "name": "Attendance",
                        "code": "attendance",
                        "fields": [
                            {
                                "label": "Chairperson",
                                "code": "chairperson",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Secretary",
                                "code": "secretary",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Members Present",
                                "code": "members_present",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Members Absent",
                                "code": "members_absent",
                                "field_type": MT,
                            },
                            {
                                "label": "Apologies",
                                "code": "apologies",
                                "field_type": MT,
                            },
                            {
                                "label": "Quorum Confirmation",
                                "code": "quorum_confirmed",
                                "field_type": CB,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Agenda Items",
                "code": "agenda-items",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Agenda Item",
                        "code": "agenda_item",
                        "fields": [
                            {
                                "label": "Agenda Item",
                                "code": "agenda_item",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Declaration of Interests",
                                "code": "declarations",
                                "field_type": MT,
                            },
                            {
                                "label": "Previous Minutes Confirmation",
                                "code": "prev_minutes",
                                "field_type": CB,
                            },
                            {
                                "label": "Matters Arising",
                                "code": "matters_arising",
                                "field_type": MT,
                            },
                            {
                                "label": "Discussion",
                                "code": "discussion",
                                "field_type": RT,
                            },
                            {
                                "label": "Decisions Made",
                                "code": "decisions",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Resolutions",
                "code": "resolutions",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Resolution",
                        "code": "resolution",
                        "fields": [
                            {
                                "label": "Resolution",
                                "code": "resolution",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Responsible Person",
                                "code": "responsible_person",
                                "field_type": T,
                            },
                            {
                                "label": "Action Deadline",
                                "code": "action_deadline",
                                "field_type": DT,
                            },
                            {
                                "label": "Action Status",
                                "code": "action_status",
                                "field_type": DD,
                                "options": [
                                    "Pending",
                                    "In Progress",
                                    "Completed",
                                    "Overdue",
                                ],
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Closing",
                "code": "closing",
                "groups": [
                    {
                        "name": "Closing",
                        "code": "closing",
                        "fields": [
                            {
                                "label": "Next Meeting",
                                "code": "next_meeting",
                                "field_type": DT,
                            },
                            {
                                "label": "Closing Remarks",
                                "code": "closing_remarks",
                                "field_type": MT,
                            },
                            {
                                "label": "Chairperson Signature",
                                "code": "chair_signature",
                                "field_type": SIG,
                            },
                            {
                                "label": "Secretary Signature",
                                "code": "secretary_signature",
                                "field_type": SIG,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "A4",
        "title": "Executive Committee Minutes",
        "description": "Minutes for executive committee meetings.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Meeting Details",
                "code": "meeting-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {
                                "label": "Meeting Details",
                                "code": "meeting_details",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Attendance",
                                "code": "attendance",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Confirmation of Quorum",
                                "code": "quorum",
                                "field_type": CB,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Updates",
                "code": "updates",
                "groups": [
                    {
                        "name": "Updates",
                        "code": "updates",
                        "fields": [
                            {
                                "label": "Previous Action Review",
                                "code": "prev_action_review",
                                "field_type": RT,
                            },
                            {
                                "label": "Directorate Updates",
                                "code": "directorate_updates",
                                "field_type": RT,
                            },
                            {
                                "label": "Operational Matters",
                                "code": "operational_matters",
                                "field_type": RT,
                            },
                            {
                                "label": "Program Performance",
                                "code": "program_performance",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Financial and HR Matters",
                "code": "financial-hr",
                "groups": [
                    {
                        "name": "Finance",
                        "code": "finance",
                        "fields": [
                            {
                                "label": "Financial Matters",
                                "code": "financial_matters",
                                "field_type": RT,
                            },
                            {
                                "label": "Human Resource Matters",
                                "code": "hr_matters",
                                "field_type": RT,
                            },
                            {
                                "label": "Risk and Compliance Matters",
                                "code": "risk_compliance",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Decisions and Actions",
                "code": "decisions-actions",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Action Item",
                        "code": "action_item",
                        "fields": [
                            {
                                "label": "Decisions",
                                "code": "decisions",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Action Items",
                                "code": "action_items",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Responsible Officers",
                                "code": "responsible_officers",
                                "field_type": T,
                            },
                            {
                                "label": "Due Dates",
                                "code": "due_dates",
                                "field_type": DT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Closing",
                "code": "closing",
                "groups": [
                    {
                        "name": "Closing",
                        "code": "closing",
                        "fields": [
                            {
                                "label": "Next Meeting",
                                "code": "next_meeting",
                                "field_type": DT,
                            },
                            {
                                "label": "Signatures",
                                "code": "signatures",
                                "field_type": SIG,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "A5",
        "title": "Annual General Meeting Report",
        "description": "Report on the Annual General Meeting proceedings and outcomes.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Meeting Details",
                "code": "meeting-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {
                                "label": "AGM Date and Venue",
                                "code": "agm_date_venue",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Notice Issuance Date",
                                "code": "notice_date",
                                "field_type": DT,
                            },
                            {
                                "label": "Attendance",
                                "code": "attendance",
                                "field_type": MT,
                                "required": True,
                            },
                            {"label": "Quorum", "code": "quorum", "field_type": CB},
                            {"label": "Agenda", "code": "agenda", "field_type": RT},
                        ],
                    }
                ],
            },
            {
                "name": "Reports",
                "code": "reports",
                "groups": [
                    {
                        "name": "Reports",
                        "code": "reports",
                        "fields": [
                            {
                                "label": "Chairperson's Report",
                                "code": "chair_report",
                                "field_type": RT,
                            },
                            {
                                "label": "Executive Director's Report",
                                "code": "ed_report",
                                "field_type": RT,
                            },
                            {
                                "label": "Financial Report",
                                "code": "financial_report",
                                "field_type": RT,
                            },
                            {
                                "label": "Auditor's Report",
                                "code": "auditor_report",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Governance Actions",
                "code": "governance-actions",
                "groups": [
                    {
                        "name": "Actions",
                        "code": "actions",
                        "fields": [
                            {
                                "label": "Elections Conducted",
                                "code": "elections",
                                "field_type": MT,
                            },
                            {
                                "label": "Constitutional Amendments",
                                "code": "amendments",
                                "field_type": MT,
                            },
                            {
                                "label": "Resolutions Adopted",
                                "code": "resolutions",
                                "field_type": MT,
                            },
                            {
                                "label": "Member Questions",
                                "code": "member_questions",
                                "field_type": MT,
                            },
                            {
                                "label": "Voting Results",
                                "code": "voting_results",
                                "field_type": RT,
                            },
                            {
                                "label": "Action Points",
                                "code": "action_points",
                                "field_type": MT,
                            },
                            {
                                "label": "Closing Remarks",
                                "code": "closing_remarks",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "A6",
        "title": "Organizational Performance Dashboard",
        "description": "Dashboard report on organizational KPIs and performance indicators.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Performance Overview",
                "code": "performance-overview",
                "groups": [
                    {
                        "name": "Overview",
                        "code": "overview",
                        "fields": [
                            {
                                "label": "Reporting Period",
                                "code": "reporting_period",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Strategic Objectives",
                                "code": "strategic_objectives",
                                "field_type": RT,
                            },
                            {
                                "label": "Organizational KPIs",
                                "code": "org_kpis",
                                "field_type": RT,
                            },
                            {
                                "label": "Program Performance Summary",
                                "code": "program_summary",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Functional Performance",
                "code": "functional-performance",
                "groups": [
                    {
                        "name": "Functions",
                        "code": "functions",
                        "fields": [
                            {
                                "label": "Financial Performance",
                                "code": "financial_performance",
                                "field_type": RT,
                            },
                            {
                                "label": "Membership Statistics",
                                "code": "membership_stats",
                                "field_type": MT,
                            },
                            {
                                "label": "Volunteer Statistics",
                                "code": "volunteer_stats",
                                "field_type": MT,
                            },
                            {
                                "label": "Partnership Performance",
                                "code": "partnership_performance",
                                "field_type": RT,
                            },
                            {
                                "label": "Governance Indicators",
                                "code": "governance_indicators",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Risk and Trends",
                "code": "risk-trends",
                "groups": [
                    {
                        "name": "Risk",
                        "code": "risk",
                        "fields": [
                            {
                                "label": "Risk Indicators",
                                "code": "risk_indicators",
                                "field_type": RT,
                            },
                            {
                                "label": "Compliance Status",
                                "code": "compliance_status",
                                "field_type": DD,
                                "options": [
                                    "Compliant",
                                    "Partially Compliant",
                                    "Non-Compliant",
                                ],
                            },
                            {
                                "label": "Dashboard Charts",
                                "code": "dashboard_charts",
                                "field_type": IMG,
                                "is_repeatable": True,
                            },
                            {
                                "label": "Performance Trends",
                                "code": "performance_trends",
                                "field_type": RT,
                            },
                            {
                                "label": "Recommendations",
                                "code": "recommendations",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "A7",
        "title": "Leadership Performance Report",
        "description": "Individual leadership performance assessment report.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Leader Details",
                "code": "leader-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {
                                "label": "Leader Details",
                                "code": "leader_details",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Position",
                                "code": "position",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Reporting Period",
                                "code": "reporting_period",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Responsibilities",
                                "code": "responsibilities",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Performance Assessment",
                "code": "performance-assessment",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "KPI",
                        "code": "kpi",
                        "fields": [
                            {
                                "label": "Performance Objectives",
                                "code": "performance_objectives",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Key Performance Indicators",
                                "code": "kpis",
                                "field_type": T,
                            },
                            {"label": "Targets", "code": "targets", "field_type": T},
                            {
                                "label": "Actual Results",
                                "code": "actual_results",
                                "field_type": T,
                            },
                            {
                                "label": "Achievement Percentage",
                                "code": "achievement_pct",
                                "field_type": PCT,
                                "is_calculated": True,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Competencies",
                "code": "competencies",
                "groups": [
                    {
                        "name": "Competencies",
                        "code": "competencies",
                        "fields": [
                            {
                                "label": "Leadership Competencies",
                                "code": "leadership_competencies",
                                "field_type": RT,
                            },
                            {
                                "label": "Team Management",
                                "code": "team_management",
                                "field_type": PCT,
                            },
                            {
                                "label": "Communication",
                                "code": "communication",
                                "field_type": PCT,
                            },
                            {
                                "label": "Accountability",
                                "code": "accountability",
                                "field_type": PCT,
                            },
                            {
                                "label": "Innovation",
                                "code": "innovation",
                                "field_type": PCT,
                            },
                            {
                                "label": "Decision-Making",
                                "code": "decision_making",
                                "field_type": PCT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Review",
                "code": "review",
                "groups": [
                    {
                        "name": "Review",
                        "code": "review",
                        "fields": [
                            {
                                "label": "Challenges",
                                "code": "challenges",
                                "field_type": RT,
                            },
                            {
                                "label": "Support Required",
                                "code": "support_required",
                                "field_type": RT,
                            },
                            {
                                "label": "Supervisor Comments",
                                "code": "supervisor_comments",
                                "field_type": RT,
                            },
                            {
                                "label": "Overall Rating",
                                "code": "overall_rating",
                                "field_type": DD,
                                "options": [
                                    "Exceeds Expectations",
                                    "Meets Expectations",
                                    "Needs Improvement",
                                    "Unsatisfactory",
                                ],
                            },
                            {
                                "label": "Development Plan",
                                "code": "development_plan",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "A8",
        "title": "Policy Compliance Report",
        "description": "Report on organizational policy compliance status.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Policy Details",
                "code": "policy-details",
                "groups": [
                    {
                        "name": "Policy",
                        "code": "policy",
                        "fields": [
                            {
                                "label": "Policy Name",
                                "code": "policy_name",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Policy Owner",
                                "code": "policy_owner",
                                "field_type": T,
                            },
                            {
                                "label": "Policy Version",
                                "code": "policy_version",
                                "field_type": T,
                            },
                            {
                                "label": "Effective Date",
                                "code": "effective_date",
                                "field_type": DT,
                            },
                            {
                                "label": "Review Date",
                                "code": "review_date",
                                "field_type": DT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Compliance Assessment",
                "code": "compliance-assessment",
                "groups": [
                    {
                        "name": "Assessment",
                        "code": "assessment",
                        "fields": [
                            {
                                "label": "Compliance Requirement",
                                "code": "compliance_requirement",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Responsible Unit",
                                "code": "responsible_unit",
                                "field_type": T,
                            },
                            {
                                "label": "Compliance Status",
                                "code": "compliance_status",
                                "field_type": DD,
                                "options": [
                                    "Compliant",
                                    "Partially Compliant",
                                    "Non-Compliant",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Evidence",
                                "code": "evidence",
                                "field_type": DOC,
                            },
                            {
                                "label": "Identified Gap",
                                "code": "identified_gap",
                                "field_type": RT,
                            },
                            {
                                "label": "Risk Rating",
                                "code": "risk_rating",
                                "field_type": DD,
                                "options": ["Low", "Medium", "High", "Critical"],
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Corrective Action",
                "code": "corrective-action",
                "groups": [
                    {
                        "name": "Action",
                        "code": "action",
                        "fields": [
                            {
                                "label": "Corrective Action",
                                "code": "corrective_action",
                                "field_type": RT,
                            },
                            {
                                "label": "Responsible Person",
                                "code": "responsible_person",
                                "field_type": T,
                            },
                            {"label": "Deadline", "code": "deadline", "field_type": DT},
                            {
                                "label": "Follow-up Status",
                                "code": "followup_status",
                                "field_type": DD,
                                "options": ["Pending", "In Progress", "Completed"],
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "A9",
        "title": "Strategic Plan Progress Report",
        "description": "Progress report on strategic plan implementation.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Strategic Progress",
                "code": "strategic-progress",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Objective",
                        "code": "objective",
                        "fields": [
                            {
                                "label": "Strategic Objective",
                                "code": "strategic_objective",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Strategic Outcome",
                                "code": "strategic_outcome",
                                "field_type": T,
                            },
                            {
                                "label": "Key Result Area",
                                "code": "key_result_area",
                                "field_type": T,
                            },
                            {
                                "label": "Indicator",
                                "code": "indicator",
                                "field_type": T,
                            },
                            {
                                "label": "Baseline",
                                "code": "baseline",
                                "field_type": DEC,
                            },
                            {
                                "label": "Annual Target",
                                "code": "annual_target",
                                "field_type": DEC,
                            },
                            {
                                "label": "Period Target",
                                "code": "period_target",
                                "field_type": DEC,
                            },
                            {
                                "label": "Actual Result",
                                "code": "actual_result",
                                "field_type": DEC,
                            },
                            {
                                "label": "Percentage Achieved",
                                "code": "pct_achieved",
                                "field_type": PCT,
                                "is_calculated": True,
                                "formula": "actual_result / period_target * 100",
                            },
                            {
                                "label": "Milestone Status",
                                "code": "milestone_status",
                                "field_type": DD,
                                "options": [
                                    "On Track",
                                    "At Risk",
                                    "Behind",
                                    "Completed",
                                ],
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Activities and Budget",
                "code": "activities-budget",
                "groups": [
                    {
                        "name": "Activities",
                        "code": "activities",
                        "fields": [
                            {
                                "label": "Activities Completed",
                                "code": "activities_completed",
                                "field_type": RT,
                            },
                            {
                                "label": "Budget Planned",
                                "code": "budget_planned",
                                "field_type": CUR,
                            },
                            {
                                "label": "Budget Spent",
                                "code": "budget_spent",
                                "field_type": CUR,
                            },
                            {
                                "label": "Variance",
                                "code": "variance",
                                "field_type": CUR,
                                "is_calculated": True,
                                "formula": "budget_planned - budget_spent",
                            },
                            {
                                "label": "Challenges",
                                "code": "challenges",
                                "field_type": RT,
                            },
                            {
                                "label": "Corrective Actions",
                                "code": "corrective_actions",
                                "field_type": RT,
                            },
                            {
                                "label": "Responsible Unit",
                                "code": "responsible_unit",
                                "field_type": T,
                            },
                            {
                                "label": "Next-period Priorities",
                                "code": "next_period_priorities",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "A10",
        "title": "Risk Management Report",
        "description": "Report on organizational risk identification, assessment and mitigation.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Risk Assessment",
                "code": "risk-assessment",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Risk",
                        "code": "risk",
                        "fields": [
                            {
                                "label": "Risk ID",
                                "code": "risk_id",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Risk Category",
                                "code": "risk_category",
                                "field_type": DD,
                                "options": [
                                    "Strategic",
                                    "Operational",
                                    "Financial",
                                    "Compliance",
                                    "Reputational",
                                    "Human Resource",
                                    "Technology",
                                    "Environmental",
                                ],
                            },
                            {
                                "label": "Risk Description",
                                "code": "risk_description",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Risk Owner",
                                "code": "risk_owner",
                                "field_type": T,
                            },
                            {"label": "Cause", "code": "cause", "field_type": MT},
                            {
                                "label": "Potential Consequence",
                                "code": "consequence",
                                "field_type": MT,
                            },
                            {
                                "label": "Likelihood",
                                "code": "likelihood",
                                "field_type": DD,
                                "options": [
                                    "Rare",
                                    "Unlikely",
                                    "Possible",
                                    "Likely",
                                    "Almost Certain",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Impact",
                                "code": "impact",
                                "field_type": DD,
                                "options": [
                                    "Insignificant",
                                    "Minor",
                                    "Moderate",
                                    "Major",
                                    "Catastrophic",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Inherent Risk Score",
                                "code": "inherent_score",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "likelihood * impact",
                            },
                            {
                                "label": "Existing Controls",
                                "code": "existing_controls",
                                "field_type": MT,
                            },
                            {
                                "label": "Control Effectiveness",
                                "code": "control_effectiveness",
                                "field_type": DD,
                                "options": [
                                    "Effective",
                                    "Partially Effective",
                                    "Ineffective",
                                ],
                            },
                            {
                                "label": "Residual Likelihood",
                                "code": "residual_likelihood",
                                "field_type": DD,
                                "options": [
                                    "Rare",
                                    "Unlikely",
                                    "Possible",
                                    "Likely",
                                    "Almost Certain",
                                ],
                            },
                            {
                                "label": "Residual Impact",
                                "code": "residual_impact",
                                "field_type": DD,
                                "options": [
                                    "Insignificant",
                                    "Minor",
                                    "Moderate",
                                    "Major",
                                    "Catastrophic",
                                ],
                            },
                            {
                                "label": "Residual Risk Score",
                                "code": "residual_score",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "residual_likelihood * residual_impact",
                            },
                            {
                                "label": "Mitigation Action",
                                "code": "mitigation_action",
                                "field_type": RT,
                            },
                            {
                                "label": "Action Owner",
                                "code": "action_owner",
                                "field_type": T,
                            },
                            {"label": "Due Date", "code": "due_date", "field_type": DT},
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Open",
                                    "In Progress",
                                    "Mitigated",
                                    "Closed",
                                ],
                            },
                            {
                                "label": "Escalation Required",
                                "code": "escalation_required",
                                "field_type": CB,
                            },
                            {
                                "label": "Review Date",
                                "code": "review_date",
                                "field_type": DT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
]
