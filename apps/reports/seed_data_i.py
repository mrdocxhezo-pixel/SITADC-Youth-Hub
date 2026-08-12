"""Seed data for Category I — Training and Capacity Building templates."""

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

CATEGORY_I_TEMPLATES: list[dict] = [
    {
        "code": "I1",
        "title": "Training Plan",
        "description": "Annual training plan outlining capacity building activities.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Plan Info",
                "code": "plan-info",
                "groups": [
                    {
                        "name": "Plan Info",
                        "code": "plan-info",
                        "fields": [
                            {"label": "Reporting Year", "code": "reporting_year", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                            {"label": "Approved By", "code": "approved_by", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Training Activities",
                "code": "training-activities",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Training Activities",
                        "code": "training-activities",
                        "fields": [
                            {"label": "Training Title", "code": "training_title", "field_type": T, "required": True},
                            {"label": "Training Type", "code": "training_type", "field_type": DD, "options": ["Workshop", "Seminar", "Course", "On-the-Job", "Online", "Conference", "Other"], "required": True},
                            {"label": "Target Group", "code": "target_group", "field_type": T, "required": True},
                            {"label": "Number of Participants", "code": "num_participants", "field_type": INT},
                            {"label": "Planned Date", "code": "planned_date", "field_type": DT},
                            {"label": "Duration", "code": "duration", "field_type": T},
                            {"label": "Location", "code": "location", "field_type": T},
                            {"label": "Trainer", "code": "trainer", "field_type": T},
                            {"label": "Budget", "code": "budget", "field_type": DEC},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Planned", "Confirmed", "Completed", "Cancelled"]},
                        ],
                    }
                ],
            },
            {
                "name": "Budget Summary",
                "code": "budget-summary",
                "groups": [
                    {
                        "name": "Budget Summary",
                        "code": "budget-summary",
                        "fields": [
                            {"label": "Total Training Budget", "code": "total_budget", "field_type": DEC},
                            {"label": "Budget Allocated", "code": "budget_allocated", "field_type": DEC, "is_calculated": True, "formula": "sum(budget)"},
                            {"label": "Remaining Budget", "code": "remaining_budget", "field_type": DEC, "is_calculated": True, "formula": "total_budget - budget_allocated"},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "I2",
        "title": "Training Attendance Register",
        "description": "Register of participants attending training sessions.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Training Info",
                "code": "training-info",
                "groups": [
                    {
                        "name": "Training Info",
                        "code": "training-info",
                        "fields": [
                            {"label": "Training Title", "code": "training_title", "field_type": T, "required": True},
                            {"label": "Training Date", "code": "training_date", "field_type": DT, "required": True},
                            {"label": "Trainer", "code": "trainer", "field_type": T, "required": True},
                            {"label": "Location", "code": "location", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Participants",
                "code": "participants",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Participants",
                        "code": "participants",
                        "fields": [
                            {"label": "Full Name", "code": "full_name", "field_type": T, "required": True},
                            {"label": "Organization", "code": "organization", "field_type": T},
                            {"label": "Title/Position", "code": "title_position", "field_type": T},
                            {"label": "Phone", "code": "phone", "field_type": T},
                            {"label": "Email", "code": "email", "field_type": T},
                            {"label": "Attendance", "code": "attendance", "field_type": DD, "options": ["Present", "Absent", "Late", "Excused"], "required": True},
                            {"label": "Arrival Time", "code": "arrival_time", "field_type": TM},
                            {"label": "Signature", "code": "signature", "field_type": SIG},
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
                            {"label": "Total Expected", "code": "total_expected", "field_type": INT},
                            {"label": "Total Present", "code": "total_present", "field_type": INT},
                            {"label": "Attendance Rate", "code": "attendance_rate", "field_type": PCT, "is_calculated": True, "formula": "total_present / total_expected * 100"},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "I3",
        "title": "Training Evaluation Report",
        "description": "Report evaluating the effectiveness of a training session.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Training Info",
                "code": "training-info",
                "groups": [
                    {
                        "name": "Training Info",
                        "code": "training-info",
                        "fields": [
                            {"label": "Training Title", "code": "training_title", "field_type": T, "required": True},
                            {"label": "Training Date", "code": "training_date", "field_type": DT, "required": True},
                            {"label": "Trainer", "code": "trainer", "field_type": T, "required": True},
                            {"label": "Number of Participants", "code": "num_participants", "field_type": INT},
                        ],
                    }
                ],
            },
            {
                "name": "Evaluation Criteria",
                "code": "evaluation-criteria",
                "groups": [
                    {
                        "name": "Evaluation Criteria",
                        "code": "evaluation-criteria",
                        "fields": [
                            {"label": "Relevance", "code": "relevance", "field_type": DD, "options": ["Very Relevant", "Relevant", "Somewhat Relevant", "Not Relevant"], "required": True},
                            {"label": "Content Quality", "code": "content_quality", "field_type": DD, "options": ["Excellent", "Good", "Average", "Poor"], "required": True},
                            {"label": "Trainer Effectiveness", "code": "trainer_effectiveness", "field_type": DD, "options": ["Excellent", "Good", "Average", "Poor"], "required": True},
                            {"label": "Training Materials", "code": "training_materials", "field_type": DD, "options": ["Excellent", "Good", "Average", "Poor"]},
                            {"label": "Venue and Logistics", "code": "venue_logistics", "field_type": DD, "options": ["Excellent", "Good", "Average", "Poor"]},
                            {"label": "Overall Satisfaction", "code": "overall_satisfaction", "field_type": DD, "options": ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied"], "required": True},
                            {"label": "Knowledge Gained", "code": "knowledge_gained", "field_type": DD, "options": ["Significant", "Moderate", "Little", "None"]},
                            {"label": "Likelihood to Apply", "code": "likelihood_apply", "field_type": DD, "options": ["Very Likely", "Likely", "Neutral", "Unlikely"]},
                        ],
                    }
                ],
            },
            {
                "name": "Feedback",
                "code": "feedback",
                "groups": [
                    {
                        "name": "Feedback",
                        "code": "feedback",
                        "fields": [
                            {"label": "What Worked Well", "code": "worked_well", "field_type": MT},
                            {"label": "What Could Be Improved", "code": "improvements", "field_type": MT},
                            {"label": "Additional Comments", "code": "comments", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "I4",
        "title": "Participant Feedback Report",
        "description": "Aggregated feedback report from training participants.",
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
                            {"label": "Training Title", "code": "training_title", "field_type": T, "required": True},
                            {"label": "Total Responses", "code": "total_responses", "field_type": INT},
                            {"label": "Report Date", "code": "report_date", "field_type": DT, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Feedback Summary",
                "code": "feedback-summary",
                "groups": [
                    {
                        "name": "Feedback Summary",
                        "code": "feedback-summary",
                        "fields": [
                            {"label": "Average Relevance Score", "code": "avg_relevance", "field_type": DEC},
                            {"label": "Average Content Score", "code": "avg_content", "field_type": DEC},
                            {"label": "Average Trainer Score", "code": "avg_trainer", "field_type": DEC},
                            {"label": "Average Overall Satisfaction", "code": "avg_satisfaction", "field_type": DEC},
                            {"label": "Net Promoter Score", "code": "nps", "field_type": DEC},
                        ],
                    }
                ],
            },
            {
                "name": "Key Themes",
                "code": "key-themes",
                "groups": [
                    {
                        "name": "Key Themes",
                        "code": "key-themes",
                        "fields": [
                            {"label": "Positive Feedback Themes", "code": "positive_themes", "field_type": MT},
                            {"label": "Improvement Suggestions", "code": "improvement_suggestions", "field_type": MT},
                            {"label": "Common Questions", "code": "common_questions", "field_type": MT},
                            {"label": "Action Items", "code": "action_items", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "I5",
        "title": "Competency Assessment Report",
        "description": "Report assessing participant competencies before and after training.",
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
                            {"label": "Training Title", "code": "training_title", "field_type": T, "required": True},
                            {"label": "Assessment Date", "code": "assessment_date", "field_type": DT, "required": True},
                            {"label": "Assessor", "code": "assessor", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Competencies",
                "code": "competencies",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Competencies",
                        "code": "competencies",
                        "fields": [
                            {"label": "Participant", "code": "participant", "field_type": T, "required": True},
                            {"label": "Competency Area", "code": "competency_area", "field_type": T, "required": True},
                            {"label": "Pre-Training Score", "code": "pre_score", "field_type": DEC, "required": True},
                            {"label": "Post-Training Score", "code": "post_score", "field_type": DEC, "required": True},
                            {"label": "Improvement", "code": "improvement", "field_type": DEC, "is_calculated": True, "formula": "post_score - pre_score"},
                            {"label": "Improvement Percentage", "code": "improvement_pct", "field_type": PCT, "is_calculated": True, "formula": "improvement / pre_score * 100"},
                            {"label": "Comments", "code": "comments", "field_type": MT},
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
                            {"label": "Average Improvement", "code": "avg_improvement", "field_type": DEC, "is_calculated": True, "formula": "mean(improvement)"},
                            {"label": "Competencies Mastered", "code": "competencies_mastered", "field_type": INT},
                            {"label": "Overall Assessment", "code": "overall_assessment", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "I6",
        "title": "Capacity Building Report",
        "description": "Report on organizational capacity building initiatives and outcomes.",
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
                "name": "Initiatives",
                "code": "initiatives",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Initiatives",
                        "code": "initiatives",
                        "fields": [
                            {"label": "Initiative", "code": "initiative", "field_type": T, "required": True},
                            {"label": "Type", "code": "type", "field_type": DD, "options": ["Training", "Mentorship", "Coaching", "Peer Learning", "Exchange", "Other"], "required": True},
                            {"label": "Participants", "code": "participants", "field_type": INT},
                            {"label": "Budget", "code": "budget", "field_type": DEC},
                            {"label": "Outcome", "code": "outcome", "field_type": MT},
                            {"label": "Rating", "code": "rating", "field_type": DD, "options": ["Excellent", "Good", "Satisfactory", "Needs Improvement"]},
                        ],
                    }
                ],
            },
            {
                "name": "Capacity Assessment",
                "code": "capacity-assessment",
                "groups": [
                    {
                        "name": "Capacity Assessment",
                        "code": "capacity-assessment",
                        "fields": [
                            {"label": "Management Capacity", "code": "management_capacity", "field_type": DD, "options": ["Strong", "Adequate", "Developing", "Weak"]},
                            {"label": "Technical Capacity", "code": "technical_capacity", "field_type": DD, "options": ["Strong", "Adequate", "Developing", "Weak"]},
                            {"label": "Financial Capacity", "code": "financial_capacity", "field_type": DD, "options": ["Strong", "Adequate", "Developing", "Weak"]},
                            {"label": "M&E Capacity", "code": "me_capacity", "field_type": DD, "options": ["Strong", "Adequate", "Developing", "Weak"]},
                            {"label": "Overall Capacity Score", "code": "overall_capacity", "field_type": DEC},
                            {"label": "Key Gaps", "code": "key_gaps", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "I7",
        "title": "Mentorship Report",
        "description": "Report on mentorship program activities and outcomes.",
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
                            {"label": "Program Coordinator", "code": "coordinator", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Mentorship Pairs",
                "code": "mentorship-pairs",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Mentorship Pairs",
                        "code": "mentorship-pairs",
                        "fields": [
                            {"label": "Mentor", "code": "mentor", "field_type": T, "required": True},
                            {"label": "Mentee", "code": "mentee", "field_type": T, "required": True},
                            {"label": "Start Date", "code": "start_date", "field_type": DT},
                            {"label": "Sessions Completed", "code": "sessions_completed", "field_type": INT},
                            {"label": "Goals Set", "code": "goals_set", "field_type": MT},
                            {"label": "Goals Achieved", "code": "goals_achieved", "field_type": MT},
                            {"label": "Mentor Rating", "code": "mentor_rating", "field_type": DD, "options": ["Excellent", "Good", "Average", "Needs Improvement"]},
                            {"label": "Mentee Satisfaction", "code": "mentee_satisfaction", "field_type": DD, "options": ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied"]},
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
                            {"label": "Total Active Pairs", "code": "total_pairs", "field_type": INT},
                            {"label": "Average Sessions", "code": "avg_sessions", "field_type": DEC},
                            {"label": "Completion Rate", "code": "completion_rate", "field_type": PCT},
                            {"label": "Overall Program Rating", "code": "overall_rating", "field_type": DD, "options": ["Excellent", "Good", "Satisfactory", "Needs Improvement"]},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "I8",
        "title": "Coaching Report",
        "description": "Report on individual coaching sessions and development progress.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Session Info",
                "code": "session-info",
                "groups": [
                    {
                        "name": "Session Info",
                        "code": "session-info",
                        "fields": [
                            {"label": "Coach", "code": "coach", "field_type": T, "required": True},
                            {"label": "Coachee", "code": "coachee", "field_type": T, "required": True},
                            {"label": "Session Date", "code": "session_date", "field_type": DT, "required": True},
                            {"label": "Session Number", "code": "session_number", "field_type": INT},
                            {"label": "Duration", "code": "duration", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Session Details",
                "code": "session-details",
                "groups": [
                    {
                        "name": "Session Details",
                        "code": "session-details",
                        "fields": [
                            {"label": "Objectives", "code": "objectives", "field_type": MT, "required": True},
                            {"label": "Topics Discussed", "code": "topics_discussed", "field_type": RT},
                            {"label": "Key Insights", "code": "key_insights", "field_type": MT},
                            {"label": "Action Items", "code": "action_items", "field_type": MT},
                            {"label": "Progress Since Last Session", "code": "progress", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Development Plan",
                "code": "development-plan",
                "groups": [
                    {
                        "name": "Development Plan",
                        "code": "development-plan",
                        "fields": [
                            {"label": "Development Goals", "code": "development_goals", "field_type": MT},
                            {"label": "Short-term Actions", "code": "short_term_actions", "field_type": MT},
                            {"label": "Long-term Goals", "code": "long_term_goals", "field_type": MT},
                            {"label": "Support Needed", "code": "support_needed", "field_type": MT},
                            {"label": "Next Session Date", "code": "next_session_date", "field_type": DT},
                            {"label": "Confidential Notes", "code": "confidential_notes", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
]
