"""Seed data for Category O — Organizational Learning templates."""

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

CATEGORY_O_TEMPLATES: list[dict] = [
    {
        "code": "O1",
        "title": "After Action Review",
        "description": "Structured review of a completed activity or project phase.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Review Info",
                "code": "review-info",
                "groups": [
                    {
                        "name": "Review Info",
                        "code": "review-info",
                        "fields": [
                            {
                                "label": "Activity/Project",
                                "code": "activity_project",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Review Date",
                                "code": "review_date",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Facilitator",
                                "code": "facilitator",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Participants",
                                "code": "participants",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Review Questions",
                "code": "review-questions",
                "groups": [
                    {
                        "name": "Review Questions",
                        "code": "review-questions",
                        "fields": [
                            {
                                "label": "What Was Planned",
                                "code": "planned",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "What Actually Happened",
                                "code": "what_happened",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "What Went Well",
                                "code": "went_well",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "What Could Be Improved",
                                "code": "improvements",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Why Were There Differences",
                                "code": "differences",
                                "field_type": RT,
                            },
                            {
                                "label": "What Will We Do Differently Next Time",
                                "code": "next_time",
                                "field_type": RT,
                                "required": True,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Action Items",
                "code": "action-items",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Action Items",
                        "code": "action-items",
                        "fields": [
                            {
                                "label": "Action Item",
                                "code": "action_item",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Responsible Person",
                                "code": "responsible_person",
                                "field_type": T,
                            },
                            {"label": "Due Date", "code": "due_date", "field_type": DT},
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": ["Open", "In Progress", "Completed"],
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "O2",
        "title": "Reflection Meeting Report",
        "description": "Report from team or organizational reflection meetings.",
        "reporting_frequency": "QUARTERLY",
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
                                "label": "Facilitator",
                                "code": "facilitator",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Participants",
                                "code": "participants",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Reflections",
                "code": "reflections",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Reflections",
                        "code": "reflections",
                        "fields": [
                            {
                                "label": "Topic Discussed",
                                "code": "topic",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Current Situation",
                                "code": "current_situation",
                                "field_type": MT,
                            },
                            {
                                "label": "What We Learned",
                                "code": "learned",
                                "field_type": MT,
                            },
                            {
                                "label": "Challenges",
                                "code": "challenges",
                                "field_type": MT,
                            },
                            {
                                "label": "Opportunities",
                                "code": "opportunities",
                                "field_type": MT,
                            },
                            {
                                "label": "Decisions Made",
                                "code": "decisions",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Action Plan",
                "code": "action-plan",
                "groups": [
                    {
                        "name": "Action Plan",
                        "code": "action-plan",
                        "fields": [
                            {
                                "label": "Action Items",
                                "code": "action_items",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Next Meeting Date",
                                "code": "next_meeting_date",
                                "field_type": DT,
                            },
                            {"label": "Minutes", "code": "minutes", "field_type": DOC},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "O3",
        "title": "Lessons Learned Register",
        "description": "Register capturing lessons learned across programs and projects.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Entries",
                "code": "entries",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Entries",
                        "code": "entries",
                        "fields": [
                            {
                                "label": "Date Captured",
                                "code": "date_captured",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Source",
                                "code": "source",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Program/Project",
                                "code": "program_project",
                                "field_type": T,
                            },
                            {
                                "label": "Lesson Category",
                                "code": "lesson_category",
                                "field_type": DD,
                                "options": [
                                    "Planning",
                                    "Implementation",
                                    "Monitoring",
                                    "Staffing",
                                    "Budget",
                                    "Partnerships",
                                    "Community",
                                    "Technology",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Lesson Learned",
                                "code": "lesson_learned",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Recommendation",
                                "code": "recommendation",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Impact",
                                "code": "impact",
                                "field_type": DD,
                                "options": ["High", "Medium", "Low"],
                            },
                            {
                                "label": "Applicability",
                                "code": "applicability",
                                "field_type": MT,
                            },
                            {
                                "label": "Validated",
                                "code": "validated",
                                "field_type": CB,
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
                                "label": "Total Lessons",
                                "code": "total_lessons",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(entries)",
                            },
                            {
                                "label": "High Impact Lessons",
                                "code": "high_impact",
                                "field_type": INT,
                            },
                            {
                                "label": "Lessons Applied",
                                "code": "lessons_applied",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "O4",
        "title": "Best Practice Register",
        "description": "Register of best practices identified and documented.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Entries",
                "code": "entries",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Entries",
                        "code": "entries",
                        "fields": [
                            {
                                "label": "Practice Title",
                                "code": "practice_title",
                                "field_type": T,
                                "required": True,
                            },
                            {"label": "Source", "code": "source", "field_type": T},
                            {
                                "label": "Program/Project",
                                "code": "program_project",
                                "field_type": T,
                            },
                            {
                                "label": "Category",
                                "code": "category",
                                "field_type": DD,
                                "options": [
                                    "Technical",
                                    "Management",
                                    "Financial",
                                    "Partnerships",
                                    "Community",
                                    "Innovation",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Description",
                                "code": "description",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Evidence of Effectiveness",
                                "code": "evidence",
                                "field_type": MT,
                            },
                            {
                                "label": "Replicability",
                                "code": "replicability",
                                "field_type": DD,
                                "options": [
                                    "Highly Replicable",
                                    "Replicable with Adaptation",
                                    "Context Specific",
                                ],
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Identified",
                                    "Documented",
                                    "Shared",
                                    "Mainstreamed",
                                ],
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
                                "label": "Total Best Practices",
                                "code": "total_practices",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(entries)",
                            },
                            {
                                "label": "Shared Practices",
                                "code": "shared_practices",
                                "field_type": INT,
                            },
                            {
                                "label": "Mainstreamed Practices",
                                "code": "mainstreamed",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "O5",
        "title": "Innovation Register",
        "description": "Register of innovations piloted and implemented.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Entries",
                "code": "entries",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Entries",
                        "code": "entries",
                        "fields": [
                            {
                                "label": "Innovation Title",
                                "code": "innovation_title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Category",
                                "code": "category",
                                "field_type": DD,
                                "options": [
                                    "Process",
                                    "Technology",
                                    "Service",
                                    "Model",
                                    "Policy",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Description",
                                "code": "description",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Problem Addressed",
                                "code": "problem_addressed",
                                "field_type": MT,
                            },
                            {
                                "label": "Implementation Date",
                                "code": "implementation_date",
                                "field_type": DT,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Proposed",
                                    "Pilot",
                                    "Scaling",
                                    "Mainstreamed",
                                    "Discontinued",
                                ],
                            },
                            {"label": "Impact", "code": "impact", "field_type": MT},
                            {
                                "label": "Lessons Learned",
                                "code": "lessons_learned",
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
                                "label": "Total Innovations",
                                "code": "total_innovations",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(entries)",
                            },
                            {
                                "label": "Successful Innovations",
                                "code": "successful",
                                "field_type": INT,
                            },
                            {
                                "label": "Mainstreamed",
                                "code": "mainstreamed",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "O6",
        "title": "Continuous Improvement Log",
        "description": "Log of continuous improvement activities and their outcomes.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Entries",
                "code": "entries",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Entries",
                        "code": "entries",
                        "fields": [
                            {
                                "label": "Date",
                                "code": "date",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Area",
                                "code": "area",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Current Process",
                                "code": "current_process",
                                "field_type": MT,
                            },
                            {
                                "label": "Proposed Improvement",
                                "code": "proposed_improvement",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Expected Benefit",
                                "code": "expected_benefit",
                                "field_type": MT,
                            },
                            {
                                "label": "Responsible Person",
                                "code": "responsible_person",
                                "field_type": T,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Proposed",
                                    "Approved",
                                    "Implementing",
                                    "Completed",
                                    "Rejected",
                                ],
                            },
                            {
                                "label": "Actual Outcome",
                                "code": "actual_outcome",
                                "field_type": MT,
                            },
                            {
                                "label": "Date Completed",
                                "code": "date_completed",
                                "field_type": DT,
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
                                "label": "Total Initiatives",
                                "code": "total_initiatives",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(entries)",
                            },
                            {
                                "label": "Completed Initiatives",
                                "code": "completed",
                                "field_type": INT,
                            },
                            {
                                "label": "Success Rate",
                                "code": "success_rate",
                                "field_type": PCT,
                                "is_calculated": True,
                                "formula": "completed / total_initiatives * 100",
                            },
                        ],
                    }
                ],
            },
        ],
    },
]
