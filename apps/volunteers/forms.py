"""
Django Forms for the volunteer management module.
"""

# ruff: noqa: RUF012 - Django form Meta options are declarative attributes.

from typing import cast

from django import forms
from django.contrib.auth import get_user_model
from django.forms import ModelChoiceField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import (
    VolunteerActivityLog,
    VolunteerApplication,
    VolunteerAssignment,
    VolunteerAttendance,
    VolunteerCategory,
    VolunteerCommunication,
    VolunteerDisciplinaryRecord,
    VolunteerDocument,
    VolunteerExit,
    VolunteerInterview,
    VolunteerLeave,
    VolunteerOnboarding,
    VolunteerPerformance,
    VolunteerProfile,
    VolunteerRecognition,
    VolunteerRecruitment,
    VolunteerScreening,
    VolunteerTraining,
)

User = get_user_model()


class VolunteerFormMixin:
    """Apply consistent accessible Bootstrap controls to volunteer forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():  # type: ignore[attr-defined]
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class VolunteerProfileForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerProfile
        fields = [
            "national_id",
            "membership_number",
            "date_of_birth",
            "gender",
            "nationality",
            "phone_number",
            "email",
            "residential_address",
            "region",
            "district",
            "community",
            "emergency_contact_name",
            "emergency_contact_relationship",
            "emergency_contact_phone",
            "education_level",
            "occupation",
            "languages",
            "category",
            "volunteer_type",
            "volunteer_level",
            "availability",
            "team",
            "supervisor",
            "biography",
            "profile_photo",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "national_id": forms.TextInput(attrs={"class": "form-control"}),
            "membership_number": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.TextInput(attrs={"class": "form-control"}),
            "nationality": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "residential_address": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "region": forms.TextInput(attrs={"class": "form-control"}),
            "district": forms.TextInput(attrs={"class": "form-control"}),
            "community": forms.TextInput(attrs={"class": "form-control"}),
            "emergency_contact_name": forms.TextInput(attrs={"class": "form-control"}),
            "emergency_contact_relationship": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "emergency_contact_phone": forms.TextInput(attrs={"class": "form-control"}),
            "education_level": forms.TextInput(attrs={"class": "form-control"}),
            "occupation": forms.TextInput(attrs={"class": "form-control"}),
            "languages": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "volunteer_type": forms.Select(attrs={"class": "form-select"}),
            "volunteer_level": forms.Select(attrs={"class": "form-select"}),
            "availability": forms.Select(attrs={"class": "form-select"}),
            "team": forms.Select(attrs={"class": "form-select"}),
            "supervisor": forms.Select(attrs={"class": "form-select"}),
            "biography": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class VolunteerRegistrationForm(VolunteerProfileForm):
    user_account = forms.ModelChoiceField(
        label=_("User account"),
        queryset=User.objects.none(),
        help_text=_("Select the approved applicant's user account."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_field = cast(ModelChoiceField, self.fields["user_account"])
        user_field.queryset = User.objects.filter(
            is_active=True,
            volunteer_profile__isnull=True,
        ).order_by("first_name", "last_name", "email")


class VolunteerRecruitmentForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerRecruitment
        fields = [
            "title",
            "category",
            "volunteer_type",
            "vacancies",
            "location",
            "required_skills",
            "application_deadline",
            "supervisor",
            "status",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "volunteer_type": forms.Select(attrs={"class": "form-select"}),
            "vacancies": forms.NumberInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "required_skills": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "application_deadline": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "supervisor": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class VolunteerApplicationForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerApplication
        fields = [
            "recruitment",
            "applicant_name",
            "email",
            "phone_number",
            "gender",
            "date_of_birth",
            "address",
            "category",
            "volunteer_type",
            "skills",
            "motivation",
            "cv_file",
            "consent_confirmed",
        ]
        widgets = {
            "recruitment": forms.Select(attrs={"class": "form-select"}),
            "applicant_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "volunteer_type": forms.Select(attrs={"class": "form-select"}),
            "skills": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "motivation": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "consent_confirmed": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        recruitment_field = cast(ModelChoiceField, self.fields["recruitment"])
        recruitment_field.queryset = VolunteerRecruitment.objects.filter(
            status="OPEN",
            application_deadline__gte=timezone.localdate(),
        )


class VolunteerScreeningForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerScreening
        fields = [
            "identity_verified",
            "references_checked",
            "qualifications_verified",
            "safeguarding_cleared",
            "passed",
            "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class VolunteerInterviewForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerInterview
        fields = [
            "scheduled_datetime",
            "venue_or_link",
            "score",
            "recommendation",
            "passed",
        ]
        widgets = {
            "scheduled_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "recommendation": forms.Textarea(attrs={"rows": 3}),
        }


class VolunteerOnboardingForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerOnboarding
        fields = [
            "orientation_completed",
            "code_of_conduct_signed",
            "safeguarding_agreed",
            "confidentiality_signed",
            "welcome_pack_issued",
            "id_card_issued",
            "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class VolunteerAssignmentForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerAssignment
        fields = [
            "profile",
            "title",
            "program_name",
            "project_name",
            "team",
            "supervisor",
            "start_date",
            "end_date",
            "objectives",
        ]
        widgets = {
            "profile": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "program_name": forms.TextInput(attrs={"class": "form-control"}),
            "project_name": forms.TextInput(attrs={"class": "form-control"}),
            "team": forms.Select(attrs={"class": "form-select"}),
            "supervisor": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "objectives": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class VolunteerAttendanceForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerAttendance
        fields = [
            "profile",
            "date",
            "activity_name",
            "category",
            "status",
            "hours_served",
            "location",
        ]
        widgets = {
            "profile": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "activity_name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "hours_served": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.5"}
            ),
            "location": forms.TextInput(attrs={"class": "form-control"}),
        }


class VolunteerTrainingForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerTraining
        fields = [
            "profile",
            "title",
            "provider",
            "start_date",
            "completion_date",
            "certificate_issued",
            "certificate_file",
            "competencies_acquired",
        ]
        widgets = {
            "profile": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "provider": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "completion_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "certificate_issued": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "competencies_acquired": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }


class VolunteerPerformanceForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerPerformance
        fields = [
            "profile",
            "review_period",
            "overall_score",
            "kpis_met",
            "strengths",
            "areas_for_growth",
            "community_feedback",
        ]
        widgets = {
            "profile": forms.Select(attrs={"class": "form-select"}),
            "review_period": forms.TextInput(attrs={"class": "form-control"}),
            "overall_score": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 100}
            ),
            "kpis_met": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "strengths": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "areas_for_growth": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "community_feedback": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
        }


class VolunteerRecognitionForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerRecognition
        fields = ["profile", "title", "category", "award_date", "citation"]
        widgets = {
            "profile": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "award_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "citation": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class VolunteerLeaveForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerLeave
        fields = ["profile", "leave_type", "start_date", "end_date", "reason"]
        widgets = {
            "profile": forms.Select(attrs={"class": "form-select"}),
            "leave_type": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class VolunteerExitForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerExit
        fields = [
            "profile",
            "reason",
            "effective_date",
            "exit_interview_notes",
            "assets_returned",
            "documents_returned",
            "transition_to_alumni",
        ]
        widgets = {
            "profile": forms.Select(attrs={"class": "form-select"}),
            "reason": forms.Select(attrs={"class": "form-select"}),
            "effective_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "exit_interview_notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "assets_returned": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "documents_returned": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "transition_to_alumni": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class VolunteerActivityLogForm(VolunteerFormMixin, forms.ModelForm):
    beneficiaries_reached = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def clean_beneficiaries_reached(self):
        return self.cleaned_data["beneficiaries_reached"] or 0

    class Meta:
        model = VolunteerActivityLog
        fields = [
            "profile",
            "activity_title",
            "category",
            "activity_date",
            "program_name",
            "location",
            "hours_served",
            "beneficiaries_reached",
            "supervisor_comments",
            "supporting_evidence",
            "notes",
        ]
        widgets = {
            "profile": forms.Select(attrs={"class": "form-select"}),
            "activity_title": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "activity_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "program_name": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "hours_served": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.5"}
            ),
            "beneficiaries_reached": forms.NumberInput(attrs={"class": "form-control"}),
            "supervisor_comments": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "supporting_evidence": forms.FileInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class VolunteerDisciplinaryRecordForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerDisciplinaryRecord
        fields = [
            "profile",
            "incident_date",
            "nature_of_concern",
            "supporting_documents",
            "notes",
        ]
        widgets = {
            "profile": forms.Select(attrs={"class": "form-select"}),
            "incident_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "nature_of_concern": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "supporting_documents": forms.FileInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class VolunteerDisciplinaryDecisionForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerDisciplinaryRecord
        fields = [
            "status",
            "decision",
            "investigation_summary",
            "corrective_action",
            "effective_date",
        ]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "decision": forms.Select(attrs={"class": "form-select"}),
            "investigation_summary": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "corrective_action": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "effective_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }


class VolunteerCommunicationForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerCommunication
        fields = [
            "profile",
            "channel",
            "subject",
            "body",
            "attachment",
            "notes",
        ]
        widgets = {
            "profile": forms.Select(attrs={"class": "form-select"}),
            "channel": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "attachment": forms.FileInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class VolunteerDocumentUploadForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerDocument
        fields = [
            "profile",
            "title",
            "document_type",
            "file",
            "is_confidential",
            "retention_until",
        ]
        widgets = {
            "profile": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "document_type": forms.TextInput(attrs={"class": "form-control"}),
            "file": forms.FileInput(attrs={"class": "form-control"}),
            "is_confidential": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "retention_until": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }


class VolunteerDocumentReviewForm(VolunteerFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerDocument
        fields = ["status", "notes"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class VolunteerCategoryForm(VolunteerFormMixin, forms.ModelForm):
    sort_order = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def clean_sort_order(self):
        return self.cleaned_data["sort_order"] or 0

    class Meta:
        model = VolunteerCategory
        fields = ["name", "code", "description", "is_active", "sort_order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
        }
