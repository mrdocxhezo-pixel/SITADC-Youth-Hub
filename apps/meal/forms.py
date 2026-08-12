"""Accessible, service-facing forms for the MEAL module."""

# ruff: noqa: RUF012 - Django form Meta options are declarative attributes.

from __future__ import annotations

from typing import cast

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.selectors import get_active_users

from .models import (
    BestPractice,
    Complaint,
    CorrectiveAction,
    DataCollectionPlan,
    DataCollectionTool,
    DataQualityAssessment,
    DataSource,
    DataSubmission,
    DQADimensionScore,
    Evaluation,
    EvaluationRecommendation,
    Feedback,
    Indicator,
    IndicatorBaseline,
    IndicatorResult,
    IndicatorTarget,
    LearningLog,
    LessonLearned,
    LogframeRow,
    LogicalFramework,
    MEALReport,
    MonitoringFinding,
    MonitoringPlan,
    MonitoringVisit,
    OrganizationalKPI,
    OutcomeHarvest,
    PerformanceScorecard,
    ResultsFramework,
    ResultStatement,
    ScorecardDimension,
    TheoryOfChange,
)


def _user_choices():
    return get_active_users()


def _choice_field(form, name: str) -> forms.ModelChoiceField:
    """Resolve a form field as a choice field for queryset updates."""
    return cast(forms.ModelChoiceField, form.fields[name])


