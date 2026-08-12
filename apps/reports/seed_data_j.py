"""Seed data for Category J — Research and Innovation templates."""

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

CATEGORY_J_TEMPLATES: list[dict] = [
    {
        "code": "J1",
        "title": "Community Needs Assessment Report",
        "description": "Report assessing community needs, priorities and gaps.",
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
                                "label": "Assessment Title",
                                "code": "assessment_title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Community/Area",
                                "code": "community",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Assessment Date",
                                "code": "assessment_date",
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
                            {
                                "label": "Limitations",
                                "code": "limitations",
                                "field_type": MT,
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
                                "label": "Need Area",
                                "code": "need_area",
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
                                "label": "Priority Level",
                                "code": "priority_level",
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
                                "label": "Current Interventions",
                                "code": "current_interventions",
                                "field_type": MT,
                            },
                            {
                                "label": "Gap Analysis",
                                "code": "gap_analysis",
                                "field_type": MT,
                            },
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
                                "label": "Key Recommendations",
                                "code": "key_recommendations",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Priority Actions",
                                "code": "priority_actions",
                                "field_type": MT,
                            },
                            {
                                "label": "Estimated Resources",
                                "code": "estimated_resources",
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
        "code": "J2",
        "title": "Research Report",
        "description": "Formal research report on a specific topic or issue.",
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
                                "label": "Research Title",
                                "code": "research_title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Researcher(s)",
                                "code": "researchers",
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
                                "label": "Funding Source",
                                "code": "funding_source",
                                "field_type": T,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Research Details",
                "code": "research-details",
                "groups": [
                    {
                        "name": "Research Details",
                        "code": "research-details",
                        "fields": [
                            {
                                "label": "Research Question",
                                "code": "research_question",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Objectives",
                                "code": "objectives",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Methodology",
                                "code": "methodology",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Data Sources",
                                "code": "data_sources",
                                "field_type": MT,
                            },
                            {
                                "label": "Limitations",
                                "code": "limitations",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Findings",
                "code": "findings",
                "groups": [
                    {
                        "name": "Findings",
                        "code": "findings",
                        "fields": [
                            {
                                "label": "Key Findings",
                                "code": "key_findings",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Evidence",
                                "code": "evidence",
                                "field_type": DOC,
                                "is_repeatable": True,
                            },
                            {"label": "Analysis", "code": "analysis", "field_type": RT},
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
                            {
                                "label": "Conclusions",
                                "code": "conclusions",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Recommendations",
                                "code": "recommendations",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Policy Implications",
                                "code": "policy_implications",
                                "field_type": RT,
                            },
                            {
                                "label": "Areas for Further Research",
                                "code": "further_research",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "J3",
        "title": "Innovation Report",
        "description": "Report on innovative practices, pilots and experiments.",
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
                "name": "Innovations",
                "code": "innovations",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Innovations",
                        "code": "innovations",
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
                                    "Pilot",
                                    "Scaling",
                                    "Mainstreamed",
                                    "Discontinued",
                                ],
                            },
                            {"label": "Impact", "code": "impact", "field_type": MT},
                            {
                                "label": "Replicability",
                                "code": "replicability",
                                "field_type": DD,
                                "options": ["High", "Medium", "Low"],
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
                                "formula": "count(innovations)",
                            },
                            {
                                "label": "Successful Innovations",
                                "code": "successful_innovations",
                                "field_type": INT,
                            },
                            {
                                "label": "Lessons Learned",
                                "code": "lessons_learned",
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
        "code": "J4",
        "title": "Policy Brief",
        "description": "Concise policy brief summarizing key issues and recommendations.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Brief Info",
                "code": "brief-info",
                "groups": [
                    {
                        "name": "Brief Info",
                        "code": "brief-info",
                        "fields": [
                            {
                                "label": "Title",
                                "code": "title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Author(s)",
                                "code": "authors",
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
                                "label": "Target Audience",
                                "code": "target_audience",
                                "field_type": T,
                                "required": True,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Content",
                "code": "content",
                "groups": [
                    {
                        "name": "Content",
                        "code": "content",
                        "fields": [
                            {
                                "label": "Executive Summary",
                                "code": "executive_summary",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Background/Context",
                                "code": "background",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Key Issues",
                                "code": "key_issues",
                                "field_type": RT,
                                "required": True,
                            },
                            {"label": "Evidence", "code": "evidence", "field_type": RT},
                            {
                                "label": "Policy Options",
                                "code": "policy_options",
                                "field_type": RT,
                            },
                            {
                                "label": "Recommendations",
                                "code": "recommendations",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Implementation Considerations",
                                "code": "implementation",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Attachments",
                "code": "attachments",
                "groups": [
                    {
                        "name": "Attachments",
                        "code": "attachments",
                        "fields": [
                            {
                                "label": "Supporting Documents",
                                "code": "supporting_docs",
                                "field_type": DOC,
                                "is_repeatable": True,
                            },
                            {
                                "label": "Infographics",
                                "code": "infographics",
                                "field_type": IMG,
                                "is_repeatable": True,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "J5",
        "title": "Case Study",
        "description": "Detailed case study documenting a program or project experience.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Case Study Info",
                "code": "case-study-info",
                "groups": [
                    {
                        "name": "Case Study Info",
                        "code": "case-study-info",
                        "fields": [
                            {
                                "label": "Title",
                                "code": "title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Author(s)",
                                "code": "authors",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Date",
                                "code": "date",
                                "field_type": DT,
                                "required": True,
                            },
                            {"label": "Location", "code": "location", "field_type": T},
                            {
                                "label": "Program/Project",
                                "code": "program_project",
                                "field_type": T,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Narrative",
                "code": "narrative",
                "groups": [
                    {
                        "name": "Narrative",
                        "code": "narrative",
                        "fields": [
                            {
                                "label": "Background",
                                "code": "background",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Challenge/Problem",
                                "code": "challenge",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Intervention/Response",
                                "code": "intervention",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Results/Outcomes",
                                "code": "results",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Lessons Learned",
                                "code": "lessons_learned",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Sustainability",
                                "code": "sustainability",
                                "field_type": RT,
                            },
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
                            {
                                "label": "Photos",
                                "code": "photos",
                                "field_type": IMG,
                                "is_repeatable": True,
                            },
                            {
                                "label": "Documents",
                                "code": "documents",
                                "field_type": DOC,
                                "is_repeatable": True,
                            },
                            {
                                "label": "Testimonials",
                                "code": "testimonials",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "J6",
        "title": "Success Story Report",
        "description": "Report documenting a success story or positive outcome.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Story Info",
                "code": "story-info",
                "groups": [
                    {
                        "name": "Story Info",
                        "code": "story-info",
                        "fields": [
                            {
                                "label": "Title",
                                "code": "title",
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
                                "label": "Program/Project",
                                "code": "program_project",
                                "field_type": T,
                            },
                            {"label": "Location", "code": "location", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Story",
                "code": "story",
                "groups": [
                    {
                        "name": "Story",
                        "code": "story",
                        "fields": [
                            {
                                "label": "Beneficiary Name",
                                "code": "beneficiary_name",
                                "field_type": T,
                            },
                            {
                                "label": "Narrative",
                                "code": "narrative",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Before Situation",
                                "code": "before_situation",
                                "field_type": MT,
                            },
                            {
                                "label": "After Situation",
                                "code": "after_situation",
                                "field_type": MT,
                            },
                            {
                                "label": "Key Factors for Success",
                                "code": "success_factors",
                                "field_type": MT,
                            },
                            {
                                "label": "Quote/Testimonial",
                                "code": "quote",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Media",
                "code": "media",
                "groups": [
                    {
                        "name": "Media",
                        "code": "media",
                        "fields": [
                            {
                                "label": "Photos",
                                "code": "photos",
                                "field_type": IMG,
                                "is_repeatable": True,
                            },
                            {"label": "Video", "code": "video", "field_type": VID},
                            {
                                "label": "Consent Obtained",
                                "code": "consent_obtained",
                                "field_type": CB,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "J7",
        "title": "Knowledge Product Report",
        "description": "Report documenting knowledge products developed and disseminated.",
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
                "name": "Products",
                "code": "products",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Products",
                        "code": "products",
                        "fields": [
                            {
                                "label": "Product Title",
                                "code": "product_title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Type",
                                "code": "type",
                                "field_type": DD,
                                "options": [
                                    "Report",
                                    "Policy Brief",
                                    "Case Study",
                                    "Research Paper",
                                    "Manual",
                                    "Toolkit",
                                    "Video",
                                    "Infographic",
                                    "Newsletter",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {"label": "Author(s)", "code": "authors", "field_type": T},
                            {
                                "label": "Date Published",
                                "code": "date_published",
                                "field_type": DT,
                            },
                            {
                                "label": "Target Audience",
                                "code": "target_audience",
                                "field_type": T,
                            },
                            {
                                "label": "Distribution Channels",
                                "code": "distribution_channels",
                                "field_type": MT,
                            },
                            {
                                "label": "Downloads/Copies",
                                "code": "downloads",
                                "field_type": INT,
                            },
                            {"label": "File", "code": "file", "field_type": DOC},
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
                            {
                                "label": "Total Products",
                                "code": "total_products",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(products)",
                            },
                            {
                                "label": "Total Reach",
                                "code": "total_reach",
                                "field_type": INT,
                            },
                            {
                                "label": "Feedback Received",
                                "code": "feedback_received",
                                "field_type": MT,
                            },
                            {"label": "Impact", "code": "impact", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
]
