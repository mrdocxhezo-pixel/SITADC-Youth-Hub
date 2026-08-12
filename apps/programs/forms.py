"""Accessible, service-facing forms for program and project management."""

# ruff: noqa: RUF012 - Django form Meta options are declarative attributes.

from __future__ import annotations

from typing import Any, cast

from django import forms
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _

from apps.accounts.selectors import get_active_users
from apps.organizations.selectors import get_active_units
from apps.stakeholders.models import Stakeholder

from .constants import (
    ChangeStatus,
    ProgramStatus,
    ProjectStatus,
    ReferenceDataKind,
    WBSNodeStatus,
)
from .models import (
    Activity,
    BeneficiaryParticipation,
    BeneficiaryRecord,
    ChangeRequest,
    Deliverable,
    EvidenceRecord,
    Issue,
    LessonsLearned,
    Milestone,
    ProcurementRequest,
    Program,
    ProgramBudget,
    ProgramDocument,
    ProgramEvaluation,
    ProgramIndicator,
    ProgramPortfolio,
    ProgramReferenceData,
    ProgramRisk,
    ProgramStakeholderLink,
    ProgramTeamMember,
    ProgressUpdate,
    Project,
    ProjectClosure,
    ProjectReport,
    ProjectResult,
    ProjectTimeline,
    ResourceAllocation,
    Task,
    WBSNode,
    WorkPlan,
)
from .services import PROGRAM_TRANSITIONS, PROJECT_TRANSITIONS


def _model_choice(form: forms.BaseForm, name: str) -> forms.ModelChoiceField:
    """Return a model-choice field with its concrete Django type."""
    return cast(forms.ModelChoiceField, form.fields[name])


def _choice(form: forms.BaseForm, name: str) -> forms.ChoiceField:
    """Return a choice field with its concrete Django type."""
    return cast(forms.ChoiceField, form.fields[name])


def _active_users():
    return get_active_users().order_by("first_name", "last_name", "email")


def _active_reference_data(kind: str):
    return ProgramReferenceData.objects.filter(kind=kind, active=True).order_by(
        "order", "name"
    )


def _validate_date_order(
    cleaned_data: dict[str, Any],
    start_name: str,
    end_name: str,
    *,
    message: str | None = None,
) -> None:
    start = cleaned_data.get(start_name)
    end = cleaned_data.get(end_name)
    if start and end and end < start:
        raise ValidationError(
            {end_name: message or _("The end date cannot precede the start date.")}
        )


