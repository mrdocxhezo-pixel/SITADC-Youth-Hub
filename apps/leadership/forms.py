"""Forms for the Leadership Management module."""

from django import forms
from django.utils.translation import gettext_lazy as _

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
            "region",
            "district",
            "community",
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
            "gender": forms.TextInput(attrs={"class": "form-control"}),
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
            "region": forms.Select(attrs={"class": "form-select"}),
            "district": forms.Select(attrs={"class": "form-select"}),
            "community": forms.Select(attrs={"class": "form-select"}),
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
            "gender": _("Gender"),
            "date_of_birth": _("Date of Birth"),
            "phone_number": _("Phone Number"),
            "email": _("Email Address"),
            "residential_address": _("Residential Address"),
            "emergency_contact_name": _("Emergency Contact Name"),
            "emergency_contact_phone": _("Emergency Contact Phone"),
            "leadership_level": _("Leadership Level"),
            "position": _("Position"),
            "organizational_unit": _("Organizational Unit"),
            "directorate": _("Directorate"),
            "region": _("Region"),
            "district": _("District"),
            "community": _("Community"),
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
            "region": _("The region this leader is assigned to."),
            "district": _("The district this leader is assigned to."),
            "community": _("The community this leader is assigned to."),
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

    def clean_reference_number(self):
        """Reference numbers are immutable once issued."""
        if self.instance and self.instance.pk:
            return self.instance.reference_number
        return self.cleaned_data.get("reference_number")


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