class MEALFormMixin:
    """Apply Bootstrap controls and accessible error/help associations."""

    fields: dict[str, forms.Field]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            widget = field.widget
            if isinstance(field, forms.DateTimeField):
                field.widget = forms.DateTimeInput(
                    attrs=widget.attrs, format="%Y-%m-%dT%H:%M"
                )
                field.widget.attrs["type"] = "datetime-local"
                field.input_formats = ["%Y-%m-%dT%H:%M"]
                widget = field.widget
            elif isinstance(field, forms.DateField):
                field.widget = forms.DateInput(attrs=widget.attrs, format="%Y-%m-%d")
                field.widget.attrs["type"] = "date"
                field.input_formats = ["%Y-%m-%d"]
                widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select | forms.SelectMultiple):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class TheoryOfChangeForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = TheoryOfChange
        fields = [
            "program",
            "title",
            "strategic_goal",
            "development_challenge",
            "context",
            "assumptions",
            "preconditions",
            "inputs",
            "activities",
            "outputs",
            "outcomes",
            "long_term_impact",
            "risks",
            "external_factors",
            "success_indicators",
            "version",
            "effective_from",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False


class ResultsFrameworkForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = ResultsFramework
        fields = [
            "program",
            "title",
            "strategic_objective",
            "description",
            "reporting_frequency",
            "responsible_officer",
            "version",
            "effective_from",
            "effective_to",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        _choice_field(self, "responsible_officer").queryset = _user_choices()


class ResultStatementForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = ResultStatement
        fields = ["level", "title", "description", "indicators", "order"]


class LogicalFrameworkForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = LogicalFramework
        fields = [
            "program",
            "project",
            "title",
            "goal",
            "purpose",
            "version",
            "responsible_officer",
            "reporting_schedule",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _choice_field(self, "responsible_officer").queryset = _user_choices()


class LogframeRowForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = LogframeRow
        fields = [
            "level",
            "statement",
            "means_of_verification",
            "assumptions",
            "indicators",
            "order",
        ]


class IndicatorForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = Indicator
        fields = [
            "code",
            "title",
            "description",
            "formula",
            "calculation_method",
            "unit",
            "indicator_type",
            "category",
            "data_source",
            "collection_method",
            "reporting_frequency",
            "responsible_officer",
            "verification_method",
            "disaggregation",
            "programs",
            "projects",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _choice_field(self, "responsible_officer").queryset = _user_choices()


class IndicatorBaselineForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = IndicatorBaseline
        fields = [
            "value",
            "collection_date",
            "data_source",
            "collection_method",
            "geographic_coverage",
            "population_covered",
            "responsible_officer",
            "evidence_file",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _choice_field(self, "responsible_officer").queryset = _user_choices()


class IndicatorTargetForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = IndicatorTarget
        fields = ["period_label", "period_start", "period_end", "value", "threshold"]


class IndicatorResultForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = IndicatorResult
        fields = [
            "target",
            "period_label",
            "submission_date",
            "value",
            "data_source",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _choice_field(self, "data_source").queryset = DataSource.objects.filter(
            is_active=True
        )


class DataSourceForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = DataSource
        fields = ["code", "name", "description", "source_type", "verification_method"]


class DataCollectionToolForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = DataCollectionTool
        fields = ["code", "name", "description", "tool_type", "template_file"]


class DataCollectionPlanForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = DataCollectionPlan
        fields = [
            "program",
            "project",
            "title",
            "description",
            "start_date",
            "end_date",
            "frequency",
            "tools",
            "enumerators",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        self.fields["project"].required = False
        _choice_field(self, "enumerators").queryset = _user_choices()


class DataSubmissionForm(MEALFormMixin, forms.ModelForm):
    data = forms.JSONField(
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
        help_text=_(
            'Enter a JSON object of collected values, e.g. {"male": 12, "female": 18}'
        ),
    )  # type: ignore[assignment]
    indicator = forms.ModelChoiceField(
        queryset=Indicator.objects.all(), label=_("Indicator")
    )

    class Meta:
        model = DataSubmission
        fields = ["indicator", "submission_date", "data", "evidence_file", "notes"]


class MonitoringPlanForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = MonitoringPlan
        fields = [
            "program",
            "project",
            "title",
            "frequency",
            "next_due_date",
            "responsible_officer",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        self.fields["project"].required = False
        _choice_field(self, "responsible_officer").queryset = _user_choices()


class MonitoringVisitForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = MonitoringVisit
        fields = [
            "program",
            "project",
            "community",
            "visit_date",
            "team",
            "objectives",
            "findings_summary",
            "recommendations",
            "follow_up_due",
            "gps_coordinates",
            "report_file",
            "photo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        self.fields["project"].required = False
        _choice_field(self, "team").queryset = _user_choices()


class MonitoringFindingForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = MonitoringFinding
        fields = ["category", "description", "recommendation"]


class EvaluationForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = [
            "program",
            "project",
            "title",
            "evaluation_type",
            "start_date",
            "end_date",
            "methodology",
            "lead_officer",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        self.fields["project"].required = False
        _choice_field(self, "lead_officer").queryset = _user_choices()


class EvaluationRecommendationForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = EvaluationRecommendation
        fields = [
            "recommendation",
            "category",
            "responsible_officer",
            "due_date",
            "adopted",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _choice_field(self, "responsible_officer").queryset = _user_choices()


class DataQualityAssessmentForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = DataQualityAssessment
        fields = [
            "program",
            "project",
            "title",
            "assessment_date",
            "assessor",
            "scope",
            "overall_score",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        self.fields["project"].required = False
        _choice_field(self, "assessor").queryset = _user_choices()


class DQADimensionScoreForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = DQADimensionScore
        fields = ["dimension", "score", "findings"]


class ComplaintForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = Complaint
        fields = [
            "program",
            "project",
            "beneficiary",
            "submission_date",
            "source",
            "category",
            "channel",
            "description",
            "priority",
            "is_confidential",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        self.fields["project"].required = False
        self.fields["beneficiary"].required = False


class ComplaintResolutionForm(MEALFormMixin, forms.Form):
    resolution = forms.CharField(
        label=_("Resolution"),
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text=_("Describe the investigation outcome and resolution."),
    )
    notes = forms.CharField(
        label=_("Notes"), widget=forms.Textarea(attrs={"rows": 2}), required=False
    )


class FeedbackForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = Feedback
        fields = [
            "program",
            "project",
            "beneficiary",
            "submission_date",
            "source",
            "category",
            "channel",
            "description",
            "is_confidential",
            "satisfaction_rating",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        self.fields["project"].required = False
        self.fields["beneficiary"].required = False


class FeedbackResponseForm(MEALFormMixin, forms.Form):
    response = forms.CharField(
        label=_("Response"),
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text=_("Record the response shared with the complainant."),
    )
    notes = forms.CharField(
        label=_("Notes"), widget=forms.Textarea(attrs={"rows": 2}), required=False
    )


class CorrectiveActionForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = CorrectiveAction
        fields = [
            "title",
            "description",
            "finding",
            "dqa",
            "complaint",
            "feedback",
            "assigned_to",
            "priority",
            "due_date",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _choice_field(self, "assigned_to").queryset = _user_choices()


class CorrectiveActionResolutionForm(MEALFormMixin, forms.Form):
    resolution = forms.CharField(
        label=_("Resolution"),
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text=_("Describe how the corrective action was completed."),
    )
    notes = forms.CharField(
        label=_("Notes"), widget=forms.Textarea(attrs={"rows": 2}), required=False
    )


class OutcomeHarvestForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = OutcomeHarvest
        fields = [
            "program",
            "project",
            "title",
            "category",
            "outcome_description",
            "evidence",
            "contributing_factors",
            "stakeholders",
            "verification_method",
            "lessons_learned",
            "sustainability",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        self.fields["project"].required = False


class LearningLogForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = LearningLog
        fields = [
            "program",
            "project",
            "log_date",
            "source",
            "category",
            "description",
            "recommendation",
            "responsible_officer",
            "follow_up_actions",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        self.fields["project"].required = False
        _choice_field(self, "responsible_officer").queryset = _user_choices()


class BestPracticeForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = BestPractice
        fields = [
            "program",
            "project",
            "title",
            "description",
            "evidence",
            "results_achieved",
            "replication_guidance",
            "responsible_officer",
            "evidence_file",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        self.fields["project"].required = False
        _choice_field(self, "responsible_officer").queryset = _user_choices()


class LessonLearnedForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = LessonLearned
        fields = [
            "program",
            "project",
            "title",
            "category",
            "context",
            "observation",
            "analysis",
            "recommendation",
            "responsible_team",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        self.fields["project"].required = False


class PerformanceScorecardForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = PerformanceScorecard
        fields = [
            "program",
            "title",
            "period_label",
            "period_start",
            "period_end",
            "period_type",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False


class ScorecardDimensionRowForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = ScorecardDimension
        fields = ["dimension", "label", "target", "actual", "score", "notes"]


class OrganizationalKPIForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = OrganizationalKPI
        fields = [
            "code",
            "name",
            "description",
            "formula",
            "unit",
            "target_value",
            "frequency",
            "responsible_officer",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _choice_field(self, "responsible_officer").queryset = _user_choices()


class MEALReportForm(MEALFormMixin, forms.ModelForm):
    class Meta:
        model = MEALReport
        fields = [
            "program",
            "project",
            "title",
            "report_type",
            "period_start",
            "period_end",
            "content",
            "file",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].required = False
        self.fields["project"].required = False


class TransitionForm(MEALFormMixin, forms.Form):
    """Confirm a workflow transition with optional notes."""

    notes = forms.CharField(
        label=_("Notes"), widget=forms.Textarea(attrs={"rows": 2}), required=False
    )

    def __init__(self, *args, choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if choices is not None:
            self.fields["to_status"] = forms.ChoiceField(
                label=_("Transition to"),
                choices=choices,
                widget=forms.Select(attrs={"class": "form-select"}),
            )
