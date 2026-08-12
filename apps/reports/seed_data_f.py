"""Seed data for Category F — Communication and Information Management templates."""

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

CATEGORY_F_TEMPLATES: list[dict] = [
    {
        "code": "F1",
        "title": "Monthly Communication Report",
        "description": "Report on all communication activities, channels and outcomes for the month.",
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
                "name": "Communication Activities",
                "code": "communication-activities",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Activity",
                        "code": "activity",
                        "fields": [
                            {"label": "Activity Type", "code": "activity_type", "field_type": DD, "options": ["Press Release", "Newsletter", "Social Media", "Website", "Event", "Brochure", "Report", "Other"], "required": True},
                            {"label": "Title", "code": "title", "field_type": T, "required": True},
                            {"label": "Date", "code": "date", "field_type": DT, "required": True},
                            {"label": "Description", "code": "description", "field_type": MT},
                            {"label": "Channel", "code": "channel", "field_type": DD, "options": ["Print", "Digital", "Broadcast", "Social Media", "Website", "Email"]},
                            {"label": "Reach", "code": "reach", "field_type": INT},
                            {"label": "Engagement", "code": "engagement", "field_type": INT},
                            {"label": "Materials", "code": "materials", "field_type": DOC, "is_repeatable": True},
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
                            {"label": "Total Reach", "code": "total_reach", "field_type": INT, "is_calculated": True, "formula": "sum(reach)"},
                            {"label": "Key Achievements", "code": "key_achievements", "field_type": MT},
                            {"label": "Challenges", "code": "challenges", "field_type": MT},
                            {"label": "Next Month Plan", "code": "next_month_plan", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "F2",
        "title": "Social Media Analytics Report",
        "description": "Report on social media performance, engagement and growth metrics.",
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
                "name": "Platform Metrics",
                "code": "platform-metrics",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Platform",
                        "code": "platform",
                        "fields": [
                            {"label": "Platform", "code": "platform", "field_type": DD, "options": ["Facebook", "Twitter", "Instagram", "LinkedIn", "YouTube", "TikTok", "Other"], "required": True},
                            {"label": "Followers Start", "code": "followers_start", "field_type": INT},
                            {"label": "Followers End", "code": "followers_end", "field_type": INT},
                            {"label": "New Followers", "code": "new_followers", "field_type": INT, "is_calculated": True, "formula": "followers_end - followers_start"},
                            {"label": "Posts Published", "code": "posts_published", "field_type": INT},
                            {"label": "Total Reach", "code": "total_reach", "field_type": INT},
                            {"label": "Total Engagement", "code": "total_engagement", "field_type": INT},
                            {"label": "Engagement Rate", "code": "engagement_rate", "field_type": PCT, "is_calculated": True, "formula": "total_engagement / total_reach * 100"},
                            {"label": "Top Post", "code": "top_post", "field_type": MT},
                            {"label": "Link to Report", "code": "link_to_report", "field_type": T},
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
                            {"label": "Key Insights", "code": "key_insights", "field_type": RT},
                            {"label": "Content Themes", "code": "content_themes", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "F3",
        "title": "Website Performance Report",
        "description": "Report on website traffic, user behavior and performance metrics.",
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
                            {"label": "Analytics Tool", "code": "analytics_tool", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Traffic Metrics",
                "code": "traffic-metrics",
                "groups": [
                    {
                        "name": "Traffic",
                        "code": "traffic",
                        "fields": [
                            {"label": "Total Visitors", "code": "total_visitors", "field_type": INT, "required": True},
                            {"label": "Unique Visitors", "code": "unique_visitors", "field_type": INT},
                            {"label": "Page Views", "code": "page_views", "field_type": INT},
                            {"label": "Bounce Rate", "code": "bounce_rate", "field_type": PCT},
                            {"label": "Average Session Duration", "code": "avg_session_duration", "field_type": T},
                            {"label": "New vs Returning", "code": "new_vs_returning", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Top Content",
                "code": "top-content",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Page",
                        "code": "page",
                        "fields": [
                            {"label": "Page Title", "code": "page_title", "field_type": T, "required": True},
                            {"label": "URL", "code": "url", "field_type": T},
                            {"label": "Views", "code": "views", "field_type": INT},
                            {"label": "Unique Views", "code": "unique_views", "field_type": INT},
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
                            {"label": "Key Findings", "code": "key_findings", "field_type": RT},
                            {"label": "SEO Observations", "code": "seo_observations", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "F4",
        "title": "Newsletter Report",
        "description": "Report on newsletter production, distribution and engagement.",
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
                            {"label": "Editor", "code": "editor", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Newsletter Issues",
                "code": "newsletter-issues",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Issue",
                        "code": "issue",
                        "fields": [
                            {"label": "Issue Title", "code": "issue_title", "field_type": T, "required": True},
                            {"label": "Publication Date", "code": "publication_date", "field_type": DT, "required": True},
                            {"label": "Total Subscribers", "code": "total_subscribers", "field_type": INT},
                            {"label": "Emails Sent", "code": "emails_sent", "field_type": INT},
                            {"label": "Open Rate", "code": "open_rate", "field_type": PCT},
                            {"label": "Click Rate", "code": "click_rate", "field_type": PCT},
                            {"label": "Unsubscribe Rate", "code": "unsubscribe_rate", "field_type": PCT},
                            {"label": "Newsletter File", "code": "newsletter_file", "field_type": DOC},
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
                            {"label": "Average Open Rate", "code": "avg_open_rate", "field_type": PCT, "is_calculated": True},
                            {"label": "Average Click Rate", "code": "avg_click_rate", "field_type": PCT, "is_calculated": True},
                            {"label": "Top Stories", "code": "top_stories", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "F5",
        "title": "Media Coverage Report",
        "description": "Report on media coverage, press mentions and media relations.",
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
                "name": "Media Coverage",
                "code": "media-coverage",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Coverage",
                        "code": "coverage",
                        "fields": [
                            {"label": "Media House", "code": "media_house", "field_type": T, "required": True},
                            {"label": "Publication Date", "code": "publication_date", "field_type": DT, "required": True},
                            {"label": "Title", "code": "title", "field_type": T, "required": True},
                            {"label": "Media Type", "code": "media_type", "field_type": DD, "options": ["Print", "Online", "Broadcast", "TV", "Radio", "Podcast"]},
                            {"label": "Reach", "code": "reach", "field_type": INT},
                            {"label": "Sentiment", "code": "sentiment", "field_type": DD, "options": ["Positive", "Neutral", "Negative"]},
                            {"label": "URL", "code": "url", "field_type": T},
                            {"label": "Clipping", "code": "clipping", "field_type": DOC},
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
                            {"label": "Total Mentions", "code": "total_mentions", "field_type": INT, "is_calculated": True, "formula": "count(coverage)"},
                            {"label": "Sentiment Breakdown", "code": "sentiment_breakdown", "field_type": MT},
                            {"label": "Key Themes", "code": "key_themes", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "F6",
        "title": "Public Relations Report",
        "description": "Report on public relations activities and stakeholder engagement.",
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
                            {"label": "PR Manager", "code": "pr_manager", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "PR Activities",
                "code": "pr-activities",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Activity",
                        "code": "activity",
                        "fields": [
                            {"label": "Activity", "code": "activity", "field_type": T, "required": True},
                            {"label": "Date", "code": "date", "field_type": DT, "required": True},
                            {"label": "Type", "code": "type", "field_type": DD, "options": ["Press Conference", "Media Briefing", "Stakeholder Meeting", "Public Event", "Interview", "Other"], "required": True},
                            {"label": "Stakeholders", "code": "stakeholders", "field_type": MT},
                            {"label": "Outcome", "code": "outcome", "field_type": MT},
                            {"label": "Media Coverage", "code": "media_coverage", "field_type": CB},
                            {"label": "Materials", "code": "materials", "field_type": DOC, "is_repeatable": True},
                        ],
                    }
                ],
            },
            {
                "name": "Reputation",
                "code": "reputation",
                "groups": [
                    {
                        "name": "Reputation",
                        "code": "reputation",
                        "fields": [
                            {"label": "Public Perception", "code": "public_perception", "field_type": RT},
                            {"label": "Key Issues", "code": "key_issues", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "F7",
        "title": "Branding Compliance Report",
        "description": "Report on compliance with organizational branding guidelines.",
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
                            {"label": "Auditor", "code": "auditor", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Compliance Areas",
                "code": "compliance-areas",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Area",
                        "code": "area",
                        "fields": [
                            {"label": "Area", "code": "area", "field_type": DD, "options": ["Logo Usage", "Color Scheme", "Typography", "Imagery", "Layout", "Tone of Voice", "Other"], "required": True},
                            {"label": "Material Reviewed", "code": "material_reviewed", "field_type": T, "required": True},
                            {"label": "Compliant", "code": "compliant", "field_type": CB},
                            {"label": "Issues Found", "code": "issues_found", "field_type": MT},
                            {"label": "Corrective Action", "code": "corrective_action", "field_type": MT},
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
                            {"label": "Overall Compliance", "code": "overall_compliance", "field_type": PCT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "F8",
        "title": "Photography and Documentation Report",
        "description": "Report on photographic and video documentation of organizational activities.",
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
                            {"label": "Documentation Officer", "code": "documentation_officer", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Documentation",
                "code": "documentation",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Event",
                        "code": "event",
                        "fields": [
                            {"label": "Event Name", "code": "event_name", "field_type": T, "required": True},
                            {"label": "Date", "code": "date", "field_type": DT, "required": True},
                            {"label": "Location", "code": "location", "field_type": T},
                            {"label": "Photos Taken", "code": "photos_taken", "field_type": INT},
                            {"label": "Photos Selected", "code": "photos_selected", "field_type": INT},
                            {"label": "Videos Taken", "code": "videos_taken", "field_type": INT},
                            {"label": "Key Photos", "code": "key_photos", "field_type": IMG, "is_repeatable": True},
                            {"label": "Key Videos", "code": "key_videos", "field_type": VID, "is_repeatable": True},
                            {"label": "Captions Written", "code": "captions_written", "field_type": CB},
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
                            {"label": "Total Photos", "code": "total_photos", "field_type": INT, "is_calculated": True, "formula": "sum(photos_taken)"},
                            {"label": "Total Videos", "code": "total_videos", "field_type": INT, "is_calculated": True, "formula": "sum(videos_taken)"},
                            {"label": "Storage Location", "code": "storage_location", "field_type": T},
                            {"label": "Notes", "code": "notes", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "F9",
        "title": "Information Management Report",
        "description": "Report on information systems, data management and digital infrastructure.",
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
                            {"label": "IT Manager", "code": "it_manager", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Systems Status",
                "code": "systems-status",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "System",
                        "code": "system",
                        "fields": [
                            {"label": "System Name", "code": "system_name", "field_type": T, "required": True},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Operational", "Degraded", "Down", "Under Maintenance"]},
                            {"label": "Uptime", "code": "uptime", "field_type": PCT},
                            {"label": "Issues", "code": "issues", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Data Management",
                "code": "data-management",
                "groups": [
                    {
                        "name": "Data",
                        "code": "data",
                        "fields": [
                            {"label": "Storage Usage", "code": "storage_usage", "field_type": T},
                            {"label": "Backup Status", "code": "backup_status", "field_type": DD, "options": ["Current", "Overdue", "Failed"]},
                            {"label": "Security Incidents", "code": "security_incidents", "field_type": INT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "F10",
        "title": "Records Management Report",
        "description": "Report on records management, filing systems and document control.",
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
                            {"label": "Records Officer", "code": "records_officer", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Records Summary",
                "code": "records-summary",
                "groups": [
                    {
                        "name": "Records",
                        "code": "records",
                        "fields": [
                            {"label": "Physical Records", "code": "physical_records", "field_type": INT},
                            {"label": "Digital Records", "code": "digital_records", "field_type": INT},
                            {"label": "Records Created", "code": "records_created", "field_type": INT},
                            {"label": "Records Archived", "code": "records_archived", "field_type": INT},
                            {"label": "Records Destroyed", "code": "records_destroyed", "field_type": INT},
                        ],
                    }
                ],
            },
            {
                "name": "Compliance",
                "code": "compliance",
                "groups": [
                    {
                        "name": "Compliance",
                        "code": "compliance",
                        "fields": [
                            {"label": "Retention Policy Compliance", "code": "retention_compliance", "field_type": PCT},
                            {"label": "Filing System Status", "code": "filing_status", "field_type": DD, "options": ["Current", "Partially Current", "Outdated"]},
                            {"label": "Audit Findings", "code": "audit_findings", "field_type": MT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "F11",
        "title": "Knowledge Management Report",
        "description": "Report on knowledge management activities and intellectual capital.",
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
                            {"label": "KM Officer", "code": "km_officer", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Knowledge Products",
                "code": "knowledge-products",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Product",
                        "code": "product",
                        "fields": [
                            {"label": "Product Title", "code": "product_title", "field_type": T, "required": True},
                            {"label": "Type", "code": "type", "field_type": DD, "options": ["Report", "Policy Brief", "Case Study", "Research Paper", "Manual", "Toolkit", "Newsletter", "Other"], "required": True},
                            {"label": "Author", "code": "author", "field_type": T},
                            {"label": "Date Published", "code": "date_published", "field_type": DT},
                            {"label": "Distribution", "code": "distribution", "field_type": INT},
                            {"label": "File", "code": "file", "field_type": DOC},
                        ],
                    }
                ],
            },
            {
                "name": "KM Activities",
                "code": "km-activities",
                "groups": [
                    {
                        "name": "Activities",
                        "code": "activities",
                        "fields": [
                            {"label": "Knowledge Sharing Events", "code": "sharing_events", "field_type": INT},
                            {"label": "Communities of Practice", "code": "cop_count", "field_type": INT},
                            {"label": "Lessons Learned Sessions", "code": "lessons_sessions", "field_type": INT},
                            {"label": "Recommendations", "code": "recommendations", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "F12",
        "title": "Content Calendar Report",
        "description": "Report on content planning, production and publishing schedule.",
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
                            {"label": "Content Manager", "code": "content_manager", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Planned Content",
                "code": "planned-content",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Content",
                        "code": "content",
                        "fields": [
                            {"label": "Title", "code": "title", "field_type": T, "required": True},
                            {"label": "Content Type", "code": "content_type", "field_type": DD, "options": ["Blog Post", "Social Media", "Newsletter", "Video", "Infographic", "Photo Story", "Other"], "required": True},
                            {"label": "Channel", "code": "channel", "field_type": DD, "options": ["Website", "Facebook", "Twitter", "Instagram", "LinkedIn", "Email", "Print"]},
                            {"label": "Planned Date", "code": "planned_date", "field_type": DT},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Draft", "In Review", "Approved", "Published", "Cancelled"]},
                            {"label": "Author", "code": "author", "field_type": T},
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
                            {"label": "Total Planned", "code": "total_planned", "field_type": INT, "is_calculated": True, "formula": "count(content)"},
                            {"label": "Total Published", "code": "total_published", "field_type": INT},
                            {"label": "Completion Rate", "code": "completion_rate", "field_type": PCT, "is_calculated": True, "formula": "total_published / total_planned * 100"},
                            {"label": "Notes", "code": "notes", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
]
