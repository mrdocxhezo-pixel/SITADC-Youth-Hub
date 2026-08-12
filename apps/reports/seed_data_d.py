"""Seed data for Category D — Membership and Volunteer Management templates."""

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

CATEGORY_D_TEMPLATES: list[dict] = [
    {
        "code": "D1",
        "title": "Membership Register",
        "description": "Register of all organization members with personal and membership details.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Member Information",
                "code": "member-info",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Personal Details",
                        "code": "personal-details",
                        "fields": [
                            {"label": "Full Name", "code": "full_name", "field_type": T, "required": True},
                            {"label": "Gender", "code": "gender", "field_type": DD, "options": ["Male", "Female", "Other", "Prefer not to say"], "required": True},
                            {"label": "Date of Birth", "code": "date_of_birth", "field_type": DT},
                            {"label": "Phone Number", "code": "phone_number", "field_type": T, "required": True},
                            {"label": "Email Address", "code": "email_address", "field_type": T},
                            {"label": "Physical Address", "code": "physical_address", "field_type": MT},
                            {"label": "Photo", "code": "photo", "field_type": IMG},
                        ],
                    },
                    {
                        "name": "Membership Details",
                        "code": "membership-details",
                        "fields": [
                            {"label": "Member Number", "code": "member_number", "field_type": T, "required": True},
                            {"label": "Membership Type", "code": "membership_type", "field_type": DD, "options": ["Full", "Associate", "Honorary", "Student", "Youth"], "required": True},
                            {"label": "Date of Joining", "code": "date_of_joining", "field_type": DT, "required": True},
                            {"label": "Chapter", "code": "chapter", "field_type": T},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Active", "Inactive", "Suspended", "Withdrawn"], "required": True},
                            {"label": "Emergency Contact", "code": "emergency_contact", "field_type": T},
                            {"label": "Skills", "code": "skills", "field_type": MT},
                            {"label": "ID Document", "code": "id_document", "field_type": DOC},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "D2",
        "title": "Volunteer Register",
        "description": "Register of all volunteers with personal, skills and deployment details.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Volunteer Information",
                "code": "volunteer-info",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Personal Details",
                        "code": "personal-details",
                        "fields": [
                            {"label": "Full Name", "code": "full_name", "field_type": T, "required": True},
                            {"label": "Gender", "code": "gender", "field_type": DD, "options": ["Male", "Female", "Other"], "required": True},
                            {"label": "Date of Birth", "code": "date_of_birth", "field_type": DT},
                            {"label": "Phone Number", "code": "phone_number", "field_type": T, "required": True},
                            {"label": "Email Address", "code": "email_address", "field_type": T},
                            {"label": "Physical Address", "code": "physical_address", "field_type": MT},
                            {"label": "Photo", "code": "photo", "field_type": IMG},
                        ],
                    },
                    {
                        "name": "Volunteer Details",
                        "code": "volunteer-details",
                        "fields": [
                            {"label": "Volunteer Number", "code": "volunteer_number", "field_type": T, "required": True},
                            {"label": "Date Registered", "code": "date_registered", "field_type": DT, "required": True},
                            {"label": "Availability", "code": "availability", "field_type": DD, "options": ["Full Time", "Part Time", "Weekends", "Flexible"]},
                            {"label": "Skills", "code": "skills", "field_type": MT},
                            {"label": "Interests", "code": "interests", "field_type": MT},
                            {"label": "Preferred Programs", "code": "preferred_programs", "field_type": MT},
                            {"label": "Reference Contact", "code": "reference_contact", "field_type": T},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Active", "Inactive", "On Leave", "Exited"], "required": True},
                            {"label": "ID Document", "code": "id_document", "field_type": DOC},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "D3",
        "title": "Membership Growth Report",
        "description": "Report on membership growth trends and analysis.",
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
                "name": "Growth Metrics",
                "code": "growth-metrics",
                "groups": [
                    {
                        "name": "Metrics",
                        "code": "metrics",
                        "fields": [
                            {"label": "Opening Membership", "code": "opening_membership", "field_type": INT, "required": True},
                            {"label": "New Members", "code": "new_members", "field_type": INT, "required": True},
                            {"label": "Withdrawn Members", "code": "withdrawn_members", "field_type": INT},
                            {"label": "Suspended Members", "code": "suspended_members", "field_type": INT},
                            {"label": "Closing Membership", "code": "closing_membership", "field_type": INT, "is_calculated": True, "formula": "opening_membership + new_members - withdrawn_members"},
                            {"label": "Growth Rate", "code": "growth_rate", "field_type": PCT, "is_calculated": True, "formula": "new_members / opening_membership * 100"},
                            {"label": "Retention Rate", "code": "retention_rate", "field_type": PCT, "is_calculated": True, "formula": "(closing_membership / opening_membership) * 100"},
                        ],
                    }
                ],
            },
            {
                "name": "Analysis",
                "code": "analysis",
                "groups": [
                    {
                        "name": "Analysis",
                        "code": "analysis",
                        "fields": [
                            {"label": "Growth Trends", "code": "growth_trends", "field_type": RT},
                            {"label": "Challenges", "code": "challenges", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "D4",
        "title": "Volunteer Recruitment Report",
        "description": "Report on volunteer recruitment activities and outcomes.",
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
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Recruitment Activities",
                "code": "recruitment-activities",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Activity",
                        "code": "activity",
                        "fields": [
                            {"label": "Activity Type", "code": "activity_type", "field_type": DD, "options": ["Job Fair", "University Outreach", "Social Media", "Community", "Referral", "Other"], "required": True},
                            {"label": "Date", "code": "date", "field_type": DT, "required": True},
                            {"label": "Description", "code": "description", "field_type": MT},
                            {"label": "Applications Received", "code": "applications_received", "field_type": INT},
                            {"label": "Qualified Candidates", "code": "qualified_candidates", "field_type": INT},
                            {"label": "Photos", "code": "photos", "field_type": IMG, "is_repeatable": True},
                        ],
                    }
                ],
            },
            {
                "name": "Recruitment Summary",
                "code": "recruitment-summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Total Applications", "code": "total_applications", "field_type": INT, "is_calculated": True, "formula": "sum(applications_received)"},
                            {"label": "Total Recruited", "code": "total_recruited", "field_type": INT},
                            {"label": "Conversion Rate", "code": "conversion_rate", "field_type": PCT, "is_calculated": True, "formula": "total_recruited / total_applications * 100"},
                            {"label": "Recruitment Challenges", "code": "recruitment_challenges", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "D5",
        "title": "Volunteer Deployment Report",
        "description": "Report on volunteer deployment across programs and activities.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Reporting Month", "code": "reporting_month", "field_type": DT, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Deployment Details",
                "code": "deployment-details",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Deployment",
                        "code": "deployment",
                        "fields": [
                            {"label": "Volunteer Name", "code": "volunteer_name", "field_type": T, "required": True},
                            {"label": "Program", "code": "program", "field_type": T, "required": True},
                            {"label": "Role", "code": "role", "field_type": T, "required": True},
                            {"label": "Location", "code": "location", "field_type": T},
                            {"label": "Start Date", "code": "start_date", "field_type": DT},
                            {"label": "End Date", "code": "end_date", "field_type": DT},
                            {"label": "Hours Contributed", "code": "hours_contributed", "field_type": DEC},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Active", "Completed", "Withdrawn"]},
                        ],
                    }
                ],
            },
            {
                "name": "Deployment Summary",
                "code": "deployment-summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Total Active Volunteers", "code": "total_active", "field_type": INT},
                            {"label": "Total Hours", "code": "total_hours", "field_type": DEC, "is_calculated": True, "formula": "sum(hours_contributed)"},
                            {"label": "Programs Covered", "code": "programs_covered", "field_type": INT},
                            {"label": "Summary Notes", "code": "summary_notes", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "D6",
        "title": "Volunteer Attendance Report",
        "description": "Report on volunteer attendance at activities and events.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Reporting Month", "code": "reporting_month", "field_type": DT, "required": True},
                            {"label": "Program", "code": "program", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Attendance Records",
                "code": "attendance-records",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Record",
                        "code": "record",
                        "fields": [
                            {"label": "Volunteer Name", "code": "volunteer_name", "field_type": T, "required": True},
                            {"label": "Activity Date", "code": "activity_date", "field_type": DT, "required": True},
                            {"label": "Activity Name", "code": "activity_name", "field_type": T, "required": True},
                            {"label": "Attendance Status", "code": "attendance_status", "field_type": DD, "options": ["Present", "Absent", "Late", "Excused"], "required": True},
                            {"label": "Hours", "code": "hours", "field_type": DEC},
                            {"label": "Remarks", "code": "remarks", "field_type": MT},
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
                            {"label": "Total Volunteers", "code": "total_volunteers", "field_type": INT},
                            {"label": "Average Attendance Rate", "code": "avg_attendance_rate", "field_type": PCT, "is_calculated": True, "formula": "count(status=Present) / count(total) * 100"},
                            {"label": "Total Hours", "code": "total_hours", "field_type": DEC, "is_calculated": True, "formula": "sum(hours)"},
                            {"label": "Notes", "code": "notes", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "D7",
        "title": "Volunteer Performance Report",
        "description": "Report on volunteer performance evaluation and assessment.",
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
                            {"label": "Evaluator", "code": "evaluator", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Performance Evaluations",
                "code": "performance-evaluations",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Volunteer",
                        "code": "volunteer",
                        "fields": [
                            {"label": "Volunteer Name", "code": "volunteer_name", "field_type": T, "required": True},
                            {"label": "Role", "code": "role", "field_type": T},
                            {"label": "Reliability", "code": "reliability", "field_type": DD, "options": ["Excellent", "Good", "Average", "Poor"]},
                            {"label": "Communication", "code": "communication", "field_type": DD, "options": ["Excellent", "Good", "Average", "Poor"]},
                            {"label": "Teamwork", "code": "teamwork", "field_type": DD, "options": ["Excellent", "Good", "Average", "Poor"]},
                            {"label": "Task Completion", "code": "task_completion", "field_type": DD, "options": ["Excellent", "Good", "Average", "Poor"]},
                            {"label": "Overall Rating", "code": "overall_rating", "field_type": DD, "options": ["Outstanding", "Exceeds Expectations", "Meets Expectations", "Needs Improvement"]},
                            {"label": "Achievements", "code": "achievements", "field_type": MT},
                            {"label": "Areas for Improvement", "code": "improvement_areas", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "D8",
        "title": "Volunteer Recognition Report",
        "description": "Report on volunteer recognition, awards and appreciation activities.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Reporting Year", "code": "reporting_year", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Recognition Events",
                "code": "recognition-events",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Event",
                        "code": "event",
                        "fields": [
                            {"label": "Event Name", "code": "event_name", "field_type": T, "required": True},
                            {"label": "Event Date", "code": "event_date", "field_type": DT, "required": True},
                            {"label": "Description", "code": "description", "field_type": MT},
                            {"label": "Number Recognized", "code": "number_recognized", "field_type": INT},
                            {"label": "Photos", "code": "photos", "field_type": IMG, "is_repeatable": True},
                        ],
                    }
                ],
            },
            {
                "name": "Awards",
                "code": "awards",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Award",
                        "code": "award",
                        "fields": [
                            {"label": "Volunteer Name", "code": "volunteer_name", "field_type": T, "required": True},
                            {"label": "Award Category", "code": "award_category", "field_type": DD, "options": ["Service Excellence", "Innovation", "Leadership", "Team Spirit", "Community Impact", "Most Improved", "Other"], "required": True},
                            {"label": "Award Title", "code": "award_title", "field_type": T, "required": True},
                            {"label": "Justification", "code": "justification", "field_type": RT, "required": True},
                            {"label": "Certificate", "code": "certificate", "field_type": DOC},
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
                            {"label": "Total Hours Contributed", "code": "total_hours", "field_type": DEC},
                            {"label": "Total Volunteers Recognized", "code": "total_recognized", "field_type": INT, "is_calculated": True, "formula": "sum(number_recognized)"},
                            {"label": "Impact Summary", "code": "impact_summary", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "D9",
        "title": "Volunteer Exit Report",
        "description": "Report capturing details when a volunteer exits the organization.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Volunteer Details",
                "code": "volunteer-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Volunteer Name", "code": "volunteer_name", "field_type": T, "required": True},
                            {"label": "Volunteer Number", "code": "volunteer_number", "field_type": T, "required": True},
                            {"label": "Date of Joining", "code": "date_of_joining", "field_type": DT},
                            {"label": "Date of Exit", "code": "date_of_exit", "field_type": DT, "required": True},
                            {"label": "Reason for Exit", "code": "reason_for_exit", "field_type": DD, "options": ["Personal", "Relocation", "Employment", "Health", "Dissatisfaction", "Completed Term", "Other"], "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Exit Interview",
                "code": "exit-interview",
                "groups": [
                    {
                        "name": "Interview",
                        "code": "interview",
                        "fields": [
                            {"label": "Satisfaction Level", "code": "satisfaction_level", "field_type": DD, "options": ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"]},
                            {"label": "Would Recommend", "code": "would_recommend", "field_type": CB},
                            {"label": "What Did You Enjoy Most", "code": "enjoy_most", "field_type": MT},
                            {"label": "What Could Be Improved", "code": "improvement_suggestions", "field_type": MT},
                            {"label": "Overall Experience", "code": "overall_experience", "field_type": RT},
                        ],
                    }
                ],
            },
            {
                "name": "Handover",
                "code": "handover",
                "groups": [
                    {
                        "name": "Handover",
                        "code": "handover",
                        "fields": [
                            {"label": "Tasks Handed Over", "code": "tasks_handed_over", "field_type": MT},
                            {"label": "Assets Returned", "code": "assets_returned", "field_type": CB},
                            {"label": "Outstanding Issues", "code": "outstanding_issues", "field_type": MT},
                            {"label": "Approved By", "code": "approved_by", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "D10",
        "title": "Membership Retention Report",
        "description": "Report on membership retention rates and strategies.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Reporting Year", "code": "reporting_year", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Retention Metrics",
                "code": "retention-metrics",
                "groups": [
                    {
                        "name": "Metrics",
                        "code": "metrics",
                        "fields": [
                            {"label": "Members at Start", "code": "members_start", "field_type": INT, "required": True},
                            {"label": "New Members", "code": "new_members", "field_type": INT},
                            {"label": "Members Retained", "code": "members_retained", "field_type": INT, "required": True},
                            {"label": "Members Lost", "code": "members_lost", "field_type": INT},
                            {"label": "Retention Rate", "code": "retention_rate", "field_type": PCT, "is_calculated": True, "formula": "members_retained / (members_start + new_members) * 100"},
                            {"label": "Attrition Rate", "code": "attrition_rate", "field_type": PCT, "is_calculated": True, "formula": "members_lost / (members_start + new_members) * 100"},
                        ],
                    }
                ],
            },
            {
                "name": "Analysis",
                "code": "analysis",
                "groups": [
                    {
                        "name": "Analysis",
                        "code": "analysis",
                        "fields": [
                            {"label": "Reasons for Attrition", "code": "attrition_reasons", "field_type": MT},
                            {"label": "Retention Strategies", "code": "retention_strategies", "field_type": RT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "D11",
        "title": "Capacity Building Report",
        "description": "Report on capacity building activities for members and volunteers.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Reporting Year", "code": "reporting_year", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
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
                        "name": "Training",
                        "code": "training",
                        "fields": [
                            {"label": "Training Title", "code": "training_title", "field_type": T, "required": True},
                            {"label": "Training Type", "code": "training_type", "field_type": DD, "options": ["Workshop", "Seminar", "Online Course", "Mentorship", "On-the-Job", "Other"], "required": True},
                            {"label": "Date", "code": "date", "field_type": DT, "required": True},
                            {"label": "Duration", "code": "duration", "field_type": T},
                            {"label": "Participants", "code": "participants", "field_type": INT},
                            {"label": "Outcome", "code": "outcome", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Skills Assessment",
                "code": "skills-assessment",
                "groups": [
                    {
                        "name": "Assessment",
                        "code": "assessment",
                        "fields": [
                            {"label": "Skills Gained", "code": "skills_gained", "field_type": MT},
                            {"label": "Capacity Improvement", "code": "capacity_improvement", "field_type": RT},
                            {"label": "Gaps Identified", "code": "gaps_identified", "field_type": MT},
                            {"label": "Next Steps", "code": "next_steps", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "D12",
        "title": "Skills Inventory Report",
        "description": "Inventory of skills available among members and volunteers.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Reporting Year", "code": "reporting_year", "field_type": T, "required": True},
                            {"label": "Total Persons Surveyed", "code": "total_surveyed", "field_type": INT},
                        ],
                    }
                ],
            },
            {
                "name": "Skills Records",
                "code": "skills-records",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Person",
                        "code": "person",
                        "fields": [
                            {"label": "Name", "code": "name", "field_type": T, "required": True},
                            {"label": "Role", "code": "role", "field_type": DD, "options": ["Member", "Volunteer", "Staff"]},
                            {"label": "Technical Skills", "code": "technical_skills", "field_type": MT},
                            {"label": "Soft Skills", "code": "soft_skills", "field_type": MT},
                            {"label": "Languages", "code": "languages", "field_type": MT},
                            {"label": "Certifications", "code": "certifications", "field_type": MT},
                            {"label": "Proficiency Level", "code": "proficiency_level", "field_type": DD, "options": ["Expert", "Advanced", "Intermediate", "Beginner"]},
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
                            {"label": "Top Skills Available", "code": "top_skills", "field_type": MT},
                            {"label": "Skills Gaps", "code": "skills_gaps", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
]
