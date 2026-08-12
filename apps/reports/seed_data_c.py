"""Seed data for Category C — Program Management templates."""

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
SIG = "SIGNATURE"
USR = "USER_SELECTOR"

CATEGORY_C_TEMPLATES: list[dict] = [
    {
        "code": "C1",
        "title": "Annual Program Plan",
        "description": "Comprehensive annual plan for program activities, goals and resource allocation.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Program Overview",
                "code": "program-overview",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Program Manager", "code": "program_manager", "field_type": T, "required": True},
                            {"label": "Reporting Year", "code": "reporting_year", "field_type": T, "required": True},
                            {"label": "Start Date", "code": "start_date", "field_type": DT, "required": True},
                            {"label": "End Date", "code": "end_date", "field_type": DT, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Goals and Objectives",
                "code": "goals-objectives",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Goal",
                        "code": "goal",
                        "fields": [
                            {"label": "Goal", "code": "goal", "field_type": T, "required": True},
                            {"label": "Objective", "code": "objective", "field_type": MT, "required": True},
                            {"label": "Key Results", "code": "key_results", "field_type": MT},
                            {"label": "Target Beneficiaries", "code": "target_beneficiaries", "field_type": INT},
                            {"label": "Timeline", "code": "timeline", "field_type": MT},
                            {"label": "Responsible Person", "code": "responsible_person", "field_type": T},
                            {"label": "Budget Estimate", "code": "budget_estimate", "field_type": DEC},
                        ],
                    }
                ],
            },
            {
                "name": "Activities",
                "code": "activities",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Activity",
                        "code": "activity",
                        "fields": [
                            {"label": "Activity Description", "code": "activity_description", "field_type": MT, "required": True},
                            {"label": "Quarter", "code": "quarter", "field_type": DD, "options": ["Q1", "Q2", "Q3", "Q4"], "required": True},
                            {"label": "Planned Start Date", "code": "planned_start", "field_type": DT},
                            {"label": "Planned End Date", "code": "planned_end", "field_type": DT},
                            {"label": "Expected Output", "code": "expected_output", "field_type": MT},
                            {"label": "Responsible Person", "code": "responsible_person", "field_type": T},
                            {"label": "Required Resources", "code": "required_resources", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Budget",
                "code": "budget",
                "groups": [
                    {
                        "name": "Budget",
                        "code": "budget",
                        "fields": [
                            {"label": "Total Budget", "code": "total_budget", "field_type": DEC, "required": True},
                            {"label": "Funding Sources", "code": "funding_sources", "field_type": MT},
                            {"label": "Budget Notes", "code": "budget_notes", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "C2",
        "title": "Quarterly Program Implementation Report",
        "description": "Quarterly report on program implementation progress and challenges.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Program Info",
                "code": "program-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Quarter", "code": "quarter", "field_type": DD, "options": ["Q1", "Q2", "Q3", "Q4"], "required": True},
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Report Date", "code": "report_date", "field_type": DT, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Progress Against Plan",
                "code": "progress-against-plan",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Activity",
                        "code": "activity",
                        "fields": [
                            {"label": "Planned Activity", "code": "planned_activity", "field_type": T, "required": True},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Completed", "On Track", "Delayed", "Not Started", "Cancelled"], "required": True},
                            {"label": "Percentage Complete", "code": "pct_complete", "field_type": PCT},
                            {"label": "Actual Output", "code": "actual_output", "field_type": MT},
                            {"label": "Variance", "code": "variance", "field_type": MT},
                            {"label": "Reason for Variance", "code": "variance_reason", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Challenges and Risks",
                "code": "challenges-risks",
                "groups": [
                    {
                        "name": "Challenges",
                        "code": "challenges",
                        "fields": [
                            {"label": "Key Challenges", "code": "key_challenges", "field_type": RT, "required": True},
                            {"label": "Risk Description", "code": "risk_description", "field_type": MT},
                            {"label": "Mitigation Actions", "code": "mitigation_actions", "field_type": MT},
                            {"label": "Support Required", "code": "support_required", "field_type": RT},
                        ],
                    }
                ],
            },
            {
                "name": "Next Quarter",
                "code": "next-quarter",
                "groups": [
                    {
                        "name": "Next Quarter",
                        "code": "next_quarter",
                        "fields": [
                            {"label": "Priority Activities", "code": "priority_activities", "field_type": MT, "required": True},
                            {"label": "Resource Needs", "code": "resource_needs", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "C3",
        "title": "Monthly Program Progress Report",
        "description": "Monthly report on program progress and key metrics.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Report Details",
                "code": "report-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Month", "code": "month", "field_type": DT, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Monthly Activities",
                "code": "monthly-activities",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Activity",
                        "code": "activity",
                        "fields": [
                            {"label": "Activity", "code": "activity", "field_type": T, "required": True},
                            {"label": "Target", "code": "target", "field_type": INT},
                            {"label": "Achieved", "code": "achieved", "field_type": INT},
                            {"label": "Achievement Rate", "code": "achievement_rate", "field_type": PCT, "is_calculated": True, "formula": "achieved / target * 100"},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["On Track", "Behind", "Ahead"]},
                            {"label": "Notes", "code": "notes", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Key Metrics",
                "code": "key-metrics",
                "groups": [
                    {
                        "name": "Metrics",
                        "code": "metrics",
                        "fields": [
                            {"label": "Beneficiaries Reached", "code": "beneficiaries_reached", "field_type": INT},
                            {"label": "Activities Completed", "code": "activities_completed", "field_type": INT},
                            {"label": "Budget Spent", "code": "budget_spent", "field_type": DEC},
                            {"label": "Overall Status", "code": "overall_status", "field_type": DD, "options": ["Green", "Yellow", "Red"]},
                            {"label": "Key Achievements", "code": "key_achievements", "field_type": MT},
                            {"label": "Challenges", "code": "challenges", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "C4",
        "title": "Weekly Activity Report",
        "description": "Weekly report on program activities and deliverables.",
        "reporting_frequency": "WEEKLY",
        "sections": [
            {
                "name": "Week Details",
                "code": "week-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Week Number", "code": "week_number", "field_type": INT, "required": True},
                            {"label": "Week Start Date", "code": "week_start", "field_type": DT, "required": True},
                            {"label": "Week End Date", "code": "week_end", "field_type": DT, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Activities This Week",
                "code": "activities-this-week",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Activity",
                        "code": "activity",
                        "fields": [
                            {"label": "Activity", "code": "activity", "field_type": T, "required": True},
                            {"label": "Description", "code": "description", "field_type": MT},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Completed", "In Progress", "Pending", "Cancelled"]},
                            {"label": "Outcome", "code": "outcome", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Issues and Next Week",
                "code": "issues-next-week",
                "groups": [
                    {
                        "name": "Issues",
                        "code": "issues",
                        "fields": [
                            {"label": "Issues Encountered", "code": "issues_encountered", "field_type": MT},
                            {"label": "Action Taken", "code": "action_taken", "field_type": MT},
                            {"label": "Planned Activities Next Week", "code": "next_week_plan", "field_type": MT, "required": True},
                            {"label": "Support Required", "code": "support_required", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "C5",
        "title": "Activity Completion Report",
        "description": "Report on completion of specific program activities.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Activity Details",
                "code": "activity-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Activity Name", "code": "activity_name", "field_type": T, "required": True},
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Planned Date", "code": "planned_date", "field_type": DT, "required": True},
                            {"label": "Actual Date", "code": "actual_date", "field_type": DT, "required": True},
                            {"label": "Location", "code": "location", "field_type": T},
                            {"label": "Activity Manager", "code": "activity_manager", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Completion Details",
                "code": "completion-details",
                "groups": [
                    {
                        "name": "Completion",
                        "code": "completion",
                        "fields": [
                            {"label": "Completion Status", "code": "completion_status", "field_type": DD, "options": ["Fully Completed", "Partially Completed", "Not Completed"], "required": True},
                            {"label": "Objectives Met", "code": "objectives_met", "field_type": MT},
                            {"label": "Outputs Produced", "code": "outputs_produced", "field_type": MT},
                            {"label": "Participants", "code": "participants", "field_type": INT},
                            {"label": "Budget Spent", "code": "budget_spent", "field_type": DEC},
                        ],
                    }
                ],
            },
            {
                "name": "Evidence",
                "code": "evidence",
                "groups": [
                    {
                        "name": "Evidence",
                        "code": "evidence",
                        "fields": [
                            {"label": "Photos", "code": "photos", "field_type": IMG, "is_repeatable": True},
                            {"label": "Documents", "code": "documents", "field_type": DOC, "is_repeatable": True},
                            {"label": "Lessons Learned", "code": "lessons_learned", "field_type": RT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                            {"label": "Signed By", "code": "signed_by", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "C6",
        "title": "Project Status Report",
        "description": "Current status report for a specific project within a program.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Project Info",
                "code": "project-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Project Name", "code": "project_name", "field_type": T, "required": True},
                            {"label": "Project Manager", "code": "project_manager", "field_type": T, "required": True},
                            {"label": "Reporting Date", "code": "reporting_date", "field_type": DT, "required": True},
                            {"label": "Overall Status", "code": "overall_status", "field_type": DD, "options": ["Green", "Yellow", "Red"], "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Progress",
                "code": "progress",
                "groups": [
                    {
                        "name": "Progress",
                        "code": "progress",
                        "fields": [
                            {"label": "Summary of Progress", "code": "progress_summary", "field_type": RT, "required": True},
                            {"label": "Planned Activities", "code": "planned_activities", "field_type": MT},
                            {"label": "Completed Activities", "code": "completed_activities", "field_type": MT},
                            {"label": "Overall Completion", "code": "overall_completion", "field_type": PCT},
                        ],
                    }
                ],
            },
            {
                "name": "Budget",
                "code": "budget",
                "groups": [
                    {
                        "name": "Budget",
                        "code": "budget",
                        "fields": [
                            {"label": "Total Budget", "code": "total_budget", "field_type": DEC},
                            {"label": "Expenditure to Date", "code": "expenditure_to_date", "field_type": DEC},
                            {"label": "Variance", "code": "variance", "field_type": DEC, "is_calculated": True, "formula": "total_budget - expenditure_to_date"},
                            {"label": "Budget Status", "code": "budget_status", "field_type": DD, "options": ["Under Budget", "On Budget", "Over Budget"]},
                        ],
                    }
                ],
            },
            {
                "name": "Risks and Issues",
                "code": "risks-issues",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Risk",
                        "code": "risk",
                        "fields": [
                            {"label": "Description", "code": "description", "field_type": MT, "required": True},
                            {"label": "Type", "code": "type", "field_type": DD, "options": ["Risk", "Issue"]},
                            {"label": "Impact", "code": "impact", "field_type": DD, "options": ["High", "Medium", "Low"]},
                            {"label": "Mitigation", "code": "mitigation", "field_type": MT},
                            {"label": "Owner", "code": "owner", "field_type": T},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "C7",
        "title": "Program Outcome Report",
        "description": "Report on program outcomes and results achieved.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Program Info",
                "code": "program-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Outcomes",
                "code": "outcomes",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Outcome",
                        "code": "outcome",
                        "fields": [
                            {"label": "Outcome Statement", "code": "outcome_statement", "field_type": T, "required": True},
                            {"label": "Indicator", "code": "indicator", "field_type": T, "required": True},
                            {"label": "Baseline", "code": "baseline", "field_type": DEC},
                            {"label": "Target", "code": "target", "field_type": DEC},
                            {"label": "Actual", "code": "actual", "field_type": DEC},
                            {"label": "Achievement", "code": "achievement", "field_type": PCT, "is_calculated": True, "formula": "actual / target * 100"},
                            {"label": "Evidence", "code": "evidence", "field_type": DOC},
                            {"label": "Analysis", "code": "analysis", "field_type": RT},
                        ],
                    }
                ],
            },
            {
                "name": "Overall Assessment",
                "code": "overall-assessment",
                "groups": [
                    {
                        "name": "Assessment",
                        "code": "assessment",
                        "fields": [
                            {"label": "Overall Outcome Rating", "code": "overall_rating", "field_type": DD, "options": ["Exceeded", "Met", "Partially Met", "Not Met"]},
                            {"label": "Key Successes", "code": "key_successes", "field_type": RT},
                            {"label": "Challenges", "code": "challenges", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "C8",
        "title": "Program Impact Report",
        "description": "Report on the long-term impact of program interventions.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Program Info",
                "code": "program-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Impact Assessment Method", "code": "assessment_method", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Impact Areas",
                "code": "impact-areas",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Impact",
                        "code": "impact",
                        "fields": [
                            {"label": "Impact Area", "code": "impact_area", "field_type": T, "required": True},
                            {"label": "Description of Change", "code": "change_description", "field_type": RT, "required": True},
                            {"label": "Beneficiaries Affected", "code": "beneficiaries_affected", "field_type": INT},
                            {"label": "Significance", "code": "significance", "field_type": DD, "options": ["High", "Medium", "Low"]},
                            {"label": "Sustainability", "code": "sustainability", "field_type": DD, "options": ["Highly Sustainable", "Sustainable", "Partially Sustainable", "Not Sustainable"]},
                            {"label": "Evidence", "code": "evidence", "field_type": DOC, "is_repeatable": True},
                        ],
                    }
                ],
            },
            {
                "name": "Unintended Outcomes",
                "code": "unintended-outcomes",
                "groups": [
                    {
                        "name": "Unintended",
                        "code": "unintended",
                        "fields": [
                            {"label": "Positive Unintended Outcomes", "code": "positive_unintended", "field_type": MT},
                            {"label": "Negative Unintended Outcomes", "code": "negative_unintended", "field_type": MT},
                            {"label": "Lessons Learned", "code": "lessons_learned", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "C9",
        "title": "Project Closure Report",
        "description": "Report for formally closing a completed project.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Project Info",
                "code": "project-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Project Name", "code": "project_name", "field_type": T, "required": True},
                            {"label": "Project Manager", "code": "project_manager", "field_type": T, "required": True},
                            {"label": "Original Start Date", "code": "original_start", "field_type": DT},
                            {"label": "Original End Date", "code": "original_end", "field_type": DT},
                            {"label": "Actual End Date", "code": "actual_end", "field_type": DT, "required": True},
                            {"label": "Closure Date", "code": "closure_date", "field_type": DT, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Deliverables",
                "code": "deliverables",
                "groups": [
                    {
                        "name": "Deliverables",
                        "code": "deliverables",
                        "fields": [
                            {"label": "Planned Deliverables", "code": "planned_deliverables", "field_type": MT},
                            {"label": "Actual Deliverables", "code": "actual_deliverables", "field_type": MT},
                            {"label": "Completion Rate", "code": "completion_rate", "field_type": PCT, "is_calculated": True, "formula": "actual / planned * 100"},
                        ],
                    }
                ],
            },
            {
                "name": "Budget Summary",
                "code": "budget-summary",
                "groups": [
                    {
                        "name": "Budget",
                        "code": "budget",
                        "fields": [
                            {"label": "Original Budget", "code": "original_budget", "field_type": DEC},
                            {"label": "Revised Budget", "code": "revised_budget", "field_type": DEC},
                            {"label": "Actual Expenditure", "code": "actual_expenditure", "field_type": DEC},
                            {"label": "Variance", "code": "variance", "field_type": DEC, "is_calculated": True, "formula": "revised_budget - actual_expenditure"},
                        ],
                    }
                ],
            },
            {
                "name": "Lessons and Handover",
                "code": "lessons-handover",
                "groups": [
                    {
                        "name": "Lessons",
                        "code": "lessons",
                        "fields": [
                            {"label": "Key Lessons Learned", "code": "lessons_learned", "field_type": RT, "required": True},
                            {"label": "Recommendations for Future", "code": "recommendations", "field_type": RT},
                            {"label": "Handover Notes", "code": "handover_notes", "field_type": MT},
                            {"label": "Outstanding Actions", "code": "outstanding_actions", "field_type": MT},
                            {"label": "Sign-off By", "code": "signoff_by", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "C10",
        "title": "Beneficiary Statistics Report",
        "description": "Statistical report on beneficiaries reached by programs.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Report Date", "code": "report_date", "field_type": DT, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Beneficiary Demographics",
                "code": "beneficiary-demographics",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Demographic",
                        "code": "demographic",
                        "fields": [
                            {"label": "Program", "code": "program", "field_type": T, "required": True},
                            {"label": "Category", "code": "category", "field_type": DD, "options": ["Youth", "Women", "Men", "Children", "Elderly", "PWDs", "Other"]},
                            {"label": "Total Beneficiaries", "code": "total_beneficiaries", "field_type": INT, "required": True},
                            {"label": "Male", "code": "male", "field_type": INT},
                            {"label": "Female", "code": "female", "field_type": INT},
                            {"label": "Locations", "code": "locations", "field_type": MT},
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
                            {"label": "Total Unique Beneficiaries", "code": "total_unique", "field_type": INT, "is_calculated": True, "formula": "sum(total_beneficiaries)"},
                            {"label": "Summary Notes", "code": "summary_notes", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "C11",
        "title": "Community Engagement Report",
        "description": "Report on community engagement activities and outcomes.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Report Details",
                "code": "report-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Reporting Month", "code": "reporting_month", "field_type": DT, "required": True},
                            {"label": "Community", "code": "community", "field_type": T, "required": True},
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
                        "name": "Activity",
                        "code": "activity",
                        "fields": [
                            {"label": "Activity Type", "code": "activity_type", "field_type": DD, "options": ["Meeting", "Workshop", "Forum", "Survey", "Outreach", "Consultation", "Other"], "required": True},
                            {"label": "Activity Description", "code": "activity_description", "field_type": MT, "required": True},
                            {"label": "Date", "code": "date", "field_type": DT, "required": True},
                            {"label": "Participants", "code": "participants", "field_type": INT},
                            {"label": "Key Issues Raised", "code": "issues_raised", "field_type": MT},
                            {"label": "Outcomes", "code": "outcomes", "field_type": MT},
                            {"label": "Photos", "code": "photos", "field_type": IMG, "is_repeatable": True},
                        ],
                    }
                ],
            },
            {
                "name": "Feedback Summary",
                "code": "feedback-summary",
                "groups": [
                    {
                        "name": "Feedback",
                        "code": "feedback",
                        "fields": [
                            {"label": "Positive Feedback", "code": "positive_feedback", "field_type": MT},
                            {"label": "Concerns Raised", "code": "concerns_raised", "field_type": MT},
                            {"label": "Follow-up Actions", "code": "followup_actions", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "C12",
        "title": "Lessons Learned Report",
        "description": "Report capturing lessons learned from program implementation.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program or Project Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Report Date", "code": "report_date", "field_type": DT, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Lessons Learned",
                "code": "lessons-learned",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Lesson",
                        "code": "lesson",
                        "fields": [
                            {"label": "Category", "code": "category", "field_type": DD, "options": ["Planning", "Implementation", "Monitoring", "Staffing", "Budget", "Partnerships", "Community", "Other"], "required": True},
                            {"label": "Description", "code": "description", "field_type": MT, "required": True},
                            {"label": "Impact", "code": "impact", "field_type": DD, "options": ["High", "Medium", "Low"]},
                            {"label": "Recommendation", "code": "recommendation", "field_type": RT, "required": True},
                            {"label": "Applicability", "code": "applicability", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Best Practices",
                "code": "best-practices",
                "groups": [
                    {
                        "name": "Best Practices",
                        "code": "best_practices",
                        "fields": [
                            {"label": "Best Practices Identified", "code": "best_practices", "field_type": RT, "required": True},
                            {"label": "Replication Potential", "code": "replication_potential", "field_type": MT},
                            {"label": "Approval", "code": "approval", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
]
