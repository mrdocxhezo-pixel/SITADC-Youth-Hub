"""Seed data for Category E — MEAL templates."""

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

CATEGORY_E_TEMPLATES: list[dict] = [
    {
        "code": "E1",
        "title": "Results Framework Report",
        "description": "Report on the results framework including goal, outcomes, outputs and indicators.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Framework Info",
                "code": "framework-info",
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
                "name": "Goal",
                "code": "goal",
                "groups": [
                    {
                        "name": "Goal",
                        "code": "goal",
                        "fields": [
                            {"label": "Goal Statement", "code": "goal_statement", "field_type": RT, "required": True},
                            {"label": "Goal Indicator", "code": "goal_indicator", "field_type": T},
                            {"label": "Baseline", "code": "baseline", "field_type": DEC},
                            {"label": "Target", "code": "target", "field_type": DEC},
                            {"label": "Actual", "code": "actual", "field_type": DEC},
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
                            {"label": "Outcome Indicator", "code": "outcome_indicator", "field_type": T, "required": True},
                            {"label": "Baseline", "code": "baseline", "field_type": DEC},
                            {"label": "Annual Target", "code": "annual_target", "field_type": DEC},
                            {"label": "Actual", "code": "actual", "field_type": DEC},
                            {"label": "Achievement", "code": "achievement", "field_type": PCT, "is_calculated": True, "formula": "actual / annual_target * 100"},
                        ],
                    }
                ],
            },
            {
                "name": "Outputs",
                "code": "outputs",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Output",
                        "code": "output",
                        "fields": [
                            {"label": "Output Statement", "code": "output_statement", "field_type": T, "required": True},
                            {"label": "Output Indicator", "code": "output_indicator", "field_type": T, "required": True},
                            {"label": "Target", "code": "target", "field_type": DEC},
                            {"label": "Actual", "code": "actual", "field_type": DEC},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["On Track", "Partially Met", "Not Met"]},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E2",
        "title": "Indicator Performance Report",
        "description": "Report on performance of individual indicators against targets.",
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
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Indicator Performance",
                "code": "indicator-performance",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Indicator",
                        "code": "indicator",
                        "fields": [
                            {"label": "Indicator Code", "code": "indicator_code", "field_type": T, "required": True},
                            {"label": "Indicator Description", "code": "indicator_description", "field_type": MT, "required": True},
                            {"label": "Data Source", "code": "data_source", "field_type": T},
                            {"label": "Frequency", "code": "frequency", "field_type": DD, "options": ["Daily", "Weekly", "Monthly", "Quarterly", "Annually"]},
                            {"label": "Baseline", "code": "baseline", "field_type": DEC},
                            {"label": "Quarter Target", "code": "quarter_target", "field_type": DEC},
                            {"label": "Actual Achievement", "code": "actual_achievement", "field_type": DEC},
                            {"label": "Achievement Rate", "code": "achievement_rate", "field_type": PCT, "is_calculated": True, "formula": "actual_achievement / quarter_target * 100"},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["On Track", "Behind", "Ahead", "Not Reported"]},
                            {"label": "Comments", "code": "comments", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E3",
        "title": "Monitoring Visit Report",
        "description": "Report from field monitoring visits to program sites.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Visit Details",
                "code": "visit-details",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Visit Date", "code": "visit_date", "field_type": DT, "required": True},
                            {"label": "Site Location", "code": "site_location", "field_type": T, "required": True},
                            {"label": "Monitor Name", "code": "monitor_name", "field_type": T, "required": True},
                            {"label": "Activities Observed", "code": "activities_observed", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Findings",
                "code": "findings",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Finding",
                        "code": "finding",
                        "fields": [
                            {"label": "Area", "code": "area", "field_type": DD, "options": ["Implementation Quality", "Beneficiary Participation", "Record Keeping", "Resource Management", "Safety", "Compliance", "Other"], "required": True},
                            {"label": "Observation", "code": "observation", "field_type": MT, "required": True},
                            {"label": "Rating", "code": "rating", "field_type": DD, "options": ["Excellent", "Good", "Satisfactory", "Needs Improvement", "Poor"]},
                            {"label": "Evidence", "code": "evidence", "field_type": IMG, "is_repeatable": True},
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
                            {"label": "Key Findings Summary", "code": "findings_summary", "field_type": RT, "required": True},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT, "required": True},
                            {"label": "Follow-up Actions", "code": "followup_actions", "field_type": MT},
                            {"label": "Next Visit Date", "code": "next_visit_date", "field_type": DT},
                            {"label": "Signature", "code": "signature", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E4",
        "title": "Data Collection Report",
        "description": "Report on data collection activities, tools and data quality.",
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
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Data Collector", "code": "data_collector", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Collection Activities",
                "code": "collection-activities",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Activity",
                        "code": "activity",
                        "fields": [
                            {"label": "Data Type", "code": "data_type", "field_type": T, "required": True},
                            {"label": "Collection Method", "code": "collection_method", "field_type": DD, "options": ["Survey", "Interview", "Focus Group", "Observation", "Document Review", "Other"], "required": True},
                            {"label": "Tool Used", "code": "tool_used", "field_type": T},
                            {"label": "Sample Size", "code": "sample_size", "field_type": INT},
                            {"label": "Collection Date", "code": "collection_date", "field_type": DT},
                            {"label": "Locations", "code": "locations", "field_type": MT},
                            {"label": "Response Rate", "code": "response_rate", "field_type": PCT},
                        ],
                    }
                ],
            },
            {
                "name": "Data Quality",
                "code": "data-quality",
                "groups": [
                    {
                        "name": "Quality",
                        "code": "quality",
                        "fields": [
                            {"label": "Completeness", "code": "completeness", "field_type": PCT},
                            {"label": "Accuracy", "code": "accuracy", "field_type": PCT},
                            {"label": "Timeliness", "code": "timeliness", "field_type": DD, "options": ["On Time", "Delayed", "Significantly Delayed"]},
                            {"label": "Challenges", "code": "challenges", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E5",
        "title": "Evaluation Report",
        "description": "Comprehensive evaluation report for a program or project.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Evaluation Info",
                "code": "evaluation-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Evaluation Type", "code": "evaluation_type", "field_type": DD, "options": ["Baseline", "Midline", "Endline", "External", "Internal", "Impact"], "required": True},
                            {"label": "Evaluator", "code": "evaluator", "field_type": T, "required": True},
                            {"label": "Evaluation Period", "code": "evaluation_period", "field_type": T, "required": True},
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
                            {"label": "Evaluation Questions", "code": "evaluation_questions", "field_type": MT, "required": True},
                            {"label": "Methodology", "code": "methodology", "field_type": RT, "required": True},
                            {"label": "Data Sources", "code": "data_sources", "field_type": MT},
                            {"label": "Limitations", "code": "limitations", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Findings",
                "code": "findings",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Finding",
                        "code": "finding",
                        "fields": [
                            {"label": "Criterion", "code": "criterion", "field_type": T, "required": True},
                            {"label": "Rating", "code": "rating", "field_type": DD, "options": ["Highly Satisfactory", "Satisfactory", "Partially Satisfactory", "Unsatisfactory"], "required": True},
                            {"label": "Finding", "code": "finding", "field_type": RT, "required": True},
                            {"label": "Evidence", "code": "evidence", "field_type": DOC, "is_repeatable": True},
                        ],
                    }
                ],
            },
            {
                "name": "Conclusions and Recommendations",
                "code": "conclusions-recommendations",
                "groups": [
                    {
                        "name": "Conclusions",
                        "code": "conclusions",
                        "fields": [
                            {"label": "Key Conclusions", "code": "key_conclusions", "field_type": RT, "required": True},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT, "required": True},
                            {"label": "Action Plan", "code": "action_plan", "field_type": MT},
                            {"label": "Signed Off By", "code": "signed_off_by", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E6",
        "title": "Baseline Report",
        "description": "Baseline assessment report establishing initial conditions before program implementation.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Baseline Info",
                "code": "baseline-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Assessment Date", "code": "assessment_date", "field_type": DT, "required": True},
                            {"label": "Assessor", "code": "assessor", "field_type": T, "required": True},
                            {"label": "Target Area", "code": "target_area", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Baseline Indicators",
                "code": "baseline-indicators",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Indicator",
                        "code": "indicator",
                        "fields": [
                            {"label": "Indicator", "code": "indicator", "field_type": T, "required": True},
                            {"label": "Data Source", "code": "data_source", "field_type": T},
                            {"label": "Baseline Value", "code": "baseline_value", "field_type": DEC, "required": True},
                            {"label": "Unit", "code": "unit", "field_type": T},
                            {"label": "Methodology", "code": "methodology", "field_type": MT},
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
                            {"label": "Key Findings", "code": "key_findings", "field_type": RT, "required": True},
                            {"label": "Implications", "code": "implications", "field_type": RT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E7",
        "title": "Midline Report",
        "description": "Midline assessment report evaluating progress halfway through program implementation.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Midline Info",
                "code": "midline-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Assessment Date", "code": "assessment_date", "field_type": DT, "required": True},
                            {"label": "Assessor", "code": "assessor", "field_type": T, "required": True},
                            {"label": "Implementation Progress", "code": "implementation_progress", "field_type": PCT},
                        ],
                    }
                ],
            },
            {
                "name": "Progress Against Baseline",
                "code": "progress-baseline",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Indicator",
                        "code": "indicator",
                        "fields": [
                            {"label": "Indicator", "code": "indicator", "field_type": T, "required": True},
                            {"label": "Baseline Value", "code": "baseline_value", "field_type": DEC},
                            {"label": "Midline Value", "code": "midline_value", "field_type": DEC, "required": True},
                            {"label": "Target", "code": "target", "field_type": DEC},
                            {"label": "Progress", "code": "progress", "field_type": PCT, "is_calculated": True, "formula": "(midline_value - baseline_value) / (target - baseline_value) * 100"},
                            {"label": "Analysis", "code": "analysis", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Conclusions",
                "code": "conclusions",
                "groups": [
                    {
                        "name": "Conclusions",
                        "code": "conclusions",
                        "fields": [
                            {"label": "Key Findings", "code": "key_findings", "field_type": RT, "required": True},
                            {"label": "Adjustments Needed", "code": "adjustments_needed", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E8",
        "title": "Endline Report",
        "description": "Endline assessment report evaluating final program outcomes.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Endline Info",
                "code": "endline-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Assessment Date", "code": "assessment_date", "field_type": DT, "required": True},
                            {"label": "Assessor", "code": "assessor", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Final Indicator Values",
                "code": "final-indicators",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Indicator",
                        "code": "indicator",
                        "fields": [
                            {"label": "Indicator", "code": "indicator", "field_type": T, "required": True},
                            {"label": "Baseline", "code": "baseline", "field_type": DEC},
                            {"label": "Midline", "code": "midline", "field_type": DEC},
                            {"label": "Endline", "code": "endline", "field_type": DEC, "required": True},
                            {"label": "Target", "code": "target", "field_type": DEC},
                            {"label": "Achievement", "code": "achievement", "field_type": PCT, "is_calculated": True, "formula": "endline / target * 100"},
                            {"label": "Analysis", "code": "analysis", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Final Assessment",
                "code": "final-assessment",
                "groups": [
                    {
                        "name": "Assessment",
                        "code": "assessment",
                        "fields": [
                            {"label": "Overall Outcome Rating", "code": "overall_rating", "field_type": DD, "options": ["Exceeded", "Met", "Partially Met", "Not Met"]},
                            {"label": "Key Achievements", "code": "key_achievements", "field_type": RT},
                            {"label": "Lessons Learned", "code": "lessons_learned", "field_type": RT},
                            {"label": "Sustainability Assessment", "code": "sustainability", "field_type": RT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E9",
        "title": "Impact Assessment Report",
        "description": "Comprehensive impact assessment report on long-term program effects.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Assessment Info",
                "code": "assessment-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Assessment Period", "code": "assessment_period", "field_type": T, "required": True},
                            {"label": "Assessor", "code": "assessor", "field_type": T, "required": True},
                            {"label": "Methodology", "code": "methodology", "field_type": T},
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
                            {"label": "Evidence", "code": "evidence", "field_type": DOC, "is_repeatable": True},
                            {"label": "Attribution Level", "code": "attribution_level", "field_type": DD, "options": ["Full", "Significant", "Partial", "Minimal", "None"]},
                            {"label": "Sustainability", "code": "sustainability", "field_type": DD, "options": ["High", "Medium", "Low"]},
                        ],
                    }
                ],
            },
            {
                "name": "Conclusions",
                "code": "conclusions",
                "groups": [
                    {
                        "name": "Conclusions",
                        "code": "conclusions",
                        "fields": [
                            {"label": "Overall Impact", "code": "overall_impact", "field_type": RT, "required": True},
                            {"label": "Unintended Impacts", "code": "unintended_impacts", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E10",
        "title": "Outcome Harvesting Report",
        "description": "Report using outcome harvesting methodology to capture changes.",
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
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Collected By", "code": "collected_by", "field_type": T, "required": True},
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
                            {"label": "Outcome Description", "code": "outcome_description", "field_type": MT, "required": True},
                            {"label": "Date Observed", "code": "date_observed", "field_type": DT},
                            {"label": "Who Changed", "code": "who_changed", "field_type": MT, "required": True},
                            {"label": "What Changed", "code": "what_changed", "field_type": RT, "required": True},
                            {"label": "Program Contribution", "code": "program_contribution", "field_type": DD, "options": ["Full", "Significant", "Moderate", "Little", "None"], "required": True},
                            {"label": "Evidence", "code": "evidence", "field_type": DOC, "is_repeatable": True},
                            {"label": "Significance", "code": "significance", "field_type": DD, "options": ["High", "Medium", "Low"]},
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
                            {"label": "Patterns Identified", "code": "patterns", "field_type": RT},
                            {"label": "Lessons Learned", "code": "lessons_learned", "field_type": RT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E11",
        "title": "Data Quality Assessment Report",
        "description": "Assessment of data quality across program data collection systems.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Assessment Info",
                "code": "assessment-info",
                "groups": [
                    {
                        "name": "Details",
                        "code": "details",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Assessment Date", "code": "assessment_date", "field_type": DT, "required": True},
                            {"label": "Assessor", "code": "assessor", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Quality Dimensions",
                "code": "quality-dimensions",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Dimension",
                        "code": "dimension",
                        "fields": [
                            {"label": "Quality Dimension", "code": "quality_dimension", "field_type": DD, "options": ["Completeness", "Accuracy", "Timeliness", "Consistency", "Validity", "Reliability"], "required": True},
                            {"label": "Assessment", "code": "assessment", "field_type": RT, "required": True},
                            {"label": "Score", "code": "score", "field_type": DEC},
                            {"label": "Evidence", "code": "evidence", "field_type": DOC, "is_repeatable": True},
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
                            {"label": "Overall Data Quality Score", "code": "overall_score", "field_type": DEC},
                            {"label": "Strengths", "code": "strengths", "field_type": MT},
                            {"label": "Weaknesses", "code": "weaknesses", "field_type": MT},
                            {"label": "Action Plan", "code": "action_plan", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E12",
        "title": "Organizational Dashboard",
        "description": "Dashboard report summarizing key organizational performance metrics.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Dashboard Info",
                "code": "dashboard-info",
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
                "name": "Key Metrics",
                "code": "key-metrics",
                "groups": [
                    {
                        "name": "Metrics",
                        "code": "metrics",
                        "fields": [
                            {"label": "Total Beneficiaries", "code": "total_beneficiaries", "field_type": INT},
                            {"label": "Active Programs", "code": "active_programs", "field_type": INT},
                            {"label": "Active Volunteers", "code": "active_volunteers", "field_type": INT},
                            {"label": "Budget Utilization", "code": "budget_utilization", "field_type": PCT},
                            {"label": "Reports Submitted", "code": "reports_submitted", "field_type": INT},
                            {"label": "Open Issues", "code": "open_issues", "field_type": INT},
                        ],
                    }
                ],
            },
            {
                "name": "Program Performance",
                "code": "program-performance",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Program",
                        "code": "program",
                        "fields": [
                            {"label": "Program Name", "code": "program_name", "field_type": T, "required": True},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Green", "Yellow", "Red"]},
                            {"label": "Completion", "code": "completion", "field_type": PCT},
                            {"label": "Notes", "code": "notes", "field_type": MT},
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
                            {"label": "Critical Alerts", "code": "critical_alerts", "field_type": MT},
                            {"label": "Action Required", "code": "action_required", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E13",
        "title": "Performance Scorecard",
        "description": "Scorecard tracking organizational performance against strategic targets.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Scorecard Info",
                "code": "scorecard-info",
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
                "name": "Performance Areas",
                "code": "performance-areas",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Area",
                        "code": "area",
                        "fields": [
                            {"label": "Performance Area", "code": "performance_area", "field_type": T, "required": True},
                            {"label": "Indicator", "code": "indicator", "field_type": T, "required": True},
                            {"label": "Target", "code": "target", "field_type": T},
                            {"label": "Actual", "code": "actual", "field_type": T},
                            {"label": "Achievement", "code": "achievement", "field_type": PCT, "is_calculated": True},
                            {"label": "Rating", "code": "rating", "field_type": DD, "options": ["Exceeds", "Meets", "Partially Meets", "Does Not Meet"]},
                            {"label": "Comments", "code": "comments", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Overall",
                "code": "overall",
                "groups": [
                    {
                        "name": "Overall",
                        "code": "overall",
                        "fields": [
                            {"label": "Overall Performance Rating", "code": "overall_rating", "field_type": DD, "options": ["Exceeds", "Meets", "Partially Meets", "Does Not Meet"]},
                            {"label": "Summary", "code": "summary", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E14",
        "title": "Learning Report",
        "description": "Report capturing organizational learning and knowledge generation.",
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
                "name": "Learning Areas",
                "code": "learning-areas",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Learning",
                        "code": "learning",
                        "fields": [
                            {"label": "Learning Area", "code": "learning_area", "field_type": DD, "options": ["Technical", "Management", "Financial", "Partnerships", "Community", "Innovation", "Other"], "required": True},
                            {"label": "Learning Description", "code": "learning_description", "field_type": RT, "required": True},
                            {"label": "Source", "code": "source", "field_type": T},
                            {"label": "Applicability", "code": "applicability", "field_type": MT},
                            {"label": "Action Taken", "code": "action_taken", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Knowledge Products",
                "code": "knowledge-products",
                "groups": [
                    {
                        "name": "Products",
                        "code": "products",
                        "fields": [
                            {"label": "Products Developed", "code": "products_developed", "field_type": MT},
                            {"label": "Knowledge Sharing Activities", "code": "sharing_activities", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "E15",
        "title": "Best Practices Report",
        "description": "Report documenting best practices identified through program implementation.",
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
                "name": "Best Practices",
                "code": "best-practices",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Practice",
                        "code": "practice",
                        "fields": [
                            {"label": "Practice Title", "code": "practice_title", "field_type": T, "required": True},
                            {"label": "Program Area", "code": "program_area", "field_type": T},
                            {"label": "Description", "code": "description", "field_type": RT, "required": True},
                            {"label": "Evidence of Effectiveness", "code": "evidence", "field_type": DOC, "is_repeatable": True},
                            {"label": "Replicability", "code": "replicability", "field_type": DD, "options": ["Highly Replicable", "Replicable with Adaptation", "Context Specific"]},
                            {"label": "Impact", "code": "impact", "field_type": DD, "options": ["High", "Medium", "Low"]},
                        ],
                    }
                ],
            },
            {
                "name": "Dissemination",
                "code": "dissemination",
                "groups": [
                    {
                        "name": "Dissemination",
                        "code": "dissemination",
                        "fields": [
                            {"label": "Sharing Mechanisms", "code": "sharing_mechanisms", "field_type": MT},
                            {"label": "Recommendations for Scaling", "code": "scaling_recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
]
