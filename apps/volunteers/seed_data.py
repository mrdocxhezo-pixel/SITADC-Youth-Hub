"""Seed definitions for volunteer skills, interests, and initial records."""

from __future__ import annotations

DEFAULT_SKILLS = [
    {"name": "Community Mobilization", "category": "Community"},
    {"name": "Public Speaking & Facilitation", "category": "Communication"},
    {"name": "Graphic Design & Content Creation", "category": "Media"},
    {"name": "Monitoring & Evaluation (MEAL)", "category": "Technical"},
    {"name": "Project Coordination", "category": "Management"},
    {"name": "Digital Literacy & ICT Training", "category": "IT"},
    {"name": "First Aid & Health Outreach", "category": "Health"},
    {"name": "Financial Literacy & Youth Entrepreneurship", "category": "Finance"},
]

DEFAULT_INTERESTS = [
    "Youth Empowerment",
    "Climate Action & Environment",
    "Digital Skills & Innovation",
    "Community Health & Well-being",
    "Governance & Civic Education",
]

DEFAULT_CATEGORIES = [
    {"code": "COMMUNITY", "name": "Community Volunteer", "sort_order": 10},
    {"code": "STUDENT", "name": "Student Volunteer", "sort_order": 20},
    {"code": "YOUTH", "name": "Youth Volunteer", "sort_order": 30},
    {"code": "PROFESSIONAL", "name": "Professional Volunteer", "sort_order": 40},
    {"code": "TECHNICAL", "name": "Technical Volunteer", "sort_order": 50},
    {"code": "PROGRAM", "name": "Program Volunteer", "sort_order": 60},
    {"code": "EVENT", "name": "Event Volunteer", "sort_order": 70},
    {"code": "FIELD", "name": "Field Volunteer", "sort_order": 80},
    {"code": "REMOTE", "name": "Remote Volunteer", "sort_order": 90},
    {"code": "INTERNATIONAL", "name": "International Volunteer", "sort_order": 100},
]

DEFAULT_TYPES = [
    {"code": "FULL_TIME", "name": "Full-Time Volunteer", "sort_order": 10},
    {"code": "PART_TIME", "name": "Part-Time Volunteer", "sort_order": 20},
    {"code": "PROJECT_BASED", "name": "Project-Based Volunteer", "sort_order": 30},
    {"code": "EVENT", "name": "Event Volunteer", "sort_order": 40},
    {"code": "ONLINE", "name": "Online / Virtual Volunteer", "sort_order": 50},
    {"code": "FIELD", "name": "Field Volunteer", "sort_order": 60},
    {"code": "SPECIALIST", "name": "Specialist Volunteer", "sort_order": 70},
    {"code": "MENTOR", "name": "Mentor", "sort_order": 80},
    {"code": "TRAINER", "name": "Trainer", "sort_order": 90},
    {"code": "ADVISORY", "name": "Advisory Volunteer", "sort_order": 100},
]

DEFAULT_LEVELS = [
    {"code": "NATIONAL", "name": "National Level", "sort_order": 10},
    {"code": "REGIONAL", "name": "Regional Level", "sort_order": 20},
    {"code": "DISTRICT", "name": "District Level", "sort_order": 30},
    {"code": "COMMUNITY", "name": "Community Level", "sort_order": 40},
    {"code": "TEAM", "name": "Team Level", "sort_order": 50},
]


def ensure_default_taxonomies() -> None:
    """Create default configurable taxonomies if they do not exist (idempotent)."""
    from .models import VolunteerCategory, VolunteerLevel, VolunteerType

    for spec in DEFAULT_CATEGORIES:
        VolunteerCategory.objects.get_or_create(
            code=spec["code"],
            defaults={"name": spec["name"], "sort_order": spec["sort_order"]},
        )
    for spec in DEFAULT_TYPES:
        VolunteerType.objects.get_or_create(
            code=spec["code"],
            defaults={"name": spec["name"], "sort_order": spec["sort_order"]},
        )
    for spec in DEFAULT_LEVELS:
        VolunteerLevel.objects.get_or_create(
            code=spec["code"],
            defaults={"name": spec["name"], "sort_order": spec["sort_order"]},
        )
