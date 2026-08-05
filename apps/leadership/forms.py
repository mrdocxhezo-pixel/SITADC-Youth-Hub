"""Forms for the Leadership Management module."""

from django import forms

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
            "leadership_level",
            "position",
            "organizational_unit",
            "directorate",
            "supervisor",
            "biography",
            "qualifications",
            "professional_skills",
            "areas_of_expertise",
            "phone_number",
            "email",
            "status",
        ]
        widgets = {
            "biography": forms.Textarea(attrs={"rows": 4}),
            "qualifications": forms.Textarea(attrs={"rows": 3}),
            "professional_skills": forms.Textarea(attrs={"rows": 3}),
            "areas_of_expertise": forms.Textarea(attrs={"rows": 3}),
        }


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
