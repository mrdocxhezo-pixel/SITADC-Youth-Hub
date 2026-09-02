"""Forms for the Leadership Management module."""

from django import forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.organizations.constants import UnitType, UnitStatus, PositionStatus
from apps.organizations.models import OrganizationUnit, Position

from .models import (
    CoachingRecord,
    LeadershipAppointment,
    LeadershipAttendance,
    LeadershipProfile,
    MentorshipRecord,
    PerformanceReview,
    SuccessionPlan,
)


class LeadershipProfileForm(forms.ModelForm):
    """Form for creating and editing leadership profiles."""

    class Meta:
        model = LeadershipProfile
        fields = [
            "user",
            "reference_number",
            "profile_photo",
            "national_id",
            "gender",
            "full_name",
            "date_of_birth",
            "phone_number",
            "email",
            "residential_address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "leadership_level",
            "position",
            "organizational_unit",
            "directorate",
            "department",
            "program_technical_management",
            "region",
            "district",
            "community",
            "team",
            "supervisor",
            "biography",
            "qualifications",
            "professional_skills",
            "areas_of_expertise",
            "appointment_date",
            "term_expiry_date",
            "terms_completed",
            "max_terms",
            "term_status",
            "renewal_eligible",
            "renewal_status",
            "status",
        ]
        widgets = {
            "biography": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "qualifications": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
            "professional_skills": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
            "areas_of_expertise": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
            "residential_address": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "national_id": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "appointment_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "term_expiry_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "emergency_contact_name": forms.TextInput(attrs={"class": "form-control"}),
            "emergency_contact_phone": forms.TextInput(attrs={"class": "form-control"}),
            "leadership_level": forms.Select(attrs={"class": "form-select"}),
            "position": forms.Select(attrs={"class": "form-select"}),
            "organizational_unit": forms.Select(attrs={"class": "form-select"}),
            "directorate": forms.Select(attrs={"class": "form-select"}),
            "department": forms.Select(attrs={"class": "form-select"}),
            "program_technical_management": forms.Select(attrs={"class": "form-select"}),
            "region": forms.Select(attrs={"class": "form-select"}),
            "district": forms.Select(attrs={"class": "form-select"}),
            "community": forms.Select(attrs={"class": "form-select"}),
            "team": forms.Select(attrs={"class": "form-select"}),
            "supervisor": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "term_status": forms.Select(attrs={"class": "form-select"}),
            "renewal_status": forms.Select(attrs={"class": "form-select"}),
            "terms_completed": forms.NumberInput(attrs={"class": "form-control"}),
            "max_terms": forms.NumberInput(attrs={"class": "form-control"}),
            "renewal_eligible": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
        labels = {
            "user": _("User Account"),
            "reference_number": _("Leadership Reference Number"),
            "profile_photo": _("Profile Photograph"),
            "national_id": _("National ID / Identification Number"),
            "full_name": _("Full Names"),
            "gender": _("Gender"),
            "date_of_birth": _("Date of Birth"),
            "phone_number": _("Phone Number"),
            "email": _("Email Address"),
            "residential_address": _("Residential Address"),
            "emergency_contact_name": _("Emergency Contact Name"),
            "emergency_contact_phone": _("Emergency Contact Phone"),
            "leadership_level": _("Leadership Level"),
            "position": _("Position (Optional)"),
            "organizational_unit": _("Organizational Unit (Optional)"),
            "directorate": _("Directorate (Optional)"),
            "department": _("Department (Optional)"),
            "program_technical_management": _(
                "Program and Technical Management (Optional)"
            ),
            "region": _("Region (Optional)"),
            "district": _("District (Optional)"),
            "community": _("Community (Optional)"),
            "team": _("Team (Optional)"),
            "supervisor": _("Immediate Supervisor"),
            "biography": _("Biography"),
            "qualifications": _("Qualifications"),
            "professional_skills": _("Professional Skills"),
            "areas_of_expertise": _("Areas of Expertise"),
            "appointment_date": _("Appointment Date"),
            "term_expiry_date": _("Term Expiry Date"),
            "terms_completed": _("Terms Completed"),
            "max_terms": _("Maximum Permitted Terms"),
            "term_status": _("Term Status"),
            "renewal_eligible": _("Renewal Eligible"),
            "renewal_status": _("Renewal Status"),
            "status": _("Status"),
        }
        help_texts = {
            "user": _("Select the user account to link to this leadership profile."),
            "reference_number": _(
                "System-generated immutable reference number. Cannot be changed."
            ),
            "profile_photo": _(
                "Upload a professional profile photograph. Max size: 5MB. "
                "Supported formats: JPEG, PNG."
            ),
            "national_id": _("National identification number or passport number."),
            "gender": _("Gender identification."),
            "full_name": _("Full name of the leader. Updates the linked user's first and last name."),
            "date_of_birth": _("Date of birth for age verification."),
            "phone_number": _("Primary contact phone number."),
            "email": _("Contact email address."),
            "residential_address": _("Full residential address."),
            "emergency_contact_name": _("Name of emergency contact person."),
            "emergency_contact_phone": _("Phone number for emergency contact."),
            "leadership_level": _("The organizational leadership level."),
            "position": _("The specific position title."),
            "organizational_unit": _("The primary organizational unit."),
            "directorate": _("The directorate this leader belongs to."),
            "department": _("The department this leader belongs to."),
            "program_technical_management": _("The program/technical management unit this leader belongs to."),
            "region": _("The region this leader is assigned to."),
            "district": _("The district this leader is assigned to."),
            "community": _("The community this leader is assigned to."),
            "team": _("The team this leader is assigned to."),
            "supervisor": _(
                "The immediate supervisor (reporting line). "
                "A leader cannot supervise themselves."
            ),
            "biography": _("A brief professional biography."),
            "qualifications": _("Educational and professional qualifications."),
            "professional_skills": _("Key professional skills and competencies."),
            "areas_of_expertise": _("Specialized areas of expertise."),
            "appointment_date": _("Date of initial appointment."),
            "term_expiry_date": _("Date when current term expires."),
            "terms_completed": _("Number of completed terms served."),
            "max_terms": _("Maximum number of terms permitted."),
            "term_status": _("Current term status."),
            "renewal_eligible": _("Whether this leader is eligible for term renewal."),
            "renewal_status": _("Current renewal eligibility status."),
            "status": _("Current leadership status."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Reference numbers are system-generated through the centralized
        # ReferenceNumberService, so creating a profile must never require
        # one up front; the model issues it automatically on save().
        self.fields["reference_number"].required = False
        # Make reference_number read-only for existing profiles
        if self.instance and self.instance.pk:
            self.fields["reference_number"].initial = self.instance.reference_number
            self.fields["reference_number"].widget.attrs["readonly"] = True
            self.fields["reference_number"].widget.attrs[
                "class"
            ] = "form-control-plaintext"
# Make user field read-only for existing profiles (linked to user)
        self.fields["user"].widget.attrs["disabled"] = True
        self.fields["user"].widget.attrs["class"] = "form-control-plaintext"
        # Set user field as not required since it's disabled
        self.fields["user"].required = False

        # Populate full_name field from related user when editing
        if self.instance and self.instance.pk and self.instance.user:
            self.fields["full_name"].initial = self.instance.user.get_full_name()

        # Filter OrganizationUnit querysets by unit_type for geographic/organizational fields
        self.fields["directorate"].queryset = OrganizationUnit.objects.filter(
            unit_type=UnitType.DIRECTORATE, status=UnitStatus.ACTIVE
        ).select_related("level")
        self.fields["department"].queryset = OrganizationUnit.objects.filter(
            unit_type=UnitType.DEPARTMENT, status=UnitStatus.ACTIVE
        ).select_related("level")
        self.fields["program_technical_management"].queryset = OrganizationUnit.objects.filter(
            unit_type=UnitType.PROGRAM_TECHNICAL_MANAGEMENT, status=UnitStatus.ACTIVE
        ).select_related("level")
        self.fields["region"].queryset = OrganizationUnit.objects.filter(
            unit_type=UnitType.REGION, status=UnitStatus.ACTIVE
        ).select_related("level")
        self.fields["district"].queryset = OrganizationUnit.objects.filter(
            unit_type=UnitType.DISTRICT, status=UnitStatus.ACTIVE
        ).select_related("level")
        self.fields["community"].queryset = OrganizationUnit.objects.filter(
            unit_type=UnitType.COMMUNITY, status=UnitStatus.ACTIVE
        ).select_related("level")
        self.fields["team"].queryset = OrganizationUnit.objects.filter(
            unit_type=UnitType.TEAM, status=UnitStatus.ACTIVE
        ).select_related("level")
        self.fields["organizational_unit"].queryset = OrganizationUnit.objects.filter(
            status=UnitStatus.ACTIVE
        ).select_related("level")
        # Filter Position queryset to active positions
        self.fields["position"].queryset = Position.objects.filter(
            status=PositionStatus.ACTIVE
        ).select_related("organizational_unit", "classification")

        # Explicit empty labels / placeholders
        self.fields["position"].empty_label = _("Select Position")
        self.fields["organizational_unit"].empty_label = _("Select Organizational Unit")
        self.fields["directorate"].empty_label = _("Select Directorate")
        self.fields["department"].empty_label = _("Select Department")
        self.fields["program_technical_management"].empty_label = _(
            "Select Program / Technical Management"
        )
        self.fields["team"].empty_label = _("Select Team")
        self.fields["region"].empty_label = _("Select Region")
        self.fields["district"].empty_label = _("Select District")
        self.fields["community"].empty_label = _("Select Community")
        self.fields["supervisor"].empty_label = _("Select Immediate Supervisor")

    def save(self, commit=True):
        """Save the form and update the related user's first and last name."""
        # Save the leadership profile instance
        instance = super().save(commit=False)
        
        # Update the related user's first and last name from full_name
        if commit:
            with transaction.atomic():
                instance.save()
                # Update the related user's name
                full_name = self.cleaned_data.get("full_name", "").strip()
                if full_name and instance.user:
                    # Split full name into first and last name (simple split on first space)
                    name_parts = full_name.split(" ", 1)
                    if len(name_parts) == 2:
                        first_name, last_name = name_parts
                    else:
                        # If only one part, treat as first name with empty last name
                        first_name, last_name = name_parts[0], ""
                    
                    # Update user fields
                    instance.user.first_name = first_name
                    instance.user.last_name = last_name
                    instance.user.save(update_fields=["first_name", "last_name"])
        # When commit=False, don't save anything - just return the unsaved instance
        return instance

    def clean_reference_number(self):
        """Reference numbers are immutable once issued."""
        if self.instance and self.instance.pk:
            return self.instance.reference_number
        return self.cleaned_data.get("reference_number")

    def clean(self):
        """Perform server-side relationship and hierarchy validation."""
        cleaned_data = super().clean()
        directorate = cleaned_data.get("directorate")
        department = cleaned_data.get("department")
        ptm = cleaned_data.get("program_technical_management")
        region = cleaned_data.get("region")
        district = cleaned_data.get("district")
        community = cleaned_data.get("community")
        team = cleaned_data.get("team")

        from apps.organizations.seed_data import (
            DEPARTMENT_TO_PTM_MAP,
            DIRECTORATE_TO_DEPARTMENT_MAP,
            DIRECTORATE_TO_PTM_MAP,
        )

        # 1. Directorate <-> Department validation
        if directorate and department:
            allowed_depts = DIRECTORATE_TO_DEPARTMENT_MAP.get(
                directorate.identifier, ()
            )
            if (
                allowed_depts
                and department.identifier not in allowed_depts
                and department.parent_id != directorate.id
            ):
                self.add_error(
                    "department",
                    _(
                        "The selected Department '%(dept)s' does not report into '%(dir)s'."
                    )
                    % {"dept": department.name, "dir": directorate.name},
                )

        # 2. Department <-> Program & Technical Management validation
        if department and ptm:
            allowed_ptm = DEPARTMENT_TO_PTM_MAP.get(department.identifier, ())
            if (
                allowed_ptm
                and ptm.identifier not in allowed_ptm
                and ptm.parent_id != department.id
            ):
                self.add_error(
                    "program_technical_management",
                    _(
                        "The selected Program / Technical role '%(ptm)s' is not valid for '%(dept)s'."
                    )
                    % {"ptm": ptm.name, "dept": department.name},
                )
        elif directorate and ptm and not department:
            allowed_ptm = DIRECTORATE_TO_PTM_MAP.get(directorate.identifier, ())
            if allowed_ptm and ptm.identifier not in allowed_ptm:
                self.add_error(
                    "program_technical_management",
                    _(
                        "The selected Program / Technical role '%(ptm)s' is not valid for '%(dir)s'."
                    )
                    % {"ptm": ptm.name, "dir": directorate.name},
                )

        # 3. Geographical Hierarchy validation
        if district and region:
            if district.parent_id and district.parent_id != region.id:
                ancestor_ids = [a.id for a in district.get_ancestor_chain()]
                if region.id not in ancestor_ids:
                    self.add_error(
                        "district",
                        _(
                            "The selected District '%(dist)s' does not belong to Region '%(reg)s'."
                        )
                        % {"dist": district.name, "reg": region.name},
                    )

        if community and district:
            if community.parent_id and community.parent_id != district.id:
                ancestor_ids = [a.id for a in community.get_ancestor_chain()]
                if district.id not in ancestor_ids:
                    self.add_error(
                        "community",
                        _(
                            "The selected Community '%(comm)s' does not belong to District '%(dist)s'."
                        )
                        % {"comm": community.name, "dist": district.name},
                    )

        if team and community:
            if team.parent_id and team.parent_id != community.id:
                ancestor_ids = [a.id for a in team.get_ancestor_chain()]
                if community.id not in ancestor_ids:
                    self.add_error(
                        "team",
                        _(
                            "The selected Team '%(team)s' does not belong to Community '%(comm)s'."
                        )
                        % {"team": team.name, "comm": community.name},
                    )

        return cleaned_data


class LeadershipAppointmentForm(forms.ModelForm):
    """Form for creating and editing leadership appointments."""

    class Meta:
        model = LeadershipAppointment
        fields = [
            "profile",
            "position",
            "organizational_unit",
            "appointment_type",
            "appointing_authority",
            "appointment_date",
            "effective_date",
            "term_start",
            "term_end",
            "status",
        ]
        widgets = {
            "appointment_date": forms.DateInput(
                attrs={"type": "date"},
            ),
            "effective_date": forms.DateInput(
                attrs={"type": "date"},
            ),
            "term_start": forms.DateInput(
                attrs={"type": "date"},
            ),
            "term_end": forms.DateInput(
                attrs={"type": "date"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["position"].queryset = Position.objects.filter(
            status=PositionStatus.ACTIVE
        ).order_by("title")
        self.fields["organizational_unit"].queryset = OrganizationUnit.objects.filter(
            status=UnitStatus.ACTIVE
        ).order_by("name")
        self.fields["position"].empty_label = _("Select Position")
        self.fields["organizational_unit"].empty_label = _("Select Organizational Unit")


class PerformanceReviewForm(forms.ModelForm):
    """Form for creating and editing performance reviews."""

    class Meta:
        model = PerformanceReview
        fields = [
            "profile",
            "review_cycle",
            "period_start",
            "period_end",
            "reviewer",
            "achievements",
            "challenges",
            "recommendations",
            "improvement_plan",
            "overall_assessment",
            "overall_rating",
            "status",
        ]
        widgets = {
            "period_start": forms.DateInput(
                attrs={"type": "date"},
            ),
            "period_end": forms.DateInput(
                attrs={"type": "date"},
            ),
            "achievements": forms.Textarea(attrs={"rows": 4}),
            "challenges": forms.Textarea(attrs={"rows": 4}),
            "recommendations": forms.Textarea(attrs={"rows": 4}),
            "improvement_plan": forms.Textarea(attrs={"rows": 4}),
            "overall_assessment": forms.Textarea(attrs={"rows": 4}),
        }


class LeadershipAttendanceForm(forms.ModelForm):
    """Form for marking leadership attendance."""

    class Meta:
        model = LeadershipAttendance
        fields = [
            "profile",
            "attendance_type",
            "attendance_date",
            "activity_name",
            "venue",
            "status",
        ]
        widgets = {
            "attendance_date": forms.DateInput(
                attrs={"type": "date"},
            ),
        }


class CoachingRecordForm(forms.ModelForm):
    """Form for coaching session records."""

    class Meta:
        model = CoachingRecord
        fields = [
            "coach",
            "leader",
            "category",
            "session_date",
            "objectives",
            "topics_discussed",
            "agreed_actions",
            "follow_up_date",
            "outcomes",
            "is_confidential",
        ]
        widgets = {
            "session_date": forms.DateInput(
                attrs={"type": "date"},
            ),
            "follow_up_date": forms.DateInput(
                attrs={"type": "date"},
            ),
            "objectives": forms.Textarea(attrs={"rows": 3}),
            "topics_discussed": forms.Textarea(attrs={"rows": 3}),
            "agreed_actions": forms.Textarea(attrs={"rows": 3}),
            "outcomes": forms.Textarea(attrs={"rows": 3}),
        }


class MentorshipRecordForm(forms.ModelForm):
    """Form for mentorship relationship records."""

    class Meta:
        model = MentorshipRecord
        fields = [
            "mentor",
            "mentee",
            "start_date",
            "end_date",
            "development_objectives",
            "progress_notes",
            "outcomes",
            "evaluation",
            "status",
        ]
        widgets = {
            "start_date": forms.DateInput(
                attrs={"type": "date"},
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date"},
            ),
            "development_objectives": forms.Textarea(
                attrs={"rows": 3},
            ),
            "progress_notes": forms.Textarea(attrs={"rows": 3}),
            "outcomes": forms.Textarea(attrs={"rows": 3}),
            "evaluation": forms.Textarea(attrs={"rows": 3}),
        }


class SuccessionPlanForm(forms.ModelForm):
    """Form for succession planning."""

    class Meta:
        model = SuccessionPlan
        fields = [
            "position",
            "current_holder",
            "readiness_level",
            "required_competencies",
            "development_activities",
            "target_readiness_date",
            "risk",
            "is_active",
        ]
        widgets = {
            "target_readiness_date": forms.DateInput(
                attrs={"type": "date"},
            ),
            "required_competencies": forms.Textarea(
                attrs={"rows": 3},
            ),
            "development_activities": forms.Textarea(
                attrs={"rows": 3},
            ),
        }
