"""Seed data for Category P — Organizational Registers templates."""

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

CATEGORY_P_TEMPLATES: list[dict] = [
    {
        "code": "P1",
        "title": "Membership Register",
        "description": "Master register of all organization members.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Members",
                "code": "members",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Members",
                        "code": "members",
                        "fields": [
                            {
                                "label": "Member Number",
                                "code": "member_number",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Full Name",
                                "code": "full_name",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Gender",
                                "code": "gender",
                                "field_type": DD,
                                "options": ["Male", "Female", "Other"],
                                "required": True,
                            },
                            {
                                "label": "Date of Birth",
                                "code": "date_of_birth",
                                "field_type": DT,
                            },
                            {
                                "label": "Phone",
                                "code": "phone",
                                "field_type": T,
                                "required": True,
                            },
                            {"label": "Email", "code": "email", "field_type": T},
                            {"label": "Address", "code": "address", "field_type": MT},
                            {
                                "label": "Membership Type",
                                "code": "membership_type",
                                "field_type": DD,
                                "options": [
                                    "Full",
                                    "Associate",
                                    "Honorary",
                                    "Student",
                                    "Youth",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Date Joined",
                                "code": "date_joined",
                                "field_type": DT,
                                "required": True,
                            },
                            {"label": "Chapter", "code": "chapter", "field_type": T},
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Active",
                                    "Inactive",
                                    "Suspended",
                                    "Withdrawn",
                                ],
                                "required": True,
                            },
                            {"label": "Photo", "code": "photo", "field_type": IMG},
                            {
                                "label": "ID Document",
                                "code": "id_document",
                                "field_type": DOC,
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
                                "label": "Total Members",
                                "code": "total_members",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(members)",
                            },
                            {
                                "label": "Active Members",
                                "code": "active_members",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P2",
        "title": "Volunteer Register",
        "description": "Master register of all volunteers.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Volunteers",
                "code": "volunteers",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Volunteers",
                        "code": "volunteers",
                        "fields": [
                            {
                                "label": "Volunteer Number",
                                "code": "volunteer_number",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Full Name",
                                "code": "full_name",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Gender",
                                "code": "gender",
                                "field_type": DD,
                                "options": ["Male", "Female", "Other"],
                                "required": True,
                            },
                            {
                                "label": "Phone",
                                "code": "phone",
                                "field_type": T,
                                "required": True,
                            },
                            {"label": "Email", "code": "email", "field_type": T},
                            {"label": "Address", "code": "address", "field_type": MT},
                            {
                                "label": "Date Registered",
                                "code": "date_registered",
                                "field_type": DT,
                                "required": True,
                            },
                            {"label": "Skills", "code": "skills", "field_type": MT},
                            {
                                "label": "Availability",
                                "code": "availability",
                                "field_type": DD,
                                "options": [
                                    "Full Time",
                                    "Part Time",
                                    "Weekends",
                                    "Flexible",
                                ],
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": ["Active", "Inactive", "On Leave", "Exited"],
                                "required": True,
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
                                "label": "Total Volunteers",
                                "code": "total_volunteers",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(volunteers)",
                            },
                            {
                                "label": "Active Volunteers",
                                "code": "active_volunteers",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P3",
        "title": "Beneficiary Register",
        "description": "Register of all program beneficiaries.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Beneficiaries",
                "code": "beneficiaries",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Beneficiaries",
                        "code": "beneficiaries",
                        "fields": [
                            {
                                "label": "Beneficiary Number",
                                "code": "beneficiary_number",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Full Name",
                                "code": "full_name",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Gender",
                                "code": "gender",
                                "field_type": DD,
                                "options": ["Male", "Female", "Other"],
                                "required": True,
                            },
                            {
                                "label": "Date of Birth",
                                "code": "date_of_birth",
                                "field_type": DT,
                            },
                            {"label": "Phone", "code": "phone", "field_type": T},
                            {"label": "Address", "code": "address", "field_type": MT},
                            {
                                "label": "Program",
                                "code": "program",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Beneficiary Type",
                                "code": "beneficiary_type",
                                "field_type": DD,
                                "options": ["Direct", "Indirect", "Community"],
                                "required": True,
                            },
                            {
                                "label": "Date Enrolled",
                                "code": "date_enrolled",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Active",
                                    "Completed",
                                    "Withdrawn",
                                    "Transferred",
                                ],
                                "required": True,
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
                                "label": "Total Beneficiaries",
                                "code": "total_beneficiaries",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(beneficiaries)",
                            },
                            {
                                "label": "Active Beneficiaries",
                                "code": "active_beneficiaries",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P4",
        "title": "Training Register",
        "description": "Register of all training sessions conducted.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Training Sessions",
                "code": "training-sessions",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Training Sessions",
                        "code": "training-sessions",
                        "fields": [
                            {
                                "label": "Training Title",
                                "code": "training_title",
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
                                "label": "Trainer",
                                "code": "trainer",
                                "field_type": T,
                                "required": True,
                            },
                            {"label": "Location", "code": "location", "field_type": T},
                            {
                                "label": "Number of Participants",
                                "code": "num_participants",
                                "field_type": INT,
                            },
                            {"label": "Duration", "code": "duration", "field_type": T},
                            {
                                "label": "Training Type",
                                "code": "training_type",
                                "field_type": DD,
                                "options": [
                                    "Workshop",
                                    "Seminar",
                                    "Course",
                                    "Online",
                                    "On-the-Job",
                                    "Other",
                                ],
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": ["Planned", "Completed", "Cancelled"],
                            },
                            {
                                "label": "Materials",
                                "code": "materials",
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
                                "label": "Total Trainings",
                                "code": "total_trainings",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(training_sessions)",
                            },
                            {
                                "label": "Total Participants",
                                "code": "total_participants",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P5",
        "title": "Attendance Register",
        "description": "Register tracking attendance at meetings and activities.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Events",
                "code": "events",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Events",
                        "code": "events",
                        "fields": [
                            {
                                "label": "Event Name",
                                "code": "event_name",
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
                                "label": "Expected Attendance",
                                "code": "expected_attendance",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Attendees",
                "code": "attendees",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Attendees",
                        "code": "attendees",
                        "fields": [
                            {
                                "label": "Name",
                                "code": "name",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Event",
                                "code": "event",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Attendance Status",
                                "code": "attendance_status",
                                "field_type": DD,
                                "options": ["Present", "Absent", "Late", "Excused"],
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
                            {"label": "Remarks", "code": "remarks", "field_type": MT},
                            {
                                "label": "Signature",
                                "code": "signature",
                                "field_type": SIG,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P6",
        "title": "Stakeholder Register",
        "description": "Register of all organizational stakeholders.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Stakeholders",
                "code": "stakeholders",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Stakeholders",
                        "code": "stakeholders",
                        "fields": [
                            {
                                "label": "Stakeholder Name",
                                "code": "stakeholder_name",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Organization",
                                "code": "organization",
                                "field_type": T,
                            },
                            {
                                "label": "Category",
                                "code": "category",
                                "field_type": DD,
                                "options": [
                                    "Government",
                                    "NGO",
                                    "Private Sector",
                                    "Community",
                                    "Academic",
                                    "International",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Contact Person",
                                "code": "contact_person",
                                "field_type": T,
                            },
                            {"label": "Email", "code": "email", "field_type": T},
                            {"label": "Phone", "code": "phone", "field_type": T},
                            {
                                "label": "Interest Level",
                                "code": "interest_level",
                                "field_type": DD,
                                "options": ["High", "Medium", "Low"],
                            },
                            {
                                "label": "Influence Level",
                                "code": "influence_level",
                                "field_type": DD,
                                "options": ["High", "Medium", "Low"],
                            },
                            {
                                "label": "Relationship",
                                "code": "relationship",
                                "field_type": DD,
                                "options": [
                                    "Strong",
                                    "Good",
                                    "Neutral",
                                    "Weak",
                                    "None",
                                ],
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": ["Active", "Inactive"],
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
                                "label": "Total Stakeholders",
                                "code": "total_stakeholders",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(stakeholders)",
                            },
                            {
                                "label": "Active Stakeholders",
                                "code": "active_stakeholders",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P7",
        "title": "Donor Register",
        "description": "Register of all donors and funding partners.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Donors",
                "code": "donors",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Donors",
                        "code": "donors",
                        "fields": [
                            {
                                "label": "Donor Name",
                                "code": "donor_name",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Type",
                                "code": "type",
                                "field_type": DD,
                                "options": [
                                    "Bilateral",
                                    "Multilateral",
                                    "Foundation",
                                    "Corporate",
                                    "Individual",
                                    "Government",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Contact Person",
                                "code": "contact_person",
                                "field_type": T,
                            },
                            {"label": "Email", "code": "email", "field_type": T},
                            {"label": "Phone", "code": "phone", "field_type": T},
                            {"label": "Address", "code": "address", "field_type": MT},
                            {
                                "label": "Total Contributions",
                                "code": "total_contributions",
                                "field_type": DEC,
                            },
                            {
                                "label": "Last Contribution Date",
                                "code": "last_contribution",
                                "field_type": DT,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": ["Active", "Prospect", "Lapsed", "Former"],
                            },
                            {
                                "label": "Relationship Manager",
                                "code": "relationship_manager",
                                "field_type": T,
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
                                "label": "Total Donors",
                                "code": "total_donors",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(donors)",
                            },
                            {
                                "label": "Active Donors",
                                "code": "active_donors",
                                "field_type": INT,
                            },
                            {
                                "label": "Total Contributions",
                                "code": "total_contributions",
                                "field_type": DEC,
                                "is_calculated": True,
                                "formula": "sum(total_contributions)",
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P8",
        "title": "Partner Register",
        "description": "Register of all implementation and technical partners.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Partners",
                "code": "partners",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Partners",
                        "code": "partners",
                        "fields": [
                            {
                                "label": "Partner Name",
                                "code": "partner_name",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Type",
                                "code": "type",
                                "field_type": DD,
                                "options": [
                                    "Implementation",
                                    "Technical",
                                    "Financial",
                                    "Advocacy",
                                    "Research",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Contact Person",
                                "code": "contact_person",
                                "field_type": T,
                            },
                            {"label": "Email", "code": "email", "field_type": T},
                            {"label": "Phone", "code": "phone", "field_type": T},
                            {
                                "label": "MoU Start Date",
                                "code": "mou_start",
                                "field_type": DT,
                            },
                            {
                                "label": "MoU End Date",
                                "code": "mou_end",
                                "field_type": DT,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Active",
                                    "Completed",
                                    "Suspended",
                                    "Terminated",
                                ],
                            },
                            {
                                "label": "Key Contact",
                                "code": "key_contact",
                                "field_type": T,
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
                                "label": "Total Partners",
                                "code": "total_partners",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(partners)",
                            },
                            {
                                "label": "Active Partners",
                                "code": "active_partners",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P9",
        "title": "Asset Register",
        "description": "Register of all organizational assets.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Assets",
                "code": "assets",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Assets",
                        "code": "assets",
                        "fields": [
                            {
                                "label": "Asset Tag",
                                "code": "asset_tag",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Description",
                                "code": "description",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Category",
                                "code": "category",
                                "field_type": DD,
                                "options": [
                                    "Furniture",
                                    "Equipment",
                                    "Vehicle",
                                    "IT",
                                    "Building",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {"label": "Location", "code": "location", "field_type": T},
                            {
                                "label": "Date Acquired",
                                "code": "date_acquired",
                                "field_type": DT,
                            },
                            {
                                "label": "Acquisition Cost",
                                "code": "acquisition_cost",
                                "field_type": DEC,
                                "required": True,
                            },
                            {
                                "label": "Condition",
                                "code": "condition",
                                "field_type": DD,
                                "options": ["Excellent", "Good", "Fair", "Poor"],
                            },
                            {
                                "label": "Assigned To",
                                "code": "assigned_to",
                                "field_type": T,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "In Use",
                                    "In Storage",
                                    "Disposed",
                                    "Under Repair",
                                ],
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
                                "label": "Total Assets",
                                "code": "total_assets",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(assets)",
                            },
                            {
                                "label": "Total Value",
                                "code": "total_value",
                                "field_type": DEC,
                                "is_calculated": True,
                                "formula": "sum(acquisition_cost)",
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P10",
        "title": "Risk Register",
        "description": "Register of organizational risks and mitigation measures.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Risks",
                "code": "risks",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Risks",
                        "code": "risks",
                        "fields": [
                            {
                                "label": "Risk Reference",
                                "code": "risk_ref",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Risk Description",
                                "code": "risk_description",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Category",
                                "code": "category",
                                "field_type": DD,
                                "options": [
                                    "Strategic",
                                    "Operational",
                                    "Financial",
                                    "Compliance",
                                    "Reputational",
                                    "Safety",
                                    "IT",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Likelihood",
                                "code": "likelihood",
                                "field_type": DD,
                                "options": [
                                    "Very High",
                                    "High",
                                    "Medium",
                                    "Low",
                                    "Very Low",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Impact",
                                "code": "impact",
                                "field_type": DD,
                                "options": [
                                    "Very High",
                                    "High",
                                    "Medium",
                                    "Low",
                                    "Very Low",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Risk Level",
                                "code": "risk_level",
                                "field_type": DD,
                                "options": ["Critical", "High", "Medium", "Low"],
                                "required": True,
                            },
                            {
                                "label": "Mitigation Measures",
                                "code": "mitigation",
                                "field_type": MT,
                            },
                            {
                                "label": "Risk Owner",
                                "code": "risk_owner",
                                "field_type": T,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": ["Open", "Mitigated", "Closed", "Accepted"],
                            },
                            {
                                "label": "Review Date",
                                "code": "review_date",
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
                                "label": "Total Risks",
                                "code": "total_risks",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(risks)",
                            },
                            {
                                "label": "Critical Risks",
                                "code": "critical_risks",
                                "field_type": INT,
                            },
                            {
                                "label": "High Risks",
                                "code": "high_risks",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P11",
        "title": "Issue Register",
        "description": "Register of organizational issues requiring attention.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Issues",
                "code": "issues",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Issues",
                        "code": "issues",
                        "fields": [
                            {
                                "label": "Issue Reference",
                                "code": "issue_ref",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Date Raised",
                                "code": "date_raised",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Description",
                                "code": "description",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Category",
                                "code": "category",
                                "field_type": DD,
                                "options": [
                                    "Operational",
                                    "Financial",
                                    "HR",
                                    "Technical",
                                    "Compliance",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Priority",
                                "code": "priority",
                                "field_type": DD,
                                "options": ["Critical", "High", "Medium", "Low"],
                                "required": True,
                            },
                            {
                                "label": "Assigned To",
                                "code": "assigned_to",
                                "field_type": T,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Open",
                                    "In Progress",
                                    "Resolved",
                                    "Closed",
                                    "Escalated",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Resolution",
                                "code": "resolution",
                                "field_type": MT,
                            },
                            {
                                "label": "Date Resolved",
                                "code": "date_resolved",
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
                                "label": "Total Issues",
                                "code": "total_issues",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(issues)",
                            },
                            {
                                "label": "Open Issues",
                                "code": "open_issues",
                                "field_type": INT,
                            },
                            {
                                "label": "Resolved Issues",
                                "code": "resolved_issues",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P12",
        "title": "Complaints Register",
        "description": "Register of all complaints received and resolved.",
        "reporting_frequency": "ONE_OFF",
        "access_restricted": True,
        "sections": [
            {
                "name": "Complaints",
                "code": "complaints",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Complaints",
                        "code": "complaints",
                        "fields": [
                            {
                                "label": "Complaint Reference",
                                "code": "complaint_ref",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Date Received",
                                "code": "date_received",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Source",
                                "code": "source",
                                "field_type": DD,
                                "options": [
                                    "Beneficiary",
                                    "Staff",
                                    "Volunteer",
                                    "Partner",
                                    "Community",
                                    "Anonymous",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Category",
                                "code": "category",
                                "field_type": DD,
                                "options": [
                                    "Service Quality",
                                    "Staff Conduct",
                                    "Program Design",
                                    "Accessibility",
                                    "Discrimination",
                                    "Safety",
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
                                "label": "Severity",
                                "code": "severity",
                                "field_type": DD,
                                "options": ["High", "Medium", "Low"],
                                "required": True,
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
                                    "Closed",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Resolution",
                                "code": "resolution",
                                "field_type": MT,
                            },
                            {
                                "label": "Date Resolved",
                                "code": "date_resolved",
                                "field_type": DT,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "Summary",
                "code": "summary",
                "access_restricted": True,
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {
                                "label": "Total Complaints",
                                "code": "total_complaints",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(complaints)",
                            },
                            {
                                "label": "Resolved Complaints",
                                "code": "resolved_complaints",
                                "field_type": INT,
                            },
                            {
                                "label": "Resolution Rate",
                                "code": "resolution_rate",
                                "field_type": PCT,
                                "is_calculated": True,
                                "formula": "resolved_complaints / total_complaints * 100",
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P13",
        "title": "Action Tracker",
        "description": "Tracker for action items from meetings, reviews and assessments.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Actions",
                "code": "actions",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Actions",
                        "code": "actions",
                        "fields": [
                            {
                                "label": "Action Reference",
                                "code": "action_ref",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Date Identified",
                                "code": "date_identified",
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
                                "label": "Description",
                                "code": "description",
                                "field_type": MT,
                                "required": True,
                            },
                            {
                                "label": "Assigned To",
                                "code": "assigned_to",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Due Date",
                                "code": "due_date",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Priority",
                                "code": "priority",
                                "field_type": DD,
                                "options": ["Critical", "High", "Medium", "Low"],
                                "required": True,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Open",
                                    "In Progress",
                                    "Completed",
                                    "Overdue",
                                    "Cancelled",
                                ],
                                "required": True,
                            },
                            {"label": "Progress", "code": "progress", "field_type": MT},
                            {
                                "label": "Completion Date",
                                "code": "completion_date",
                                "field_type": DT,
                            },
                            {
                                "label": "Evidence",
                                "code": "evidence",
                                "field_type": DOC,
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
                                "label": "Total Actions",
                                "code": "total_actions",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(actions)",
                            },
                            {
                                "label": "Completed Actions",
                                "code": "completed_actions",
                                "field_type": INT,
                            },
                            {
                                "label": "Overdue Actions",
                                "code": "overdue_actions",
                                "field_type": INT,
                            },
                            {
                                "label": "Completion Rate",
                                "code": "completion_rate",
                                "field_type": PCT,
                                "is_calculated": True,
                                "formula": "completed_actions / total_actions * 100",
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P14",
        "title": "Decision Register",
        "description": "Register of key organizational decisions.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Decisions",
                "code": "decisions",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Decisions",
                        "code": "decisions",
                        "fields": [
                            {
                                "label": "Decision Reference",
                                "code": "decision_ref",
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
                                "label": "Meeting/Forum",
                                "code": "meeting_forum",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Decision",
                                "code": "decision",
                                "field_type": RT,
                                "required": True,
                            },
                            {
                                "label": "Rationale",
                                "code": "rationale",
                                "field_type": MT,
                            },
                            {
                                "label": "Made By",
                                "code": "made_by",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Implementation Status",
                                "code": "implementation_status",
                                "field_type": DD,
                                "options": [
                                    "Pending",
                                    "In Progress",
                                    "Implemented",
                                    "Not Implemented",
                                ],
                            },
                            {
                                "label": "Review Date",
                                "code": "review_date",
                                "field_type": DT,
                            },
                            {
                                "label": "Attachments",
                                "code": "attachments",
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
                                "label": "Total Decisions",
                                "code": "total_decisions",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(decisions)",
                            },
                            {
                                "label": "Implemented",
                                "code": "implemented",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P15",
        "title": "Lessons Learned Register",
        "description": "Register of lessons learned from programs and projects.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Lessons",
                "code": "lessons",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Lessons",
                        "code": "lessons",
                        "fields": [
                            {
                                "label": "Lesson Reference",
                                "code": "lesson_ref",
                                "field_type": T,
                                "required": True,
                            },
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
                                "label": "Category",
                                "code": "category",
                                "field_type": DD,
                                "options": [
                                    "Planning",
                                    "Implementation",
                                    "Monitoring",
                                    "Staffing",
                                    "Budget",
                                    "Partnerships",
                                    "Community",
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
                                "label": "Validated",
                                "code": "validated",
                                "field_type": CB,
                            },
                            {"label": "Applied", "code": "applied", "field_type": CB},
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
                                "formula": "count(lessons)",
                            },
                            {
                                "label": "Validated Lessons",
                                "code": "validated_lessons",
                                "field_type": INT,
                            },
                            {
                                "label": "Applied Lessons",
                                "code": "applied_lessons",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P16",
        "title": "Innovation Register",
        "description": "Register of innovations and experiments within the organization.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
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
                                "label": "Innovation Reference",
                                "code": "innovation_ref",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Title",
                                "code": "title",
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
                                "label": "Date Proposed",
                                "code": "date_proposed",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Description",
                                "code": "description",
                                "field_type": RT,
                                "required": True,
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
                                "formula": "count(innovations)",
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
        "code": "P17",
        "title": "Policy Register",
        "description": "Register of all organizational policies and procedures.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Policies",
                "code": "policies",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Policies",
                        "code": "policies",
                        "fields": [
                            {
                                "label": "Policy Title",
                                "code": "policy_title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Policy Number",
                                "code": "policy_number",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Category",
                                "code": "category",
                                "field_type": DD,
                                "options": [
                                    "Governance",
                                    "HR",
                                    "Finance",
                                    "Operations",
                                    "Program",
                                    "Security",
                                    "Safeguarding",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {"label": "Version", "code": "version", "field_type": T},
                            {
                                "label": "Effective Date",
                                "code": "effective_date",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Review Date",
                                "code": "review_date",
                                "field_type": DT,
                            },
                            {"label": "Owner", "code": "owner", "field_type": T},
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Active",
                                    "Under Review",
                                    "Expired",
                                    "Draft",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Policy Document",
                                "code": "policy_document",
                                "field_type": DOC,
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
                                "label": "Total Policies",
                                "code": "total_policies",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(policies)",
                            },
                            {
                                "label": "Active Policies",
                                "code": "active_policies",
                                "field_type": INT,
                            },
                            {
                                "label": "Policies Due for Review",
                                "code": "due_for_review",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P18",
        "title": "Meeting Register",
        "description": "Register of all organizational meetings.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Meetings",
                "code": "meetings",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Meetings",
                        "code": "meetings",
                        "fields": [
                            {
                                "label": "Meeting Title",
                                "code": "meeting_title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Meeting Type",
                                "code": "meeting_type",
                                "field_type": DD,
                                "options": [
                                    "Board",
                                    "Staff",
                                    "Committee",
                                    "Team",
                                    "Annual General",
                                    "Extraordinary",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Date",
                                "code": "date",
                                "field_type": DT,
                                "required": True,
                            },
                            {"label": "Time", "code": "time", "field_type": TM},
                            {"label": "Location", "code": "location", "field_type": T},
                            {
                                "label": "Chairperson",
                                "code": "chairperson",
                                "field_type": T,
                            },
                            {
                                "label": "Minutes Taker",
                                "code": "minutes_taker",
                                "field_type": T,
                            },
                            {
                                "label": "Attendees",
                                "code": "attendees",
                                "field_type": MT,
                            },
                            {
                                "label": "Key Decisions",
                                "code": "key_decisions",
                                "field_type": MT,
                            },
                            {"label": "Minutes", "code": "minutes", "field_type": DOC},
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
                                "label": "Total Meetings",
                                "code": "total_meetings",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(meetings)",
                            },
                            {
                                "label": "Meeting Types",
                                "code": "meeting_types",
                                "field_type": MT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P19",
        "title": "Event Register",
        "description": "Register of all organizational events.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Events",
                "code": "events",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Events",
                        "code": "events",
                        "fields": [
                            {
                                "label": "Event Title",
                                "code": "event_title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Event Type",
                                "code": "event_type",
                                "field_type": DD,
                                "options": [
                                    "Workshop",
                                    "Conference",
                                    "Seminar",
                                    "Training",
                                    "Celebration",
                                    "Outreach",
                                    "Other",
                                ],
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
                                "label": "Organizer",
                                "code": "organizer",
                                "field_type": T,
                            },
                            {
                                "label": "Expected Participants",
                                "code": "expected_participants",
                                "field_type": INT,
                            },
                            {
                                "label": "Actual Participants",
                                "code": "actual_participants",
                                "field_type": INT,
                            },
                            {"label": "Budget", "code": "budget", "field_type": DEC},
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Planned",
                                    "Confirmed",
                                    "Completed",
                                    "Cancelled",
                                ],
                            },
                            {
                                "label": "Photos",
                                "code": "photos",
                                "field_type": IMG,
                                "is_repeatable": True,
                            },
                            {"label": "Report", "code": "report", "field_type": DOC},
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
                                "label": "Total Events",
                                "code": "total_events",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(events)",
                            },
                            {
                                "label": "Completed Events",
                                "code": "completed_events",
                                "field_type": INT,
                            },
                            {
                                "label": "Total Participants",
                                "code": "total_participants",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P20",
        "title": "Media Register",
        "description": "Register of all media coverage and communications.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Media Items",
                "code": "media-items",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Media Items",
                        "code": "media-items",
                        "fields": [
                            {
                                "label": "Title",
                                "code": "title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Media Type",
                                "code": "media_type",
                                "field_type": DD,
                                "options": [
                                    "Print",
                                    "Online",
                                    "Broadcast",
                                    "TV",
                                    "Radio",
                                    "Social Media",
                                    "Other",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Media House",
                                "code": "media_house",
                                "field_type": T,
                            },
                            {
                                "label": "Publication Date",
                                "code": "publication_date",
                                "field_type": DT,
                                "required": True,
                            },
                            {"label": "Reach", "code": "reach", "field_type": INT},
                            {
                                "label": "Sentiment",
                                "code": "sentiment",
                                "field_type": DD,
                                "options": ["Positive", "Neutral", "Negative"],
                            },
                            {"label": "URL", "code": "url", "field_type": T},
                            {
                                "label": "Clipping",
                                "code": "clipping",
                                "field_type": DOC,
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
                                "label": "Total Media Items",
                                "code": "total_media",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(media_items)",
                            },
                            {
                                "label": "Positive Coverage",
                                "code": "positive_coverage",
                                "field_type": INT,
                            },
                            {
                                "label": "Total Reach",
                                "code": "total_reach",
                                "field_type": INT,
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P21",
        "title": "Grant Register",
        "description": "Register of all grants received and managed.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Grants",
                "code": "grants",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Grants",
                        "code": "grants",
                        "fields": [
                            {
                                "label": "Grant Reference",
                                "code": "grant_ref",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Grant Name",
                                "code": "grant_name",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Donor",
                                "code": "donor",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Amount",
                                "code": "amount",
                                "field_type": DEC,
                                "required": True,
                            },
                            {
                                "label": "Start Date",
                                "code": "start_date",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "End Date",
                                "code": "end_date",
                                "field_type": DT,
                                "required": True,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Active",
                                    "Completed",
                                    "Pending",
                                    "Rejected",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Utilized",
                                "code": "utilized",
                                "field_type": DEC,
                            },
                            {
                                "label": "Remaining",
                                "code": "remaining",
                                "field_type": DEC,
                                "is_calculated": True,
                                "formula": "amount - utilized",
                            },
                            {"label": "Project", "code": "project", "field_type": T},
                            {
                                "label": "Agreement",
                                "code": "agreement",
                                "field_type": DOC,
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
                                "label": "Total Grants",
                                "code": "total_grants",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(grants)",
                            },
                            {
                                "label": "Total Value",
                                "code": "total_value",
                                "field_type": DEC,
                                "is_calculated": True,
                                "formula": "sum(amount)",
                            },
                            {
                                "label": "Total Utilized",
                                "code": "total_utilized",
                                "field_type": DEC,
                                "is_calculated": True,
                                "formula": "sum(utilized)",
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "P22",
        "title": "Proposal Register",
        "description": "Register of all proposals submitted or in development.",
        "reporting_frequency": "ONE_OFF",
        "sections": [
            {
                "name": "Proposals",
                "code": "proposals",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Proposals",
                        "code": "proposals",
                        "fields": [
                            {
                                "label": "Proposal Reference",
                                "code": "proposal_ref",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Title",
                                "code": "title",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Donor",
                                "code": "donor",
                                "field_type": T,
                                "required": True,
                            },
                            {
                                "label": "Amount Requested",
                                "code": "amount_requested",
                                "field_type": DEC,
                                "required": True,
                            },
                            {
                                "label": "Submission Date",
                                "code": "submission_date",
                                "field_type": DT,
                            },
                            {
                                "label": "Decision Date",
                                "code": "decision_date",
                                "field_type": DT,
                            },
                            {
                                "label": "Status",
                                "code": "status",
                                "field_type": DD,
                                "options": [
                                    "Draft",
                                    "Submitted",
                                    "Under Review",
                                    "Approved",
                                    "Rejected",
                                    "Cancelled",
                                ],
                                "required": True,
                            },
                            {
                                "label": "Program Area",
                                "code": "program_area",
                                "field_type": T,
                            },
                            {
                                "label": "Lead Writer",
                                "code": "lead_writer",
                                "field_type": T,
                            },
                            {
                                "label": "Proposal Document",
                                "code": "proposal_document",
                                "field_type": DOC,
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
                                "label": "Total Proposals",
                                "code": "total_proposals",
                                "field_type": INT,
                                "is_calculated": True,
                                "formula": "count(proposals)",
                            },
                            {
                                "label": "Approved Proposals",
                                "code": "approved_proposals",
                                "field_type": INT,
                            },
                            {
                                "label": "Total Value",
                                "code": "total_value",
                                "field_type": DEC,
                                "is_calculated": True,
                                "formula": "sum(amount_requested)",
                            },
                        ],
                    }
                ],
            },
        ],
    },
]