class ProgramFormMixin:
    """Apply Bootstrap controls and accessible error/help associations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._relax_defaulted_fields()
        for name, field in self.fields.items():  # type: ignore[attr-defined]
            widget = field.widget
            if isinstance(field, forms.DateTimeField):
                field.widget = forms.DateTimeInput(
                    attrs=widget.attrs,
                    format="%Y-%m-%dT%H:%M",
                )
                field.widget.attrs["type"] = "datetime-local"
                field.input_formats = ["%Y-%m-%dT%H:%M"]
                widget = field.widget
            elif isinstance(field, forms.DateField):
                field.widget = forms.DateInput(attrs=widget.attrs, format="%Y-%m-%d")
                field.widget.attrs["type"] = "date"
                widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, forms.Select | forms.SelectMultiple):
                css_class = "form-select"
            else:
                css_class = "form-control"
            widget.attrs["class"] = " ".join(
                value for value in (widget.attrs.get("class", ""), css_class) if value
            )
            if field.help_text:
                widget.attrs["aria-describedby"] = f"id_{name}_help"

    def _relax_defaulted_fields(self) -> None:
        """Make model fields with DB defaults optional so create forms are usable."""
        meta = getattr(self, "Meta", None)
        model = getattr(meta, "model", None)
        if model is None:
            return
        for name in self.fields:  # type: ignore[attr-defined]
            try:
                model_field = model._meta.get_field(name)
            except FieldDoesNotExist:
                continue
            if model_field.has_default():
                self.fields[name].required = False  # type: ignore[attr-defined]

    def clean(self):
        cleaned = super().clean()  # type: ignore[misc]
        if cleaned is None:
            return cleaned
        meta = getattr(self, "Meta", None)
        model = getattr(meta, "model", None)
        if model is None:
            return cleaned
        for name in list(cleaned):
            value = cleaned.get(name)
            if value not in (None, ""):
                continue
            try:
                model_field = model._meta.get_field(name)
            except FieldDoesNotExist:
                continue
            if model_field.has_default():
                cleaned.pop(name)
        return cleaned

    def full_clean(self):
        super().full_clean()  # type: ignore[misc]
        for name in self.errors:  # type: ignore[attr-defined]
            field = self.fields.get(name)  # type: ignore[attr-defined]
            if field is None:
                continue
            css_classes = field.widget.attrs.get("class", "").split()
            if "is-invalid" not in css_classes:
                css_classes.append("is-invalid")
            field.widget.attrs["class"] = " ".join(css_classes)
            field.widget.attrs["aria-invalid"] = "true"


class ProgramForm(ProgramFormMixin, forms.ModelForm):
    """Create or update an authoritative program profile."""

    class Meta:
        model = Program
        fields = [
            "title",
            "short_title",
            "portfolio",
            "category",
            "description",
            "background",
            "justification",
            "strategic_objective",
            "vision",
            "mission",
            "pillars",
            "sdgs",
            "expected_outcomes",
            "expected_outputs",
            "key_indicators",
            "geographic_coverage",
            "regions",
            "districts",
            "communities",
            "target_beneficiaries",
            "target_beneficiary_count",
            "start_date",
            "end_date",
            "priority",
            "program_manager",
            "responsible_directorate",
            "budget_approved",
            "currency",
            "funding_sources",
            "assumptions",
            "dependencies",
        ]
        widgets = {
            name: forms.Textarea(attrs={"rows": 3})
            for name in (
                "description",
                "background",
                "justification",
                "strategic_objective",
                "vision",
                "mission",
                "expected_outcomes",
                "expected_outputs",
                "key_indicators",
                "geographic_coverage",
                "target_beneficiaries",
                "assumptions",
                "dependencies",
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "portfolio").queryset = ProgramPortfolio.objects.all()
        _model_choice(self, "category").queryset = _active_reference_data(
            ReferenceDataKind.CATEGORY
        )
        _model_choice(self, "pillars").queryset = _active_reference_data(
            ReferenceDataKind.PILLAR
        )
        _model_choice(self, "sdgs").queryset = _active_reference_data(
            ReferenceDataKind.SDG
        )
        _model_choice(self, "funding_sources").queryset = _active_reference_data(
            ReferenceDataKind.FUNDING_SOURCE
        )
        _model_choice(self, "program_manager").queryset = _active_users()
        active_units = get_active_units().order_by("name")
        _model_choice(self, "responsible_directorate").queryset = active_units

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "start_date", "end_date")
        return cleaned_data


class ProgramStatusTransitionForm(ProgramFormMixin, forms.Form):
    new_status = forms.ChoiceField(label=_("New status"))
    reason = forms.CharField(
        label=_("Reason"),
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("This reason is retained in the status history."),
    )

    def __init__(self, *args, program: Program, **kwargs):
        super().__init__(*args, **kwargs)
        allowed = PROGRAM_TRANSITIONS.get(program.status, set())
        _choice(self, "new_status").choices = [
            (value, label) for value, label in ProgramStatus.choices if value in allowed
        ]


class ProjectForm(ProgramFormMixin, forms.ModelForm):
    """Create or update a project under a program."""

    class Meta:
        model = Project
        fields = [
            "program",
            "title",
            "category",
            "classifications",
            "description",
            "objectives",
            "scope",
            "expected_outputs",
            "expected_outcomes",
            "target_beneficiaries",
            "target_beneficiary_count",
            "geographic_coverage",
            "regions",
            "districts",
            "communities",
            "start_date",
            "end_date",
            "project_manager",
            "budget_approved",
            "currency",
            "funding_source",
            "risk_level",
            "assumptions",
            "dependencies",
        ]
        widgets = {
            name: forms.Textarea(attrs={"rows": 3})
            for name in (
                "description",
                "objectives",
                "scope",
                "expected_outputs",
                "expected_outcomes",
                "target_beneficiaries",
                "geographic_coverage",
                "assumptions",
                "dependencies",
            )
        }

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        program_field = _model_choice(self, "program")
        program_field.queryset = Program.objects.filter(is_archived=False)
        if program is not None:
            program_field.initial = program
            program_field.queryset = Program.objects.filter(pk=program.pk)
        _model_choice(self, "category").queryset = _active_reference_data(
            ReferenceDataKind.PROJECT_CATEGORY
        )
        if "classifications" in self.fields:
            _model_choice(self, "classifications").queryset = _active_reference_data(
                ReferenceDataKind.PROJECT_CLASSIFICATION
            )
        _model_choice(self, "funding_source").queryset = _active_reference_data(
            ReferenceDataKind.FUNDING_SOURCE
        )
        _model_choice(self, "project_manager").queryset = _active_users()

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "start_date", "end_date")
        return cleaned_data


class ProjectStatusTransitionForm(ProgramFormMixin, forms.Form):
    new_status = forms.ChoiceField(label=_("New status"))
    reason = forms.CharField(
        label=_("Reason"),
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("This reason is retained in the status history."),
    )

    def __init__(self, *args, project: Project, **kwargs):
        super().__init__(*args, **kwargs)
        allowed = PROJECT_TRANSITIONS.get(project.status, set())
        _choice(self, "new_status").choices = [
            (value, label) for value, label in ProjectStatus.choices if value in allowed
        ]


class ReasonArchiveForm(ProgramFormMixin, forms.Form):
    reason = forms.CharField(
        label=_("Reason"),
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("The reason is preserved in status history."),
    )


class WorkPlanForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = WorkPlan
        fields = [
            "program",
            "project",
            "title",
            "reporting_period",
            "objectives",
            "start_date",
            "end_date",
            "budget_allocation",
            "responsible_officer",
            "status",
        ]
        widgets = {"objectives": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.program = program
        program_field = _model_choice(self, "program")
        if program is not None:
            program_field.initial = program
            program_field.queryset = Program.objects.filter(pk=program.pk)
        else:
            program_field.queryset = Program.objects.filter(is_archived=False)
        _model_choice(self, "responsible_officer").queryset = _active_users()

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "start_date", "end_date")
        if cleaned_data.get("program") and cleaned_data.get("project"):
            raise ValidationError(
                _("A work plan belongs to a program or a project, not both.")
            )
        if (
            not cleaned_data.get("program")
            and not cleaned_data.get("project")
            and self.program is not None
        ):
            cleaned_data["program"] = self.program
        return cleaned_data


class ActivityForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = Activity
        fields = [
            "title",
            "description",
            "responsible_officer",
            "location",
            "planned_date",
            "actual_date",
            "status",
            "expected_output",
            "completion_percentage",
            "budget_allocated",
            "budget_spent",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "expected_output": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, work_plan: WorkPlan | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if work_plan is not None:
            self.fields["work_plan"] = forms.ModelChoiceField(
                queryset=WorkPlan.objects.filter(pk=work_plan.pk),
                initial=work_plan,
            )
            self.fields["work_plan"].widget.attrs.update({"class": "form-select"})
        _model_choice(self, "responsible_officer").queryset = _active_users()

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "planned_date", "actual_date")
        return cleaned_data


class TaskForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "assigned_user",
            "priority",
            "due_date",
            "estimated_effort_hours",
            "completion_percentage",
            "status",
            "comments",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "comments": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, activity: Activity | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if activity is not None:
            self.fields["activity"] = forms.ModelChoiceField(
                queryset=Activity.objects.filter(pk=activity.pk),
                initial=activity,
            )
            self.fields["activity"].widget.attrs.update({"class": "form-select"})
        _model_choice(self, "assigned_user").queryset = _active_users()


class MilestoneForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = Milestone
        fields = [
            "title",
            "description",
            "target_date",
            "completion_date",
            "status",
            "responsible_officer",
            "deliverables",
            "evidence_notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "deliverables": forms.Textarea(attrs={"rows": 3}),
            "evidence_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, project: Project | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            self.fields["project"] = forms.ModelChoiceField(
                queryset=Project.objects.filter(pk=project.pk),
                initial=project,
            )
            self.fields["project"].widget.attrs.update({"class": "form-select"})
        _model_choice(self, "responsible_officer").queryset = _active_users()

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "target_date", "completion_date")
        return cleaned_data


class DeliverableForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = Deliverable
        fields = [
            "title",
            "description",
            "deliverable_type",
            "due_date",
            "completion_date",
            "status",
            "responsible_officer",
            "approval_notes",
            "evidence_notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "approval_notes": forms.Textarea(attrs={"rows": 3}),
            "evidence_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, project: Project | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            self.fields["project"] = forms.ModelChoiceField(
                queryset=Project.objects.filter(pk=project.pk),
                initial=project,
            )
            self.fields["project"].widget.attrs.update({"class": "form-select"})
        _model_choice(self, "responsible_officer").queryset = _active_users()

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "due_date", "completion_date")
        return cleaned_data


class IssueForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = Issue
        fields = [
            "program",
            "project",
            "title",
            "description",
            "priority",
            "date_identified",
            "responsible_officer",
            "corrective_actions",
            "target_resolution_date",
            "resolved_date",
            "status",
            "evidence_notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "corrective_actions": forms.Textarea(attrs={"rows": 3}),
            "evidence_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        program_field = _model_choice(self, "program")
        if program is not None:
            program_field.initial = program
            program_field.queryset = Program.objects.filter(pk=program.pk)
        else:
            program_field.queryset = Program.objects.filter(is_archived=False)
        _model_choice(self, "responsible_officer").queryset = _active_users()

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "date_identified", "resolved_date")
        if cleaned_data.get("program") and cleaned_data.get("project"):
            raise ValidationError(
                _("An issue belongs to a program or a project, not both.")
            )
        return cleaned_data


class ChangeRequestForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ChangeRequest
        fields = [
            "program",
            "project",
            "requestor",
            "title",
            "reason_for_change",
            "scope_affected",
            "budget_impact",
            "timeline_impact",
            "risk_assessment",
            "status",
            "decision_notes",
        ]
        widgets = {
            "reason_for_change": forms.Textarea(attrs={"rows": 3}),
            "scope_affected": forms.Textarea(attrs={"rows": 3}),
            "risk_assessment": forms.Textarea(attrs={"rows": 3}),
            "decision_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        program_field = _model_choice(self, "program")
        if program is not None:
            program_field.initial = program
            program_field.queryset = Program.objects.filter(pk=program.pk)
        else:
            program_field.queryset = Program.objects.filter(is_archived=False)
        _model_choice(self, "requestor").queryset = _active_users()

    def clean(self):
        cleaned_data = super().clean() or {}
        if cleaned_data.get("program") and cleaned_data.get("project"):
            raise ValidationError(
                _("A change request belongs to a program or a project, not both.")
            )
        return cleaned_data


class EvidenceRecordForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = EvidenceRecord
        fields = [
            "program",
            "project",
            "activity",
            "title",
            "evidence_type",
            "file",
            "captured_at",
            "gps_coordinates",
            "notes",
            "is_verified",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        program_field = _model_choice(self, "program")
        if program is not None:
            program_field.initial = program
            program_field.queryset = Program.objects.filter(pk=program.pk)
            _model_choice(self, "activity").queryset = Activity.objects.filter(
                work_plan__program=program
            )
        else:
            program_field.queryset = Program.objects.filter(is_archived=False)
        _model_choice(self, "evidence_type").queryset = _active_reference_data(
            ReferenceDataKind.EVIDENCE_TYPE
        )

    def clean(self):
        cleaned_data = super().clean() or {}
        if cleaned_data.get("program") and cleaned_data.get("project"):
            raise ValidationError(
                _("Evidence belongs to a program or a project, not both.")
            )
        return cleaned_data


class BeneficiaryRecordForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = BeneficiaryRecord
        fields = [
            "program",
            "project",
            "name",
            "category",
            "age",
            "gender",
            "location",
            "vulnerability_status",
            "disability_included",
            "services_received",
            "enrollment_date",
            "completion_date",
            "status",
        ]
        widgets = {"services_received": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        program_field = _model_choice(self, "program")
        if program is not None:
            program_field.initial = program
            program_field.queryset = Program.objects.filter(pk=program.pk)
        else:
            program_field.queryset = Program.objects.filter(is_archived=False)
        _model_choice(self, "category").queryset = _active_reference_data(
            ReferenceDataKind.BENEFICIARY_CATEGORY
        )

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "enrollment_date", "completion_date")
        if cleaned_data.get("program") and cleaned_data.get("project"):
            raise ValidationError(
                _("A beneficiary belongs to a program or a project, not both.")
            )
        return cleaned_data


class ProgressUpdateForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProgressUpdate
        fields = [
            "program",
            "project",
            "period_label",
            "overall_completion",
            "budget_utilization",
            "status",
            "summary",
            "challenges",
            "next_steps",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "challenges": forms.Textarea(attrs={"rows": 3}),
            "next_steps": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        program_field = _model_choice(self, "program")
        if program is not None:
            program_field.initial = program
            program_field.queryset = Program.objects.filter(pk=program.pk)
        else:
            program_field.queryset = Program.objects.filter(is_archived=False)

    def clean(self):
        cleaned_data = super().clean() or {}
        if cleaned_data.get("program") and cleaned_data.get("project"):
            raise ValidationError(
                _("A progress update belongs to a program or a project, not both.")
            )
        return cleaned_data


class ProgramDocumentForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProgramDocument
        fields = [
            "program",
            "project",
            "title",
            "document_type",
            "file",
            "description",
            "status",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        program_field = _model_choice(self, "program")
        if program is not None:
            program_field.initial = program
            program_field.queryset = Program.objects.filter(pk=program.pk)
        else:
            program_field.queryset = Program.objects.filter(is_archived=False)
        _model_choice(self, "document_type").queryset = _active_reference_data(
            ReferenceDataKind.DOCUMENT_TYPE
        )

    def clean(self):
        cleaned_data = super().clean() or {}
        if cleaned_data.get("program") and cleaned_data.get("project"):
            raise ValidationError(
                _("A document belongs to a program or a project, not both.")
            )
        return cleaned_data


class ProgramBudgetForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProgramBudget
        fields = [
            "period_label",
            "approved_amount",
            "utilized_amount",
            "funding_source",
            "currency",
            "start_date",
            "end_date",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "funding_source").queryset = _active_reference_data(
            ReferenceDataKind.FUNDING_SOURCE
        )

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "start_date", "end_date")
        return cleaned_data


class ProgramRiskForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProgramRisk
        fields = [
            "category",
            "title",
            "description",
            "likelihood",
            "impact",
            "mitigation_measures",
            "responsible_officer",
            "next_review_date",
            "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "mitigation_measures": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "category").queryset = _active_reference_data(
            ReferenceDataKind.RISK_CATEGORY
        )
        _model_choice(self, "responsible_officer").queryset = _active_users()


class ProgramEvaluationForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProgramEvaluation
        fields = [
            "evaluation_type",
            "title",
            "evaluation_date",
            "methodology",
            "findings",
            "recommendations",
            "success_stories",
            "best_practices",
            "lessons_learned",
            "conducted_by",
            "report_file",
            "is_published",
        ]
        widgets = {
            "methodology": forms.Textarea(attrs={"rows": 3}),
            "findings": forms.Textarea(attrs={"rows": 3}),
            "recommendations": forms.Textarea(attrs={"rows": 3}),
            "success_stories": forms.Textarea(attrs={"rows": 3}),
            "best_practices": forms.Textarea(attrs={"rows": 3}),
            "lessons_learned": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "conducted_by").queryset = _active_users()


class ProgramIndicatorForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProgramIndicator
        fields = [
            "code",
            "description",
            "indicator_type",
            "baseline",
            "target",
            "actual",
            "unit",
            "frequency",
            "responsible_officer",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _model_choice(self, "indicator_type").queryset = _active_reference_data(
            ReferenceDataKind.INDICATOR_TYPE
        )
        _model_choice(self, "responsible_officer").queryset = _active_users()


class ProgramTeamMemberForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProgramTeamMember
        fields = [
            "user",
            "role_title",
            "responsibility",
            "start_date",
            "end_date",
            "is_active",
        ]
        widgets = {"responsibility": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if program is not None:
            self.fields["program"] = forms.ModelChoiceField(
                queryset=Program.objects.filter(pk=program.pk),
                initial=program,
            )
            self.fields["program"].widget.attrs.update({"class": "form-select"})
        _model_choice(self, "user").queryset = _active_users()

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "start_date", "end_date")
        return cleaned_data


class ProgramStakeholderLinkForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProgramStakeholderLink
        fields = ["stakeholder", "link_kind", "description", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if program is not None:
            self.fields["program"] = forms.ModelChoiceField(
                queryset=Program.objects.filter(pk=program.pk),
                initial=program,
            )
            self.fields["program"].widget.attrs.update({"class": "form-select"})
        _model_choice(self, "stakeholder").queryset = Stakeholder.objects.filter(
            is_active=True
        ).order_by("legal_name")


class ChangeStatusForm(ProgramFormMixin, forms.Form):
    status = forms.ChoiceField(choices=ChangeStatus.choices)
    decision_notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3})
    )


class DocumentArchiveForm(ProgramFormMixin, forms.Form):
    reason = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class ResourceAllocationForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ResourceAllocation
        fields = [
            "program",
            "project",
            "resource_type",
            "description",
            "quantity",
            "unit",
            "estimated_cost",
            "currency",
            "supplier_name",
            "start_date",
            "end_date",
            "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        program_field = _model_choice(self, "program")
        if program is not None:
            program_field.initial = program
            program_field.queryset = Program.objects.filter(pk=program.pk)
        else:
            program_field.queryset = Program.objects.filter(is_archived=False)

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "start_date", "end_date")
        if cleaned_data.get("program") and cleaned_data.get("project"):
            raise ValidationError(
                _("A resource allocation belongs to a program or a project, not both.")
            )
        return cleaned_data


class ProcurementRequestForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProcurementRequest
        fields = [
            "program",
            "project",
            "title",
            "description",
            "items",
            "quantity",
            "estimated_cost",
            "currency",
            "justification",
            "supplier_name",
            "status",
            "requested_by",
            "delivery_status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "items": forms.Textarea(attrs={"rows": 3}),
            "justification": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        program_field = _model_choice(self, "program")
        if program is not None:
            program_field.initial = program
            program_field.queryset = Program.objects.filter(pk=program.pk)
        else:
            program_field.queryset = Program.objects.filter(is_archived=False)
        _model_choice(self, "requested_by").queryset = _active_users()

    def clean(self):
        cleaned_data = super().clean() or {}
        if cleaned_data.get("program") and cleaned_data.get("project"):
            raise ValidationError(
                _("A procurement request belongs to a program or a project, not both.")
            )
        return cleaned_data


class LessonsLearnedForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = LessonsLearned
        fields = [
            "program",
            "project",
            "title",
            "category",
            "summary",
            "context",
            "recommendations",
            "recorded_by",
            "recorded_at",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "context": forms.Textarea(attrs={"rows": 3}),
            "recommendations": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, program: Program | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        program_field = _model_choice(self, "program")
        if program is not None:
            program_field.initial = program
            program_field.queryset = Program.objects.filter(pk=program.pk)
        else:
            program_field.queryset = Program.objects.filter(is_archived=False)
        _model_choice(self, "recorded_by").queryset = _active_users()

    def clean(self):
        cleaned_data = super().clean() or {}
        if cleaned_data.get("program") and cleaned_data.get("project"):
            raise ValidationError(
                _(
                    "A lessons learned record belongs to a program or a "
                    "project, not both."
                )
            )
        return cleaned_data


class WBSNodeForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = WBSNode
        fields = [
            "parent",
            "node_type",
            "code",
            "title",
            "description",
            "responsible_officer",
            "planned_start_date",
            "planned_end_date",
            "actual_start_date",
            "actual_end_date",
            "estimated_effort_hours",
            "actual_effort_hours",
            "completion_percentage",
            "budget_allocated",
            "budget_spent",
            "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, project: Project | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            _model_choice(self, "parent").queryset = WBSNode.objects.filter(
                project=project
            ).order_by("code", "title")
            self.fields["parent"].required = False
        _model_choice(self, "responsible_officer").queryset = _active_users()

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "planned_start_date", "planned_end_date")
        _validate_date_order(cleaned_data, "actual_start_date", "actual_end_date")
        return cleaned_data


class ProjectResultForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProjectResult
        fields = [
            "result_type",
            "code",
            "description",
            "indicator",
            "baseline",
            "target",
            "actual",
            "status",
            "target_date",
            "notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class BeneficiaryParticipationForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = BeneficiaryParticipation
        fields = [
            "participation_date",
            "activity_title",
            "description",
            "services_received",
            "outcomes_achieved",
            "notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "services_received": forms.Textarea(attrs={"rows": 3}),
            "outcomes_achieved": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class ProjectTimelineForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProjectTimeline
        fields = [
            "title",
            "description",
            "planned_start_date",
            "planned_end_date",
            "actual_start_date",
            "actual_end_date",
            "status",
            "depends_on",
            "order",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, project: Project | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None and "depends_on" in self.fields:
            _model_choice(self, "depends_on").queryset = ProjectTimeline.objects.filter(
                project=project
            ).order_by("order", "planned_start_date")

    def clean(self):
        cleaned_data = super().clean() or {}
        _validate_date_order(cleaned_data, "planned_start_date", "planned_end_date")
        _validate_date_order(cleaned_data, "actual_start_date", "actual_end_date")
        return cleaned_data


class ProjectClosureForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProjectClosure
        fields = [
            "completion_verification",
            "financial_reconciliation",
            "final_evaluation_notes",
            "asset_handover",
            "stakeholder_signoff",
            "final_documentation",
            "closure_notes",
            "closure_date",
        ]
        widgets = {
            name: forms.Textarea(attrs={"rows": 3})
            for name in (
                "completion_verification",
                "financial_reconciliation",
                "final_evaluation_notes",
                "asset_handover",
                "stakeholder_signoff",
                "final_documentation",
                "closure_notes",
            )
        }


class ClosureActionForm(ProgramFormMixin, forms.Form):
    notes = forms.CharField(
        label=_("Notes"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class ProjectReportForm(ProgramFormMixin, forms.ModelForm):
    class Meta:
        model = ProjectReport
        fields = [
            "title",
            "report_type",
            "period_label",
            "summary",
            "report_file",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 4}),
        }


class ReportSubmissionForm(ProgramFormMixin, forms.Form):
    summary = forms.CharField(
        label=_("Executive summary"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )


class ProjectApprovalActionForm(ProgramFormMixin, forms.Form):
    notes = forms.CharField(
        label=_("Review notes"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class ChangeDecisionForm(ProgramFormMixin, forms.Form):
    decision = forms.ChoiceField(
        label=_("Decision"),
        choices=(
            ("APPROVED", _("Approve")),
            ("REJECTED", _("Reject")),
        ),
    )
    reviewer_notes = forms.CharField(
        label=_("Reviewer notes"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class WBSNodeProgressForm(ProgramFormMixin, forms.Form):
    status = forms.ChoiceField(
        label=_("Status"),
        choices=WBSNodeStatus.choices,
    )
    completion_percentage = forms.DecimalField(
        label=_("Completion percentage"),
        min_value=0,
        max_value=100,
        required=False,
        max_digits=5,
        decimal_places=2,
    )
    actual_effort_hours = forms.DecimalField(
        label=_("Actual effort (hours)"),
        required=False,
        max_digits=10,
        decimal_places=2,
    )
    notes = forms.CharField(
        label=_("Notes"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
