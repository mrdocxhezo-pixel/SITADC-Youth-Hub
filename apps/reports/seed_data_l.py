"""Seed data for Category L — Community Engagement templates."""

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

CATEGORY_L_TEMPLATES: list[dict] = [
    {
        "code": "L1",
        "title": "Community Outreach Report",
        "description": "Report on community outreach activities and engagement.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {
                                "label": "Reporting Month",
                                "code": "reporting_month",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Prepared By",
                                "code": "prepared_by",
                                "field_type": T,
                                "required": True,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Outreach Activities",
                "code": "outreach-activities",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Outreach Activities",
                        "code": "outreach-activities",
                        "fields": [
                            {
                                "label": "Activity Type",
                                "code": "activity_type",
                                "field_type": DD,
                                "options": [
                                    "Door-to-Door",
                                    "Community Meeting",
                                    "Market Outreach",
                                    "School Visit",
                                    "Health Campaign",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Location",
                                "code": "location",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Date",
                                "code": "date",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Target Group",
                                "code": "target_group",
                                "field_type": T,
                            },
                            {
                                "label": "People Reached",
                                "code": "people_reached",
                                "field_type": INT,
                            },
                            {
                                "label": "Description",
                                "code": "description",
                                "field_type": MT,
                            },
                            {
                                "label": "Materials Distributed",
                                "code": "materials_distributed",
                                "field_type": MT,
                            },
                            {
                                "label": "Photos",
                                "code": "photos",
                                "field_type": IMG,
                                "is_repeatable": True,
                            },
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
                            {
                                "label": "Total People Reached",
                                "code": "total_reached",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "sum(people_reached)",
                            },
                            {
                                "label": "Total Activities",
                                "code": "total_activities",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(activities)",
                            },
                            {
                                "label": "Key Issues Identified",
                                "code": "key_issues",
                                "field_type": MT,
                            },
                            {
                                "label": "Follow-up Actions",
                                "code": "followup_actions",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "L2",
        "title": "Community Needs Assessment",
        "description": "Assessment of community needs, priorities and existing resources.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Assessment Info",
                "code": "assessment-info",
                "groups": [
                    {
                        "name": "Assessment Info",
                        "code": "assessment-info",
                        "fields": [
                            {
                                "label": "Assessment Title",
                                "code": "assessment_title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Community",
                                "code": "community",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Date",
                                "code": "date",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Assessor",
                                "code": "assessor",
                                "field_type": T,
                                "required": True,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Methodology",
                "code": "methodology",
                "groups": [
                    {
                        "name": "Methodology",
                        "code": "methodology",
                        "fields": [
                            {
                                "label": "Methods Used",
                                "code": "methods_used",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Sample Size",
                                "code": "sample_size",
                                "field_type": INT,
                            },
                            {
                                "label": "Response Rate",
                                "code": "response_rate",
                                "field_type": PCT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Needs Identified",
                "code": "needs-identified",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Needs Identified",
                        "code": "needs-identified",
                        "fields": [
                            {
                                "label": "Need Category",
                                "code": "need_category",
                                "field_type": DD,
                                "options": [
                                    "Health",
                                    "Education",
                                    "Economic",
                                    "Social",
                                    "Infrastructure",
                                    "Environment",
                                    "Governance",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Description",
                                "code": "description",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Priority",
                                "code": "priority",
                                "field_type": DD,
                                "options": ["High", "Medium", "Low"],
                                "required": True,
                            },
                            {
                                "label": "Affected Population",
                                "code": "affected_population",
                                "field_type": INT,
                            },
                            {
                                "label": "Current Resources",
                                "code": "current_resources",
                                "field_type": MT,
                            },
                            {"label": "Gaps", "code": "gaps", "field_type": MT},
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
                            {
                                "label": "Priority Actions",
                                "code": "priority_actions",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Resource Requirements",
                                "code": "resource_requirements",
                                "field_type": MT,
                            },
                            {"label": "Timeline", "code": "timeline", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "L3",
        "title": "Community Feedback Report",
        "description": "Report on feedback received from community members.",
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
                            {
                                "label": "Reporting Period",
                                "code": "reporting_period",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Prepared By",
                                "code": "prepared_by",
                                "field_type": T,
                                "required": True,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Feedback Items",
                "code": "feedback-items",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Feedback Items",
                        "code": "feedback-items",
                        "fields": [
                            {
                                "label": "Source",
                                "code": "source",
                                "field_type": DD,
                                "options": [
                                    "Community Meeting",
                                    "Suggestion Box",
                                    "Hotline",
                                    "Survey",
                                    "Direct",
                                    "Social Media",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Date Received",
                                "code": "date_received",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Category",
                                "code": "category",
                                "field_type": DD,
                                "options": [
                                    "Service Quality",
                                    "Program Design",
                                    "Staff Conduct",
                                    "Accessibility",
                                    "Complaint",
                                    "Suggestion",
                                    "Compliment",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Description",
                                "code": "description",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Response Provided",
                                "code": "response_provided",
                                "field_type": MT,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Received",
                                    "Acknowledged",
                                    "Investigating",
                                    "Resolved",
                                    "Escalated",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Action Taken",
                                "code": "action_taken",
                                "field_type": MT,
                            },
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
                            {
                                "label": "Total Feedback Items",
                                "code": "total_items",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(feedback)",
                            },
                            {
                                "label": "Resolved Items",
                                "code": "resolved_items",
                                "field_type": INT,
                            },
                            {
                                "label": "Resolution Rate",
                                "code": "resolution_rate",
                                "field_type": PCT,
                                "is_calculated": True,
                                "formula": "resolved_items / total_items * 100",
                            },
                            {
                                "label": "Key Themes",
                                "code": "key_themes",
                                "field_type": MT,
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
        "code": "L4",
        "title": "Community Meeting Report",
        "description": "Report documenting community meetings held.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Meeting Info",
                "code": "meeting-info",
                "groups": [
                    {
                        "name": "Meeting Info",
                        "code": "meeting-info",
                        "fields": [
                            {
                                "label": "Meeting Title",
                                "code": "meeting_title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Date",
                                "code": "date",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Location",
                                "code": "location",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Facilitator",
                                "code": "facilitator",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Number of Attendees",
                                "code": "num_attendees",
                                "field_type": INT,
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
                        "name": "Agenda Items",
                        "code": "agenda-items",
                        "fields": [
                            {
                                "label": "Agenda Item",
                                "code": "agenda_item",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Presenter",
                                "code": "presenter",
                                "field_type": T,
                            },
                            {
                                "label": "Discussion Summary",
                                "code": "discussion_summary",
                                "field_type": MT,
                            },
                            {
                                "label": "Decisions Made",
                                "code": "decisions_made",
                                "field_type": MT,
                            },
                            {
                                "label": "Action Items",
                                "code": "action_items",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Follow-up",
                "code": "follow-up",
                "groups": [
                    {
                        "name": "Follow-up",
                        "code": "follow-up",
                        "fields": [
                            {
                                "label": "Key Outcomes",
                                "code": "key_outcomes",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Action Items",
                                "code": "action_items",
                                "field_type": MT,
                            },
                            {
                                "label": "Next Meeting Date",
                                "code": "next_meeting_date",
                                "field_type": DT,
                            },
                            {
                                "label": "Photos",
                                "code": "photos",
                                "field_type": IMG,
                                "is_repeatable": True,
                            },
                            {
                                "label": "Attendance List",
                                "code": "attendance_list",
                                "field_type": DOC,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "L5",
        "title": "Community Impact Report",
        "description": "Report on the impact of programs on the community.",
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
                            {
                                "label": "Reporting Year",
                                "code": "reporting_year",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Prepared By",
                                "code": "prepared_by",
                                "field_type": T,
                                "required": True,
                            },
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
                        "name": "Impact Areas",
                        "code": "impact-areas",
                        "fields": [
                            {
                                "label": "Impact Area",
                                "code": "impact_area",
                                "field_type": DD,
                                "options": [
                                    "Economic",
                                    "Social",
                                    "Health",
                                    "Education",
                                    "Environmental",
                                    "Governance",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Description of Change",
                                "code": "change_description",
                                "field_type": RT,
                                "required": True,
                            },
                            {"label": "Evidence", "code": "evidence", "field_type": MT},
                            {
                                "label": "Beneficiaries Affected",
                                "code": "beneficiaries_affected",
                                "field_type": INT,
                            },
                            {
                                "label": "Sustainability",
                                "code": "sustainability",
                                "field_type": DD,
                                "options": ["High", "Medium", "Low"],
                            },
                            {
                                "label": "Photos",
                                "code": "photos",
                                "field_type": IMG,
                                "is_repeatable": True,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Community Voice",
                "code": "community-voice",
                "groups": [
                    {
                        "name": "Community Voice",
                        "code": "community-voice",
                        "fields": [
                            {
                                "label": "Testimonials",
                                "code": "testimonials",
                                "field_type": MT,
                            },
                            {
                                "label": "Community Leaders Feedback",
                                "code": "leaders_feedback",
                                "field_type": MT,
                            },
                            {
                                "label": "Unexpected Outcomes",
                                "code": "unexpected_outcomes",
                                "field_type": MT,
                            },
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
                            {
                                "label": "Overall Impact Rating",
                                "code": "overall_impact",
                                "field_type": DD,
                                "options": [
                                    "Very High",
                                    "High",
                                    "Moderate",
                                    "Low",
                                    "None",
                                ],
                            },
                            {
                                "label": "Key Achievements",
                                "code": "key_achievements",
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
        "code": "L6",
        "title": "Beneficiary Testimonial Report",
        "description": "Collection of testimonials from program beneficiaries.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {
                                "label": "Program Name",
                                "code": "program_name",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Collection Date",
                                "code": "collection_date",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Collected By",
                                "code": "collected_by",
                                "field_type": T,
                                "required": True,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Testimonials",
                "code": "testimonials",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Testimonials",
                        "code": "testimonials",
                        "fields": [
                            {
                                "label": "Beneficiary Name",
                                "code": "beneficiary_name",
                                "field_type": T,
                                "required": True,
                            },
                            {"label": "Age", "code": "age", "field_type": INT},
                            {
                                "label": "Gender",
                                "code": "gender",
                                "field_type": DD,
                                "options": ["Male", "Female", "Other"],
                            },
                            {"label": "Location", "code": "location", "field_type": T},
                            {
                                "label": "Testimonial",
                                "code": "testimonial",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Photo Consent",
                                "code": "photo_consent",
                                "field_type": CB,
                            },
                            {"label": "Photo", "code": "photo", "field_type": IMG},
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
                            {
                                "label": "Total Testimonials",
                                "code": "total_testimonials",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(testimonials)",
                            },
                            {
                                "label": "Common Themes",
                                "code": "common_themes",
                                "field_type": MT,
                            },
                            {
                                "label": "Usage Consent",
                                "code": "usage_consent",
                                "field_type": CB,
                            },
                        ],
                    }
                ],
            },
        ],
    },
]
