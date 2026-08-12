"""Seed data for Category H — Resource Mobilization templates."""

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

CATEGORY_H_TEMPLATES: list[dict] = [
    {
        "code": "H1",
        "title": "Grant Tracking Report",
        "description": "Report tracking all grants, their status and utilization.",
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
                "name": "Grants",
                "code": "grants",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Grants",
                        "code": "grants",
                        "fields": [
                            {"label": "Grant Name", "code": "grant_name", "field_type": T, "required": True},
                            {"label": "Donor", "code": "donor", "field_type": T, "required": True},
                            {"label": "Grant Amount", "code": "grant_amount", "field_type": DEC, "required": True},
                            {"label": "Start Date", "code": "start_date", "field_type": DT},
                            {"label": "End Date", "code": "end_date", "field_type": DT},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Active", "Completed", "Pending", "Rejected"], "required": True},
                            {"label": "Utilized Amount", "code": "utilized_amount", "field_type": DEC},
                            {"label": "Remaining Balance", "code": "remaining_balance", "field_type": DEC, "is_calculated": True, "formula": "grant_amount - utilized_amount"},
                            {"label": "Utilization Rate", "code": "utilization_rate", "field_type": PCT, "is_calculated": True, "formula": "utilized_amount / grant_amount * 100"},
                            {"label": "Compliance Status", "code": "compliance_status", "field_type": DD, "options": ["Compliant", "Partially Compliant", "Non-Compliant"]},
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
                            {"label": "Total Grants", "code": "total_grants", "field_type": INT, "is_calculated": True, "formula": "count(grants)"},
                            {"label": "Total Grant Value", "code": "total_value", "field_type": DEC, "is_calculated": True, "formula": "sum(grant_amount)"},
                            {"label": "Total Utilized", "code": "total_utilized", "field_type": DEC, "is_calculated": True, "formula": "sum(utilized_amount)"},
                            {"label": "Overall Utilization", "code": "overall_utilization", "field_type": PCT, "is_calculated": True, "formula": "total_utilized / total_value * 100"},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "H2",
        "title": "Proposal Pipeline Report",
        "description": "Report on proposals submitted, pending and in development.",
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
                "name": "Proposals",
                "code": "proposals",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Proposals",
                        "code": "proposals",
                        "fields": [
                            {"label": "Proposal Title", "code": "proposal_title", "field_type": T, "required": True},
                            {"label": "Donor", "code": "donor", "field_type": T, "required": True},
                            {"label": "Amount Requested", "code": "amount_requested", "field_type": DEC, "required": True},
                            {"label": "Submission Date", "code": "submission_date", "field_type": DT},
                            {"label": "Decision Date", "code": "decision_date", "field_type": DT},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Draft", "Submitted", "Under Review", "Approved", "Rejected", "Cancelled"], "required": True},
                            {"label": "Program Area", "code": "program_area", "field_type": T},
                            {"label": "Probability", "code": "probability", "field_type": PCT},
                            {"label": "Notes", "code": "notes", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Pipeline Summary",
                "code": "pipeline-summary",
                "groups": [
                    {
                        "name": "Pipeline Summary",
                        "code": "pipeline-summary",
                        "fields": [
                            {"label": "Total Proposals", "code": "total_proposals", "field_type": INT, "is_calculated": True, "formula": "count(proposals)"},
                            {"label": "Total Value", "code": "total_value", "field_type": DEC, "is_calculated": True, "formula": "sum(amount_requested)"},
                            {"label": "Approval Rate", "code": "approval_rate", "field_type": PCT},
                            {"label": "Pipeline Notes", "code": "pipeline_notes", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "H3",
        "title": "Donor Engagement Report",
        "description": "Report on donor relationship management and engagement activities.",
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
                            {"label": "Donor Name", "code": "donor_name", "field_type": T, "required": True},
                            {"label": "Activity Type", "code": "activity_type", "field_type": DD, "options": ["Meeting", "Report", "Site Visit", "Event", "Communication", "Proposal", "Other"], "required": True},
                            {"label": "Date", "code": "date", "field_type": DT, "required": True},
                            {"label": "Description", "code": "description", "field_type": MT},
                            {"label": "Outcome", "code": "outcome", "field_type": MT},
                            {"label": "Follow-up Required", "code": "followup_required", "field_type": CB},
                            {"label": "Next Action", "code": "next_action", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Donor Status",
                "code": "donor-status",
                "groups": [
                    {
                        "name": "Donor Status",
                        "code": "donor-status",
                        "fields": [
                            {"label": "Total Donors", "code": "total_donors", "field_type": INT},
                            {"label": "Active Donors", "code": "active_donors", "field_type": INT},
                            {"label": "New Donors", "code": "new_donors", "field_type": INT},
                            {"label": "Donor Satisfaction", "code": "donor_satisfaction", "field_type": DD, "options": ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied"]},
                            {"label": "Key Relationships", "code": "key_relationships", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "H4",
        "title": "Sponsorship Report",
        "description": "Report on sponsorship agreements, benefits delivered and revenue.",
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
                "name": "Sponsorships",
                "code": "sponsorships",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Sponsorships",
                        "code": "sponsorships",
                        "fields": [
                            {"label": "Sponsor Name", "code": "sponsor_name", "field_type": T, "required": True},
                            {"label": "Sponsorship Type", "code": "sponsorship_type", "field_type": DD, "options": ["Event", "Program", "Capital", "In-Kind", "Media", "Other"], "required": True},
                            {"label": "Value", "code": "value", "field_type": DEC, "required": True},
                            {"label": "Start Date", "code": "start_date", "field_type": DT},
                            {"label": "End Date", "code": "end_date", "field_type": DT},
                            {"label": "Benefits Delivered", "code": "benefits_delivered", "field_type": MT},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Active", "Expired", "Pending", "Cancelled"]},
                            {"label": "Renewal Likelihood", "code": "renewal_likelihood", "field_type": DD, "options": ["High", "Medium", "Low"]},
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
                            {"label": "Total Sponsorship Value", "code": "total_value", "field_type": DEC, "is_calculated": True, "formula": "sum(value)"},
                            {"label": "Active Sponsorships", "code": "active_count", "field_type": INT},
                            {"label": "Notes", "code": "notes", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "H5",
        "title": "Partnership Report",
        "description": "Report on partnerships established, maintained and their outcomes.",
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
                "name": "Partnerships",
                "code": "partnerships",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Partnerships",
                        "code": "partnerships",
                        "fields": [
                            {"label": "Partner Name", "code": "partner_name", "field_type": T, "required": True},
                            {"label": "Partnership Type", "code": "partnership_type", "field_type": DD, "options": ["Implementation", "Technical", "Financial", "Advocacy", "Research", "Other"], "required": True},
                            {"label": "Start Date", "code": "start_date", "field_type": DT},
                            {"label": "End Date", "code": "end_date", "field_type": DT},
                            {"label": "Contribution", "code": "contribution", "field_type": MT},
                            {"label": "Benefits", "code": "benefits", "field_type": MT},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Active", "Completed", "Suspended", "Terminated"]},
                            {"label": "Satisfaction", "code": "satisfaction", "field_type": DD, "options": ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied"]},
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
                            {"label": "Key Outcomes", "code": "key_outcomes", "field_type": RT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "H6",
        "title": "Fundraising Performance Report",
        "description": "Report on fundraising activities, targets and achievements.",
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
                "name": "Fundraising Activities",
                "code": "fundraising-activities",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Fundraising Activities",
                        "code": "fundraising-activities",
                        "fields": [
                            {"label": "Activity", "code": "activity", "field_type": T, "required": True},
                            {"label": "Type", "code": "type", "field_type": DD, "options": ["Event", "Campaign", "Online", "Grant", "Corporate", "Individual", "Other"], "required": True},
                            {"label": "Target Amount", "code": "target_amount", "field_type": DEC},
                            {"label": "Amount Raised", "code": "amount_raised", "field_type": DEC, "required": True},
                            {"label": "Cost", "code": "cost", "field_type": DEC},
                            {"label": "Net Income", "code": "net_income", "field_type": DEC, "is_calculated": True, "formula": "amount_raised - cost"},
                            {"label": "ROI", "code": "roi", "field_type": PCT, "is_calculated": True, "formula": "net_income / cost * 100"},
                            {"label": "Date", "code": "date", "field_type": DT},
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
                            {"label": "Total Raised", "code": "total_raised", "field_type": DEC, "is_calculated": True, "formula": "sum(amount_raised)"},
                            {"label": "Total Target", "code": "total_target", "field_type": DEC, "is_calculated": True, "formula": "sum(target_amount)"},
                            {"label": "Achievement Rate", "code": "achievement_rate", "field_type": PCT, "is_calculated": True, "formula": "total_raised / total_target * 100"},
                            {"label": "Total Costs", "code": "total_costs", "field_type": DEC, "is_calculated": True, "formula": "sum(cost)"},
                            {"label": "Overall ROI", "code": "overall_roi", "field_type": PCT, "is_calculated": True, "formula": "(total_raised - total_costs) / total_costs * 100"},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "H7",
        "title": "Income Generation Report",
        "description": "Report on income generation activities and revenue streams.",
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
                "name": "Income Streams",
                "code": "income-streams",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Income Streams",
                        "code": "income-streams",
                        "fields": [
                            {"label": "Stream Name", "code": "stream_name", "field_type": T, "required": True},
                            {"label": "Type", "code": "type", "field_type": DD, "options": ["Service Fee", "Training", "Consultancy", "Sales", "Membership", "Rental", "Other"], "required": True},
                            {"label": "Revenue", "code": "revenue", "field_type": DEC, "required": True},
                            {"label": "Costs", "code": "costs", "field_type": DEC},
                            {"label": "Net Income", "code": "net_income", "field_type": DEC, "is_calculated": True, "formula": "revenue - costs"},
                            {"label": "Growth Rate", "code": "growth_rate", "field_type": PCT},
                            {"label": "Notes", "code": "notes", "field_type": MT},
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
                            {"label": "Total Revenue", "code": "total_revenue", "field_type": DEC, "is_calculated": True, "formula": "sum(revenue)"},
                            {"label": "Total Costs", "code": "total_costs", "field_type": DEC, "is_calculated": True, "formula": "sum(costs)"},
                            {"label": "Total Net Income", "code": "total_net_income", "field_type": DEC, "is_calculated": True, "formula": "sum(net_income)"},
                            {"label": "Diversification Score", "code": "diversification_score", "field_type": DEC},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "H8",
        "title": "Resource Mobilization Dashboard",
        "description": "Dashboard summarizing resource mobilization performance and pipeline.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Dashboard Info",
                "code": "dashboard-info",
                "groups": [
                    {
                        "name": "Dashboard Info",
                        "code": "dashboard-info",
                        "fields": [
                            {"label": "Reporting Month", "code": "reporting_month", "field_type": DT, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Key Metrics",
                "code": "key-metrics",
                "groups": [
                    {
                        "name": "Key Metrics",
                        "code": "key-metrics",
                        "fields": [
                            {"label": "Total Funds Raised YTD", "code": "funds_raised_ytd", "field_type": DEC},
                            {"label": "Annual Target", "code": "annual_target", "field_type": DEC},
                            {"label": "Achievement", "code": "achievement", "field_type": PCT, "is_calculated": True, "formula": "funds_raised_ytd / annual_target * 100"},
                            {"label": "Active Grants", "code": "active_grants", "field_type": INT},
                            {"label": "Pipeline Value", "code": "pipeline_value", "field_type": DEC},
                            {"label": "New Donors", "code": "new_donors", "field_type": INT},
                        ],
                    }
                ],
            },
            {
                "name": "By Source",
                "code": "by-source",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "By Source",
                        "code": "by-source",
                        "fields": [
                            {"label": "Source", "code": "source", "field_type": DD, "options": ["Grants", "Donations", "Corporate", "Events", "Individual", "Government", "Other"], "required": True},
                            {"label": "Amount", "code": "amount", "field_type": DEC, "required": True},
                            {"label": "Percentage of Total", "code": "pct_of_total", "field_type": PCT, "is_calculated": True, "formula": "amount / total_raised * 100"},
                        ],
                    }
                ],
            },
            {
                "name": "Alerts",
                "code": "alerts",
                "groups": [
                    {
                        "name": "Alerts",
                        "code": "alerts",
                        "fields": [
                            {"label": "Upcoming Deadlines", "code": "upcoming_deadlines", "field_type": MT},
                            {"label": "At Risk Grants", "code": "at_risk_grants", "field_type": MT},
                            {"label": "Action Required", "code": "action_required", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
]
