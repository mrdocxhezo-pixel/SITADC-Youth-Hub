"""Seed data for Category B — Leadership templates."""

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

CATEGORY_B_TEMPLATES: list[dict] = [
    {
        "code": "B1",
        "title": "Monthly Leadership Activity Report",
        "description": "Monthly report on leadership activities, meetings and supervisory tasks.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Activity Summary",
                "code": "activity-summary",
                "groups": [
                    {
                        "name": "Leader Info",
                        "code": "leader-info",
                        "fields": [
                            {
                                "label": "Leader",
                                "code": "leader",
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
                                "label": "Month",
                                "code": "month",
                                "field_type": DT,
                                "required": True,
                            },
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
                            {
                                "label": "Planned Activities",
                                "code": "planned_activities",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Completed Activities",
                                "code": "completed_activities",
                                "field_type": MT,
                            },
                            {
                                "label": "Activity Dates",
                                "code": "activity_dates",
                                "field_type": DT,
                            },
                            {
                                "label": "Participants Reached",
                                "code": "participants_reached",
                                "field_type": INT,
                            },
                            {"label": "Outputs", "code": "outputs", "field_type": MT},
                            {"label": "Outcomes", "code": "outcomes", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Performance",
                "code": "performance",
                "groups": [
                    {
                        "name": "Performance",
                        "code": "performance",
                        "fields": [
                            {
                                "label": "Meetings Attended",
                                "code": "meetings_attended",
                                "field_type": INT,
                            },
                            {
                                "label": "Supervisory Activities",
                                "code": "supervisory_activities",
                                "field_type": MT,
                            },
                            {
                                "label": "Decisions Made",
                                "code": "decisions_made",
                                "field_type": MT,
                            },
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
                                "label": "Priorities for Next Month",
                                "code": "next_month_priorities",
                                "field_type": RT,
                            },
                            {
                                "label": "Evidence",
                                "code": "evidence",
                                "field_type": DOC,
                                "is_repeatable": True,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "B2",
        "title": "Weekly Leadership Update",
        "description": "Weekly update on leadership activities, decisions and blockers.",
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
                            {
                                "label": "Week Number",
                                "code": "week_number",
                                "field_type": INT,
                                "required": True,
                            },
                            {
                                "label": "Week Start Date",
                                "code": "week_start",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Week End Date",
                                "code": "week_end",
                                "field_type": DT,
                                "required": True,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Weekly Activities",
                "code": "weekly-activities",
                "groups": [
                    {
                        "name": "Activities",
                        "code": "activities",
                        "fields": [
                            {
                                "label": "Weekly Priorities",
                                "code": "weekly_priorities",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Activities Completed",
                                "code": "activities_completed",
                                "field_type": MT,
                            },
                            {
                                "label": "Key Decisions",
                                "code": "key_decisions",
                                "field_type": MT,
                            },
                            {
                                "label": "Team Updates",
                                "code": "team_updates",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Risks and Next Week",
                "code": "risks-nextweek",
                "groups": [
                    {
                        "name": "Risks",
                        "code": "risks",
                        "fields": [
                            {
                                "label": "Emerging Risks",
                                "code": "emerging_risks",
                                "field_type": MT,
                            },
                            {"label": "Blockers", "code": "blockers", "field_type": MT},
                            {
                                "label": "Support Needed",
                                "code": "support_needed",
                                "field_type": MT,
                            },
                            {
                                "label": "Activities for Next Week",
                                "code": "next_week_activities",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "B3",
        "title": "Leadership Performance Scorecard",
        "description": "Scorecard for evaluating leadership performance against KPIs.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Performance Areas",
                "code": "performance-areas",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "KPI",
                        "code": "kpi",
                        "fields": [
                            {
                                "label": "Performance Area",
                                "code": "performance_area",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "KPI",
                                "code": "kpi",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Weight",
                                "code": "weight",
                                "field_type": PCT,
                                "required": True,
                            },
                            {"label": "Target", "code": "target", "field_type": T},
                            {"label": "Actual", "code": "actual", "field_type": T},
                            {
                                "label": "Achievement Percentage",
                                "code": "achievement_pct",
                                "field_type": PCT,
                                "is_calculated": True,
                            },
                            {
                                "label": "Weighted Score",
                                "code": "weighted_score",
                                "field_type": DEC,
                                "is_calculated": True,
                                "formula": "achievement_pct * weight / 100",
                            },
                            {
                                "label": "Rating",
                                "code": "rating",
                                "field_type": DD,
                                "options": [
                                    "Excellent",
                                    "Good",
                                    "Satisfactory",
                                    "Needs Improvement",
                                    "Unsatisfactory",
                                ],
                            },
                            {
                                "label": "Evidence",
                                "code": "evidence",
                                "field_type": DOC,
                            },
                            {
                                "label": "Reviewer Comments",
                                "code": "reviewer_comments",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Overall Score",
                "code": "overall-score",
                "groups": [
                    {
                        "name": "Overall",
                        "code": "overall",
                        "fields": [
                            {
                                "label": "Overall Weighted Performance Score",
                                "code": "overall_score",
                                "field_type": DEC,
                                "is_calculated": True,
                                "formula": "sum(weighted_score)",
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "B4",
        "title": "Leadership Development Report",
        "description": "Report on leadership development activities, skills and career aspirations.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Development Objectives",
                "code": "development-objectives",
                "groups": [
                    {
                        "name": "Objectives",
                        "code": "objectives",
                        "fields": [
                            {
                                "label": "Development Objectives",
                                "code": "development_objectives",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Competency Gaps",
                                "code": "competency_gaps",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Training and Learning",
                "code": "training-learning",
                "groups": [
                    {
                        "name": "Training",
                        "code": "training",
                        "fields": [
                            {
                                "label": "Training Completed",
                                "code": "training_completed",
                                "field_type": MT,
                            },
                            {
                                "label": "Workshops Attended",
                                "code": "workshops_attended",
                                "field_type": MT,
                            },
                            {
                                "label": "Learning Outcomes",
                                "code": "learning_outcomes",
                                "field_type": RT,
                            },
                            {
                                "label": "Skills Gained",
                                "code": "skills_gained",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Progress and Planning",
                "code": "progress-planning",
                "groups": [
                    {
                        "name": "Progress",
                        "code": "progress",
                        "fields": [
                            {
                                "label": "Development Activities",
                                "code": "development_activities",
                                "field_type": MT,
                            },
                            {
                                "label": "Progress Status",
                                "code": "progress_status",
                                "field_type": DD,
                                "options": [
                                    "On Track",
                                    "Partially Complete",
                                    "Not Started",
                                ],
                            },
                            {
                                "label": "Further Development Needs",
                                "code": "further_needs",
                                "field_type": MT,
                            },
                            {
                                "label": "Career Aspirations",
                                "code": "career_aspirations",
                                "field_type": MT,
                            },
                            {
                                "label": "Supervisor Recommendations",
                                "code": "supervisor_recommendations",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "B5",
        "title": "Leadership Coaching and Mentorship Report",
        "description": "Report on coaching and mentorship sessions for leadership development.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Session Details",
                "code": "session-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {
                                "label": "Coach or Mentor",
                                "code": "coach_mentor",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Mentee",
                                "code": "mentee",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Session Date",
                                "code": "session_date",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Session Number",
                                "code": "session_number",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Session Content",
                "code": "session-content",
                "groups": [
                    {
                        "name": "Content",
                        "code": "content",
                        "fields": [
                            {
                                "label": "Objectives",
                                "code": "objectives",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Topics Discussed",
                                "code": "topics_discussed",
                                "field_type": RT,
                            },
                            {
                                "label": "Challenges Raised",
                                "code": "challenges_raised",
                                "field_type": MT,
                            },
                            {
                                "label": "Guidance Provided",
                                "code": "guidance_provided",
                                "field_type": RT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Follow-up",
                "code": "followup",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Action",
                        "code": "action",
                        "fields": [
                            {
                                "label": "Commitments",
                                "code": "commitments",
                                "field_type": MT,
                            },
                            {
                                "label": "Action Items",
                                "code": "action_items",
                                "field_type": MT,
                            },
                            {
                                "label": "Due Dates",
                                "code": "due_dates",
                                "field_type": DT,
                            },
                            {
                                "label": "Progress Since Previous Session",
                                "code": "progress",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Confidential Notes",
                "code": "confidential-notes",
                "groups": [
                    {
                        "name": "Notes",
                        "code": "notes",
                        "fields": [
                            {
                                "label": "Confidential Notes",
                                "code": "confidential_notes",
                                "field_type": MT,
                            },
                            {
                                "label": "Next Session Date",
                                "code": "next_session_date",
                                "field_type": DT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "B6",
        "title": "Staff and Volunteer Supervision Report",
        "description": "Report on supervision of staff and volunteers.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Supervision Details",
                "code": "supervision-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {
                                "label": "Supervisor",
                                "code": "supervisor",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Staff or Volunteer",
                                "code": "staff_volunteer",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Supervision Date",
                                "code": "supervision_date",
                                "field_type": DT,
                                "required": True,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Performance Assessment",
                "code": "performance-assessment",
                "groups": [
                    {
                        "name": "Assessment",
                        "code": "assessment",
                        "fields": [
                            {
                                "label": "Work Assignment",
                                "code": "work_assignment",
                                "field_type": MT,
                            },
                            {"label": "Progress", "code": "progress", "field_type": MT},
                            {
                                "label": "Attendance",
                                "code": "attendance",
                                "field_type": DD,
                                "options": ["Excellent", "Good", "Fair", "Poor"],
                            },
                            {
                                "label": "Performance",
                                "code": "performance",
                                "field_type": DD,
                                "options": [
                                    "Excellent",
                                    "Good",
                                    "Satisfactory",
                                    "Needs Improvement",
                                ],
                            },
                            {
                                "label": "Conduct",
                                "code": "conduct",
                                "field_type": DD,
                                "options": [
                                    "Excellent",
                                    "Good",
                                    "Satisfactory",
                                    "Needs Improvement",
                                ],
                            },
                            {
                                "label": "Support Provided",
                                "code": "support_provided",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Issues and Follow-up",
                "code": "issues-followup",
                "groups": [
                    {
                        "name": "Issues",
                        "code": "issues",
                        "fields": [
                            {
                                "label": "Issues Identified",
                                "code": "issues_identified",
                                "field_type": MT,
                            },
                            {
                                "label": "Corrective Action",
                                "code": "corrective_action",
                                "field_type": MT,
                            },
                            {
                                "label": "Development Needs",
                                "code": "development_needs",
                                "field_type": MT,
                            },
                            {
                                "label": "Follow-up Date",
                                "code": "followup_date",
                                "field_type": DT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "B7",
        "title": "Team Performance Report",
        "description": "Report on team performance, collaboration and productivity.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Team Details",
                "code": "team-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {
                                "label": "Team Name",
                                "code": "team_name",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Team Leader",
                                "code": "team_leader",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Team Members",
                                "code": "team_members",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Performance",
                "code": "performance",
                "groups": [
                    {
                        "name": "Performance",
                        "code": "performance",
                        "fields": [
                            {
                                "label": "Team Objectives",
                                "code": "team_objectives",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Planned Outputs",
                                "code": "planned_outputs",
                                "field_type": MT,
                            },
                            {
                                "label": "Actual Outputs",
                                "code": "actual_outputs",
                                "field_type": MT,
                            },
                            {
                                "label": "Achievement Rate",
                                "code": "achievement_rate",
                                "field_type": PCT,
                            },
                            {
                                "label": "Collaboration Rating",
                                "code": "collaboration_rating",
                                "field_type": DD,
                                "options": [
                                    "Excellent",
                                    "Good",
                                    "Satisfactory",
                                    "Needs Improvement",
                                ],
                            },
                            {
                                "label": "Attendance",
                                "code": "attendance",
                                "field_type": PCT,
                            },
                            {
                                "label": "Productivity",
                                "code": "productivity",
                                "field_type": PCT,
                            },
                            {"label": "Quality", "code": "quality", "field_type": PCT},
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
                                "field_type": MT,
                            },
                            {
                                "label": "Recognition",
                                "code": "recognition",
                                "field_type": MT,
                            },
                            {
                                "label": "Improvement Actions",
                                "code": "improvement_actions",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "B8",
        "title": "Leadership Attendance Report",
        "description": "Report on leadership attendance at meetings and activities.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Attendance Record",
                "code": "attendance-record",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Attendance",
                        "code": "attendance",
                        "fields": [
                            {
                                "label": "Leader",
                                "code": "leader",
                                "field_type": T,
                                "required": True,
                            },
                            {"label": "Position", "code": "position", "field_type": T},
                            {
                                "label": "Meeting or Activity",
                                "code": "meeting_activity",
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
                                "label": "Expected Attendance",
                                "code": "expected_attendance",
                                "field_type": CB,
                            },
                            {
                                "label": "Attendance Status",
                                "code": "attendance_status",
                                "field_type": DD,
                                "options": ["Present", "Absent", "Late", "Apology"],
                                "required": True,
                            },
                            {
                                "label": "Arrival Time",
                                "code": "arrival_time",
                                "field_type": TM,
                            },
                            {
                                "label": "Departure Time",
                                "code": "departure_time",
                                "field_type": TM,
                            },
                            {
                                "label": "Reason for Absence",
                                "code": "reason_absence",
                                "field_type": MT,
                            },
                            {
                                "label": "Apology Submitted",
                                "code": "apology_submitted",
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
                                "label": "Attendance Percentage",
                                "code": "attendance_pct",
                                "field_type": PCT,
                                "is_calculated": True,
                                "formula": "count(status=Present) / count(total) * 100",
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "B9",
        "title": "Leadership Succession Progress Report",
        "description": "Report on leadership succession planning progress.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Succession Planning",
                "code": "succession-planning",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Position",
                        "code": "position",
                        "fields": [
                            {
                                "label": "Critical Position",
                                "code": "critical_position",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Current Position Holder",
                                "code": "current_holder",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Potential Successor",
                                "code": "potential_successor",
                                "field_type": T,
                            },
                            {
                                "label": "Readiness Level",
                                "code": "readiness_level",
                                "field_type": DD,
                                "options": [
                                    "Ready Now",
                                    "Ready in 1-2 Years",
                                    "Ready in 3-5 Years",
                                    "Not Identified",
                                ],
                            },
                            {
                                "label": "Competency Requirements",
                                "code": "competency_requirements",
                                "field_type": MT,
                            },
                            {
                                "label": "Identified Gaps",
                                "code": "identified_gaps",
                                "field_type": MT,
                            },
                            {
                                "label": "Development Actions",
                                "code": "development_actions",
                                "field_type": MT,
                            },
                            {
                                "label": "Mentorship Status",
                                "code": "mentorship_status",
                                "field_type": DD,
                                "options": ["Active", "Planned", "Not Started"],
                            },
                            {
                                "label": "Expected Readiness Date",
                                "code": "expected_readiness",
                                "field_type": DT,
                            },
                            {
                                "label": "Succession Risk",
                                "code": "succession_risk",
                                "field_type": DD,
                                "options": ["Low", "Medium", "High", "Critical"],
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
        "code": "B10",
        "title": "Leadership Challenges and Recommendations Report",
        "description": "Report on challenges faced by leadership and recommendations.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Challenges",
                "code": "challenges",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Challenge",
                        "code": "challenge",
                        "fields": [
                            {
                                "label": "Leadership Area",
                                "code": "leadership_area",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Challenge",
                                "code": "challenge",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Root Cause",
                                "code": "root_cause",
                                "field_type": MT,
                            },
                            {
                                "label": "Effect on the Organization",
                                "code": "effect",
                                "field_type": MT,
                            },
                            {
                                "label": "Severity",
                                "code": "severity",
                                "field_type": DD,
                                "options": ["Low", "Medium", "High", "Critical"],
                            },
                            {
                                "label": "Current Response",
                                "code": "current_response",
                                "field_type": MT,
                            },
                            {
                                "label": "Recommended Solution",
                                "code": "recommended_solution",
                                "field_type": RT,
                            },
                            {
                                "label": "Required Resources",
                                "code": "required_resources",
                                "field_type": MT,
                            },
                            {
                                "label": "Responsible Person",
                                "code": "responsible_person",
                                "field_type": T,
                            },
                            {
                                "label": "Target Completion Date",
                                "code": "target_date",
                                "field_type": DT,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": ["Open", "In Progress", "Resolved"],
                            },
                        ],
                    }
                ],
            },
        ],
    },
]
