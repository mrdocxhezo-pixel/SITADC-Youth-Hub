"""Views for the Monitoring, Evaluation, Accountability & Learning module.

All views are permission checked (``meal.*`` codes with a ``meal.manage``
override) and read through the confidentiality-aware selectors so that
unauthorized actors can neither see nor modify restricted records.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any, ClassVar

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView

from apps.rbac.authorization import user_has_permission

from .constants import (
    ComplaintStatus,
    FeedbackStatus,
    IndicatorStatus,
    MonitoringVisitStatus,
)
from .exports import (
    complaint_register_csv_response,
    evaluation_register_csv_response,
    feedback_register_csv_response,
    indicator_register_csv_response,
    lesson_register_csv_response,
    meal_report_export_response,
    meal_report_register_csv_response,
    monitoring_visit_register_csv_response,
)
from .forms import (
    BestPracticeForm,
    ComplaintForm,
    ComplaintResolutionForm,
    CorrectiveActionForm,
    CorrectiveActionResolutionForm,
    DataCollectionPlanForm,
    DataQualityAssessmentForm,
    DataSubmissionForm,
    EvaluationForm,
    FeedbackForm,
    FeedbackResponseForm,
    IndicatorForm,
    LearningLogForm,
    LessonLearnedForm,
    LogicalFrameworkForm,
    MEALReportForm,
    MonitoringFindingForm,
    MonitoringPlanForm,
    MonitoringVisitForm,
    OrganizationalKPIForm,
    OutcomeHarvestForm,
    PerformanceScorecardForm,
    ResultsFrameworkForm,
    TheoryOfChangeForm,
    TransitionForm,
)
from .models import (
    BestPractice,
    Complaint,
    CorrectiveAction,
    DataCollectionPlan,
    DataQualityAssessment,
    Evaluation,
    Feedback,
    Indicator,
    LearningLog,
    LessonLearned,
    LogicalFramework,
    MEALReport,
    MEALStatusHistory,
    MonitoringPlan,
    MonitoringVisit,
    OrganizationalKPI,
    OutcomeHarvest,
    PerformanceScorecard,
    ResultsFramework,
    TheoryOfChange,
)
from .permissions import (
    MEAL_APPROVE,
    MEAL_ARCHIVE,
    MEAL_CREATE,
    MEAL_EXPORT,
    MEAL_MANAGE,
    MEAL_MANAGE_ACCOUNTABILITY,
    MEAL_MANAGE_DATA_COLLECTION,
    MEAL_MANAGE_DQA,
    MEAL_MANAGE_EVALUATIONS,
    MEAL_MANAGE_INDICATORS,
    MEAL_MANAGE_LEARNING,
    MEAL_MANAGE_MONITORING,
    MEAL_MANAGE_REPORTS,
    MEAL_MANAGE_SCORECARDS,
    MEAL_RESTORE,
    MEAL_SUBMIT,
    MEAL_UPDATE,
    MEAL_VIEW,
)
from .selectors import meal_queryset, visible_complaints, visible_feedback
from .services import (
    AccountabilityService,
    DataCollectionService,
    DQAService,
    EvaluationService,
    FrameworkService,
    IndicatorService,
    LearningService,
    MEALService,
    MonitoringService,
    ReportService,
    ScorecardService,
)

logger = logging.getLogger(__name__)


def _can(user, *permission_codes: str) -> bool:
    return bool(
        user_has_permission(user, MEAL_MANAGE)
        or any(user_has_permission(user, code) for code in permission_codes)
    )


def _apply_service_errors(form, exc: ValidationError | PermissionDenied) -> None:
    if isinstance(exc, PermissionDenied):
        form.add_error(None, str(exc))
        return
    if hasattr(exc, "message_dict"):
        for field_name, field_messages in exc.message_dict.items():
            target = field_name if field_name in form.fields else None
            for message in field_messages:
                form.add_error(target, message)
        return
    for message in exc.messages:
        form.add_error(None, message)


def _scoped(user, model, pk, *, include_archived: bool = False):
    return get_object_or_404(
        meal_queryset(user, model, include_archived=include_archived), pk=pk
    )


def _scoped_visible(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        visible_complaints(user, include_archived=include_archived), pk=pk
    )


def _scoped_feedback(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        visible_feedback(user, include_archived=include_archived), pk=pk
    )


class MealPermissionMixin(PermissionRequiredMixin):
    """Allow any listed MEAL permission, with module-manager override.

    The ``meal.*`` codes are stored as literal permission codenames, so the
    inherited ``has_perm()`` lookup (``<app>.<codename>``) can never match.
    ``has_permission()`` is therefore overridden to resolve the codes through
    ``user_has_permission`` instead.
    """

    request: HttpRequest

    def has_permission(self) -> bool:
        required = self.permission_required
        permissions = (required,) if isinstance(required, str) else tuple(required)
        return _can(self.request.user, *permissions)


def _status_summary(queryset, status_field: str = "status"):
    return list(
        queryset.values(status_field).annotate(total=Count("id")).order_by(status_field)
    )


# ── Dashboard ────────────────────────────────────────────────────────────


class MealDashboardView(MealPermissionMixin, TemplateView):
    template_name = "meal/dashboard.html"
    permission_required = MEAL_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        indicators = meal_queryset(user, Indicator)
        complaints = visible_complaints(user)
        feedback = visible_feedback(user)
        visits = meal_queryset(user, MonitoringVisit)
        evaluations = meal_queryset(user, Evaluation)
        reports = meal_queryset(user, MEALReport)
        corrective_actions = meal_queryset(user, CorrectiveAction)
        lessons = meal_queryset(user, LessonLearned)
        harvests = meal_queryset(user, OutcomeHarvest)
        context.update(
            {
                "metrics": {
                    "indicators": indicators.count(),
                    "active_indicators": indicators.filter(
                        status=IndicatorStatus.ACTIVE
                    ).count(),
                    "visits": visits.count(),
                    "open_complaints": complaints.filter(
                        status__in=[
                            ComplaintStatus.RECEIVED,
                            ComplaintStatus.ASSIGNED,
                            ComplaintStatus.UNDER_INVESTIGATION,
                        ]
                    ).count(),
                    "open_feedback": feedback.exclude(
                        status=FeedbackStatus.CLOSED
                    ).count(),
                    "open_actions": corrective_actions.exclude(
                        status__in=["CLOSED", "CANCELLED", "VERIFIED"]
                    ).count(),
                    "evaluations": evaluations.count(),
                    "draft_reports": reports.filter(status="DRAFT").count(),
                    "lessons": lessons.count(),
                    "harvests": harvests.count(),
                },
                "complaint_status_summary": _status_summary(complaints),
                "visit_status_summary": _status_summary(visits),
                "indicator_status_summary": _status_summary(indicators),
                "recent_activity": MEALStatusHistory.objects.all()[:10],
                "can_create": _can(user, MEAL_CREATE),
            }
        )
        return context


# ── Generic entity CRUD ──────────────────────────────────────────────────


class MealEntityCreateView(MealPermissionMixin, FormView):
    """Create any MEAL entity through its service."""

    form_class: Any = None
    model: ClassVar[type[models.Model] | None] = None
    service_class = MEALService
    entity_label = "Record"
    template_name = "meal/entity_form.html"
    permission_required = MEAL_CREATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = self.entity_label
        context["is_update"] = False
        return context

    def form_valid(self, form):
        try:
            instance = self.service_class(user=self.request.user).create(
                fields=form.cleaned_data, model=self.model
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"{self.entity_label} created successfully.",
        )
        return redirect(self.get_success_url_for(instance))

    def get_success_url_for(self, instance) -> str:
        raise NotImplementedError


class MealEntityUpdateView(MealPermissionMixin, FormView):
    """Update any MEAL entity through its service."""

    form_class: Any = None
    model: ClassVar[type[models.Model] | None] = None
    service_class = MEALService
    entity_label = "Record"
    template_name = "meal/entity_form.html"
    permission_required = MEAL_UPDATE

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = _scoped(self.request.user, self.model, self.kwargs["pk"])
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        context["entity_label"] = self.entity_label
        context["is_update"] = True
        return context

    def form_valid(self, form):
        try:
            instance = self.service_class(user=self.request.user).update(
                instance=self.get_object(), fields=form.cleaned_data
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, f"{self.entity_label} updated successfully.")
        return redirect(self.get_success_url_for(instance))

    def get_success_url_for(self, instance) -> str:
        raise NotImplementedError


class MealArchiveView(MealPermissionMixin, View):
    model: ClassVar[type[models.Model] | None] = None
    service_class = MEALService
    permission_required = MEAL_ARCHIVE
    success_url_name: ClassVar[str] = ""

    def post(self, request, *args, **kwargs):
        instance = _scoped(request.user, self.model, kwargs["pk"])
        self.service_class(user=request.user).archive(instance=instance)
        messages.success(request, "Record archived successfully.")
        return redirect(self.success_url_name, pk=instance.pk)


class MealRestoreView(MealPermissionMixin, View):
    model: ClassVar[type[models.Model] | None] = None
    service_class = MEALService
    permission_required = MEAL_RESTORE
    success_url_name: ClassVar[str] = ""

    def post(self, request, *args, **kwargs):
        instance = _scoped(
            request.user, self.model, kwargs["pk"], include_archived=True
        )
        self.service_class(user=request.user).restore(instance=instance)
        messages.success(request, "Record restored successfully.")
        return redirect(self.success_url_name, pk=instance.pk)


class MealTransitionView(MealPermissionMixin, FormView):
    """Generic status transition form (to_status + notes)."""

    template_name = "meal/workflow_form.html"
    form_class = TransitionForm
    service_class = MEALService
    action_method = "transition"
    model: ClassVar[type[models.Model] | None] = None
    permission_required: str | Sequence[str] = MEAL_MANAGE
    entity_label = "Record"
    success_url_name: ClassVar[str] = ""
    transition_permission = MEAL_MANAGE
    permission_by_status: ClassVar[dict[str, str]] = {}

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = _scoped(self.request.user, self.model, self.kwargs["pk"])
        return self.object

    def get_form(self, form_class=None):
        form_class = form_class or self.form_class
        allowed = [
            (choice, choice.replace("_", " ").title())
            for choice in sorted(
                self.service_class.transitions.get(self.get_object().status, set())
            )
            if _can(
                self.request.user,
                self.permission_by_status.get(choice, self.transition_permission),
            )
        ]
        return form_class(**self.get_form_kwargs(), choices=allowed)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        context["entity_label"] = self.entity_label
        return context

    def form_valid(self, form):
        instance = self.get_object()
        to_status = form.cleaned_data["to_status"]
        service = self.service_class(user=self.request.user)
        method = getattr(service, self.action_method)
        try:
            updated = method(
                instance=instance,
                to_status=to_status,
                permission_code=self.permission_by_status.get(
                    to_status, self.transition_permission
                ),
                notes=form.cleaned_data.get("notes", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, f"{self.entity_label} status updated.")
        return redirect(self.get_success_url_for(updated))

    def get_success_url_for(self, instance) -> str:
        return self.request.path.rsplit("/actions/", 1)[0] + "/"


# ── Indicators ───────────────────────────────────────────────────────────


class IndicatorRegistryView(MealPermissionMixin, ListView):
    model = Indicator
    template_name = "meal/indicator_registry.html"
    context_object_name = "indicators"
    paginate_by = 24
    permission_required = MEAL_VIEW

    def get_queryset(self):
        queryset = meal_queryset(self.request.user, Indicator).select_related(
            "category", "unit", "responsible_officer"
        )
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(reference_number__icontains=search)
                | Q(code__icontains=search)
                | Q(title__icontains=search)
            )
        status = self.request.GET.get("status", "")
        if status in IndicatorStatus.values:
            queryset = queryset.filter(status=status)
        indicator_type = self.request.GET.get("type", "")
        if indicator_type:
            queryset = queryset.filter(indicator_type=indicator_type)
        return queryset.order_by("code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop("page", None)
        user = self.request.user
        context.update(
            {
                "status_choices": IndicatorStatus.choices,
                "type_choices": self.model._meta.get_field("indicator_type").choices,
                "query_without_page": query.urlencode(),
                "can_create": _can(user, MEAL_CREATE),
                "can_manage": _can(user, MEAL_MANAGE_INDICATORS),
            }
        )
        return context


class IndicatorCreateView(MealEntityCreateView):
    form_class = IndicatorForm
    model = Indicator
    service_class = IndicatorService
    entity_label = "Indicator"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return self.request.path.replace("/new/", f"/{instance.pk}/")


class IndicatorUpdateView(MealEntityUpdateView):
    form_class = IndicatorForm
    model = Indicator
    service_class = IndicatorService
    entity_label = "Indicator"
    permission_required = MEAL_UPDATE

    def get_success_url_for(self, instance) -> str:
        return self.request.path.rsplit("/edit/", 1)[0] + "/"


class IndicatorDetailView(MealPermissionMixin, DetailView):
    model = Indicator
    template_name = "meal/indicator_detail.html"
    context_object_name = "indicator"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, Indicator).select_related(
            "category", "unit", "responsible_officer"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        indicator = self.object
        context.update(
            {
                "baselines": indicator.baselines.all(),
                "targets": indicator.targets.all(),
                "results": indicator.results.all(),
                "can_manage": _can(user, MEAL_MANAGE_INDICATORS),
                "can_update": _can(user, MEAL_UPDATE),
            }
        )
        return context


class IndicatorActivateView(MealPermissionMixin, View):
    permission_required = MEAL_MANAGE_INDICATORS

    def post(self, request, *args, **kwargs):
        indicator = _scoped(request.user, Indicator, kwargs["pk"])
        IndicatorService(user=request.user).activate(instance=indicator)
        messages.success(request, "Indicator activated.")
        return redirect("meal:indicator_detail", pk=indicator.pk)


# ── Frameworks ───────────────────────────────────────────────────────────


class TheoryOfChangeCreateView(MealEntityCreateView):
    form_class = TheoryOfChangeForm
    model = TheoryOfChange
    service_class = FrameworkService
    entity_label = "Theory of Change"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/frameworks/theories-of-change/{instance.pk}/"


class TheoryOfChangeUpdateView(MealEntityUpdateView):
    form_class = TheoryOfChangeForm
    model = TheoryOfChange
    service_class = FrameworkService
    entity_label = "Theory of Change"
    permission_required = MEAL_UPDATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/frameworks/theories-of-change/{instance.pk}/"


class TheoryOfChangeDetailView(MealPermissionMixin, DetailView):
    model = TheoryOfChange
    template_name = "meal/framework_profile.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, TheoryOfChange).select_related(
            "program"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Theory of Change"
        context["can_update"] = _can(self.request.user, MEAL_UPDATE)
        context["can_approve"] = _can(self.request.user, MEAL_APPROVE)
        context["can_submit"] = _can(self.request.user, MEAL_SUBMIT)
        context["can_archive"] = _can(self.request.user, MEAL_ARCHIVE)
        context["actions_url_name"] = "meal:theory_of_change_actions"
        context["edit_url_name"] = "meal:theory_of_change_edit"
        return context


class ResultsFrameworkCreateView(MealEntityCreateView):
    form_class = ResultsFrameworkForm
    model = ResultsFramework
    service_class = FrameworkService
    entity_label = "Results Framework"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/frameworks/results-frameworks/{instance.pk}/"


class ResultsFrameworkUpdateView(MealEntityUpdateView):
    form_class = ResultsFrameworkForm
    model = ResultsFramework
    service_class = FrameworkService
    entity_label = "Results Framework"
    permission_required = MEAL_UPDATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/frameworks/results-frameworks/{instance.pk}/"


class ResultsFrameworkDetailView(MealPermissionMixin, DetailView):
    model = ResultsFramework
    template_name = "meal/framework_profile.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, ResultsFramework).prefetch_related(
            "statements"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Results Framework"
        context["can_update"] = _can(self.request.user, MEAL_UPDATE)
        context["can_approve"] = _can(self.request.user, MEAL_APPROVE)
        context["can_submit"] = _can(self.request.user, MEAL_SUBMIT)
        context["can_archive"] = _can(self.request.user, MEAL_ARCHIVE)
        context["actions_url_name"] = "meal:results_framework_actions"
        context["edit_url_name"] = "meal:results_framework_edit"
        return context


class LogicalFrameworkCreateView(MealEntityCreateView):
    form_class = LogicalFrameworkForm
    model = LogicalFramework
    service_class = FrameworkService
    entity_label = "Logical Framework"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/frameworks/logframes/{instance.pk}/"


class LogicalFrameworkUpdateView(MealEntityUpdateView):
    form_class = LogicalFrameworkForm
    model = LogicalFramework
    service_class = FrameworkService
    entity_label = "Logical Framework"
    permission_required = MEAL_UPDATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/frameworks/logframes/{instance.pk}/"


class LogicalFrameworkDetailView(MealPermissionMixin, DetailView):
    model = LogicalFramework
    template_name = "meal/framework_profile.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, LogicalFramework).prefetch_related(
            "rows"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Logical Framework"
        context["can_update"] = _can(self.request.user, MEAL_UPDATE)
        context["can_approve"] = _can(self.request.user, MEAL_APPROVE)
        context["can_submit"] = _can(self.request.user, MEAL_SUBMIT)
        context["can_archive"] = _can(self.request.user, MEAL_ARCHIVE)
        context["actions_url_name"] = "meal:logical_framework_actions"
        context["edit_url_name"] = "meal:logical_framework_edit"
        return context


# ── Data collection ──────────────────────────────────────────────────────


class DataCollectionPlanCreateView(MealEntityCreateView):
    form_class = DataCollectionPlanForm
    model = DataCollectionPlan
    service_class = DataCollectionService
    entity_label = "Data Collection Plan"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/data-collection/{instance.pk}/"


class DataCollectionPlanUpdateView(MealEntityUpdateView):
    form_class = DataCollectionPlanForm
    model = DataCollectionPlan
    service_class = DataCollectionService
    entity_label = "Data Collection Plan"
    permission_required = MEAL_UPDATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/data-collection/{instance.pk}/"


class DataCollectionPlanDetailView(MealPermissionMixin, DetailView):
    model = DataCollectionPlan
    template_name = "meal/entity_detail.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, DataCollectionPlan)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Data Collection Plan"
        context["submissions"] = self.object.submissions.select_related("indicator")[
            :20
        ]
        return context


class DataSubmissionCreateView(MealPermissionMixin, FormView):
    form_class = DataSubmissionForm
    template_name = "meal/entity_form.html"
    permission_required = MEAL_MANAGE_DATA_COLLECTION

    def get_plan(self):
        return _scoped(self.request.user, DataCollectionPlan, self.kwargs["plan_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Data Submission"
        context["plan"] = self.get_plan()
        return context

    def form_valid(self, form):
        try:
            DataCollectionService(user=self.request.user).create_submission(
                plan=self.get_plan(),
                indicator=form.cleaned_data["indicator"],
                fields=form.cleaned_data,
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Data submission created.")
        return redirect("meal:data_collection_detail", pk=self.get_plan().pk)


# ── Monitoring ───────────────────────────────────────────────────────────


class MonitoringPlanCreateView(MealEntityCreateView):
    form_class = MonitoringPlanForm
    model = MonitoringPlan
    service_class = MonitoringService
    entity_label = "Monitoring Plan"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/monitoring/plans/{instance.pk}/"


class MonitoringPlanUpdateView(MealEntityUpdateView):
    form_class = MonitoringPlanForm
    model = MonitoringPlan
    service_class = MonitoringService
    entity_label = "Monitoring Plan"
    permission_required = MEAL_UPDATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/monitoring/plans/{instance.pk}/"


class MonitoringPlanDetailView(MealPermissionMixin, DetailView):
    model = MonitoringPlan
    template_name = "meal/entity_detail.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, MonitoringPlan)


class MonitoringVisitCreateView(MealEntityCreateView):
    form_class = MonitoringVisitForm
    model = MonitoringVisit
    service_class = MonitoringService
    entity_label = "Monitoring Visit"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/monitoring/visits/{instance.pk}/"


class MonitoringVisitUpdateView(MealEntityUpdateView):
    form_class = MonitoringVisitForm
    model = MonitoringVisit
    service_class = MonitoringService
    entity_label = "Monitoring Visit"
    permission_required = MEAL_UPDATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/monitoring/visits/{instance.pk}/"


class MonitoringVisitDirectoryView(MealPermissionMixin, ListView):
    model = MonitoringVisit
    template_name = "meal/entity_directory.html"
    context_object_name = "records"
    paginate_by = 24
    permission_required = MEAL_VIEW

    def get_queryset(self):
        queryset = meal_queryset(self.request.user, MonitoringVisit).select_related(
            "program", "project"
        )
        status = self.request.GET.get("status", "")
        if status in MonitoringVisitStatus.values:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-visit_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Monitoring Visits"
        context["status_choices"] = MonitoringVisitStatus.choices
        context["can_create"] = _can(self.request.user, MEAL_CREATE)
        context["create_url_name"] = "meal:monitoring_visit_create"
        context["detail_url_name"] = "meal:monitoring_visit_detail"
        return context


class MonitoringVisitDetailView(MealPermissionMixin, DetailView):
    model = MonitoringVisit
    template_name = "meal/monitoring_visit_detail.html"
    context_object_name = "visit"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, MonitoringVisit).select_related(
            "program", "project"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["findings"] = self.object.findings.all()
        context["can_manage"] = _can(self.request.user, MEAL_MANAGE_MONITORING)
        return context


class MonitoringFindingCreateView(MealPermissionMixin, FormView):
    form_class = MonitoringFindingForm
    template_name = "meal/entity_form.html"
    permission_required = MEAL_MANAGE_MONITORING

    def get_visit(self):
        return _scoped(self.request.user, MonitoringVisit, self.kwargs["visit_pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["visit"] = self.get_visit()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Monitoring Finding"
        context["visit"] = self.get_visit()
        return context

    def form_valid(self, form):
        try:
            MonitoringService(user=self.request.user).create_finding(
                visit=self.get_visit(), fields=form.cleaned_data
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Finding recorded.")
        return redirect("meal:monitoring_visit_detail", pk=self.get_visit().pk)


# ── Evaluations ──────────────────────────────────────────────────────────


class EvaluationCreateView(MealEntityCreateView):
    form_class = EvaluationForm
    model = Evaluation
    service_class = EvaluationService
    entity_label = "Evaluation"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/evaluations/{instance.pk}/"


class EvaluationUpdateView(MealEntityUpdateView):
    form_class = EvaluationForm
    model = Evaluation
    service_class = EvaluationService
    entity_label = "Evaluation"
    permission_required = MEAL_UPDATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/evaluations/{instance.pk}/"


class EvaluationDirectoryView(MealPermissionMixin, ListView):
    model = Evaluation
    template_name = "meal/entity_directory.html"
    context_object_name = "records"
    paginate_by = 24
    permission_required = MEAL_VIEW

    def get_queryset(self):
        queryset = meal_queryset(self.request.user, Evaluation).select_related(
            "program", "project"
        )
        status = self.request.GET.get("status", "")
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-start_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Evaluations"
        context["status_choices"] = self.model._meta.get_field("status").choices
        context["can_create"] = _can(self.request.user, MEAL_CREATE)
        context["create_url_name"] = "meal:evaluation_create"
        context["detail_url_name"] = "meal:evaluation_detail"
        return context


class EvaluationDetailView(MealPermissionMixin, DetailView):
    model = Evaluation
    template_name = "meal/entity_detail.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, Evaluation).select_related(
            "program", "project"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Evaluation"
        context["recommendations"] = self.object.recommendations.all()[:10]
        return context


# ── DQA ──────────────────────────────────────────────────────────────────


class DQACreateView(MealEntityCreateView):
    form_class = DataQualityAssessmentForm
    model = DataQualityAssessment
    service_class = DQAService
    entity_label = "Data Quality Assessment"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/dqa/{instance.pk}/"


class DQADetailView(MealPermissionMixin, DetailView):
    model = DataQualityAssessment
    template_name = "meal/entity_detail.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, DataQualityAssessment)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Data Quality Assessment"
        context["dimension_scores"] = self.object.dimension_scores.all()
        return context


# ── Accountability ───────────────────────────────────────────────────────


class ComplaintCreateView(MealPermissionMixin, FormView):
    form_class = ComplaintForm
    template_name = "meal/entity_form.html"
    permission_required = MEAL_CREATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Complaint"
        return context

    def form_valid(self, form):
        try:
            complaint = AccountabilityService(user=self.request.user).create(
                fields=form.cleaned_data, model=Complaint
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Complaint received.")
        return redirect("meal:complaint_detail", pk=complaint.pk)


class ComplaintDirectoryView(MealPermissionMixin, ListView):
    model = Complaint
    template_name = "meal/complaint_directory.html"
    context_object_name = "complaints"
    paginate_by = 24
    permission_required = MEAL_VIEW

    def get_queryset(self):
        queryset = visible_complaints(self.request.user).select_related(
            "category", "channel", "program"
        )
        status = self.request.GET.get("status", "")
        if status in ComplaintStatus.values:
            queryset = queryset.filter(status=status)
        priority = self.request.GET.get("priority", "")
        if priority:
            queryset = queryset.filter(priority=priority)
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(reference_number__icontains=search) | Q(description__icontains=search)
            )
        return queryset.order_by("-submission_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = ComplaintStatus.choices
        context["can_create"] = _can(self.request.user, MEAL_CREATE)
        context["can_manage"] = _can(self.request.user, MEAL_MANAGE_ACCOUNTABILITY)
        return context


class ComplaintDetailView(MealPermissionMixin, DetailView):
    model = Complaint
    template_name = "meal/complaint_detail.html"
    context_object_name = "complaint"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return visible_complaints(self.request.user).select_related(
            "category", "channel", "program", "project", "beneficiary"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage"] = _can(self.request.user, MEAL_MANAGE_ACCOUNTABILITY)
        context["is_confidential"] = self.object.is_confidential
        return context


class ComplaintResolveView(MealPermissionMixin, FormView):
    form_class = ComplaintResolutionForm
    template_name = "meal/workflow_form.html"
    permission_required = MEAL_MANAGE_ACCOUNTABILITY

    def get_object(self):
        return _scoped_visible(self.request.user, self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        context["entity_label"] = "Resolve Complaint"
        return context

    def form_valid(self, form):
        try:
            complaint = AccountabilityService(user=self.request.user).resolve_complaint(
                instance=self.get_object(), resolution=form.cleaned_data["resolution"]
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Complaint resolved.")
        return redirect("meal:complaint_detail", pk=complaint.pk)


class ComplaintCloseView(MealPermissionMixin, View):
    permission_required = MEAL_MANAGE_ACCOUNTABILITY

    def post(self, request, *args, **kwargs):
        complaint = _scoped_visible(request.user, kwargs["pk"])
        AccountabilityService(user=request.user).close_complaint(instance=complaint)
        messages.success(request, "Complaint closed.")
        return redirect("meal:complaint_detail", pk=complaint.pk)


class FeedbackCreateView(MealPermissionMixin, FormView):
    form_class = FeedbackForm
    template_name = "meal/entity_form.html"
    permission_required = MEAL_CREATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Feedback"
        return context

    def form_valid(self, form):
        try:
            feedback = AccountabilityService(user=self.request.user).create(
                fields=form.cleaned_data, model=Feedback
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Feedback received.")
        return redirect("meal:feedback_detail", pk=feedback.pk)


class FeedbackDirectoryView(MealPermissionMixin, ListView):
    model = Feedback
    template_name = "meal/entity_directory.html"
    context_object_name = "records"
    paginate_by = 24
    permission_required = MEAL_VIEW

    def get_queryset(self):
        queryset = visible_feedback(self.request.user).select_related("category")
        status = self.request.GET.get("status", "")
        if status in FeedbackStatus.values:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-submission_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Feedback"
        context["status_choices"] = FeedbackStatus.choices
        context["can_create"] = _can(self.request.user, MEAL_CREATE)
        context["create_url_name"] = "meal:feedback_create"
        context["detail_url_name"] = "meal:feedback_detail"
        return context


class FeedbackDetailView(MealPermissionMixin, DetailView):
    model = Feedback
    template_name = "meal/feedback_detail.html"
    context_object_name = "feedback"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return visible_feedback(self.request.user).select_related(
            "category", "channel", "program", "beneficiary"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage"] = _can(self.request.user, MEAL_MANAGE_ACCOUNTABILITY)
        return context


class FeedbackRespondView(MealPermissionMixin, FormView):
    form_class = FeedbackResponseForm
    template_name = "meal/workflow_form.html"
    permission_required = MEAL_MANAGE_ACCOUNTABILITY

    def get_object(self):
        return _scoped_feedback(self.request.user, self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        context["entity_label"] = "Respond to Feedback"
        return context

    def form_valid(self, form):
        try:
            feedback = AccountabilityService(user=self.request.user).respond_feedback(
                instance=self.get_object(), response=form.cleaned_data["response"]
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Feedback response recorded.")
        return redirect("meal:feedback_detail", pk=feedback.pk)


class FeedbackCloseView(MealPermissionMixin, View):
    permission_required = MEAL_MANAGE_ACCOUNTABILITY

    def post(self, request, *args, **kwargs):
        feedback = _scoped_feedback(request.user, kwargs["pk"])
        AccountabilityService(user=request.user).close_feedback(instance=feedback)
        messages.success(request, "Feedback closed.")
        return redirect("meal:feedback_detail", pk=feedback.pk)


class CorrectiveActionCreateView(MealEntityCreateView):
    form_class = CorrectiveActionForm
    model = CorrectiveAction
    service_class = AccountabilityService
    entity_label = "Corrective Action"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/accountability/corrective-actions/{instance.pk}/"


class CorrectiveActionDetailView(MealPermissionMixin, DetailView):
    model = CorrectiveAction
    template_name = "meal/entity_detail.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, CorrectiveAction)


class CorrectiveActionResolveView(MealPermissionMixin, FormView):
    form_class = CorrectiveActionResolutionForm
    template_name = "meal/workflow_form.html"
    permission_required = MEAL_MANAGE_ACCOUNTABILITY

    def get_object(self):
        return _scoped(self.request.user, CorrectiveAction, self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        context["entity_label"] = "Complete Corrective Action"
        return context

    def form_valid(self, form):
        try:
            action = AccountabilityService(
                user=self.request.user
            ).complete_corrective_action(
                instance=self.get_object(), resolution=form.cleaned_data["resolution"]
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Corrective action completed.")
        return redirect("meal:corrective_action_detail", pk=action.pk)


class CorrectiveActionVerifyView(MealPermissionMixin, View):
    permission_required = MEAL_MANAGE_ACCOUNTABILITY

    def post(self, request, *args, **kwargs):
        action = _scoped(request.user, CorrectiveAction, kwargs["pk"])
        AccountabilityService(user=request.user).verify_corrective_action(
            instance=action
        )
        messages.success(request, "Corrective action verified.")
        return redirect("meal:corrective_action_detail", pk=action.pk)


# ── Learning ─────────────────────────────────────────────────────────────


class OutcomeHarvestCreateView(MealEntityCreateView):
    form_class = OutcomeHarvestForm
    model = OutcomeHarvest
    service_class = LearningService
    entity_label = "Outcome Harvest"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/learning/outcome-harvests/{instance.pk}/"


class OutcomeHarvestDetailView(MealPermissionMixin, DetailView):
    model = OutcomeHarvest
    template_name = "meal/entity_detail.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, OutcomeHarvest)


class LearningLogCreateView(MealEntityCreateView):
    form_class = LearningLogForm
    model = LearningLog
    service_class = LearningService
    entity_label = "Learning Log"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/learning/logs/{instance.pk}/"


class LearningLogDetailView(MealPermissionMixin, DetailView):
    model = LearningLog
    template_name = "meal/entity_detail.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, LearningLog)


class BestPracticeCreateView(MealEntityCreateView):
    form_class = BestPracticeForm
    model = BestPractice
    service_class = LearningService
    entity_label = "Best Practice"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/learning/best-practices/{instance.pk}/"


class BestPracticeDetailView(MealPermissionMixin, DetailView):
    model = BestPractice
    template_name = "meal/entity_detail.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, BestPractice)


class LessonLearnedCreateView(MealEntityCreateView):
    form_class = LessonLearnedForm
    model = LessonLearned
    service_class = LearningService
    entity_label = "Lesson Learned"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/learning/lessons/{instance.pk}/"


class LessonLearnedDetailView(MealPermissionMixin, DetailView):
    model = LessonLearned
    template_name = "meal/entity_detail.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, LessonLearned)


# ── Scorecards & KPIs ────────────────────────────────────────────────────


class PerformanceScorecardCreateView(MealEntityCreateView):
    form_class = PerformanceScorecardForm
    model = PerformanceScorecard
    service_class = ScorecardService
    entity_label = "Performance Scorecard"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/scorecards/{instance.pk}/"


class PerformanceScorecardDetailView(MealPermissionMixin, DetailView):
    model = PerformanceScorecard
    template_name = "meal/scorecard_detail.html"
    context_object_name = "scorecard"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, PerformanceScorecard)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dimensions"] = self.object.dimensions.all()
        context["can_manage"] = _can(self.request.user, MEAL_MANAGE_SCORECARDS)
        return context


class OrganizationalKPICreateView(MealEntityCreateView):
    form_class = OrganizationalKPIForm
    model = OrganizationalKPI
    service_class = ScorecardService
    entity_label = "Organizational KPI"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/scorecards/kpis/{instance.pk}/"


class OrganizationalKPIDetailView(MealPermissionMixin, DetailView):
    model = OrganizationalKPI
    template_name = "meal/entity_detail.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, OrganizationalKPI)


# ── Reports ──────────────────────────────────────────────────────────────


class MEALReportCreateView(MealEntityCreateView):
    form_class = MEALReportForm
    model = MEALReport
    service_class = ReportService
    entity_label = "MEAL Report"
    permission_required = MEAL_CREATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/reports/{instance.pk}/"


class MEALReportUpdateView(MealEntityUpdateView):
    form_class = MEALReportForm
    model = MEALReport
    service_class = ReportService
    entity_label = "MEAL Report"
    permission_required = MEAL_UPDATE

    def get_success_url_for(self, instance) -> str:
        return f"/meal/reports/{instance.pk}/"


class MEALReportDirectoryView(MealPermissionMixin, ListView):
    model = MEALReport
    template_name = "meal/entity_directory.html"
    context_object_name = "records"
    paginate_by = 24
    permission_required = MEAL_VIEW

    def get_queryset(self):
        queryset = meal_queryset(self.request.user, MEALReport).select_related(
            "prepared_by"
        )
        status = self.request.GET.get("status", "")
        if status:
            queryset = queryset.filter(status=status)
        report_type = self.request.GET.get("type", "")
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "MEAL Reports"
        context["status_choices"] = self.model._meta.get_field("status").choices
        context["can_create"] = _can(self.request.user, MEAL_CREATE)
        context["can_manage"] = _can(self.request.user, MEAL_MANAGE_REPORTS)
        context["create_url_name"] = "meal:meal_report_create"
        context["detail_url_name"] = "meal:meal_report_detail"
        return context


class MEALReportDetailView(MealPermissionMixin, DetailView):
    model = MEALReport
    template_name = "meal/entity_detail.html"
    context_object_name = "record"
    permission_required = MEAL_VIEW

    def get_queryset(self):
        return meal_queryset(self.request.user, MEALReport).select_related(
            "prepared_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "MEAL Report"
        context["can_export"] = _can(self.request.user, MEAL_EXPORT)
        context["can_manage"] = _can(self.request.user, MEAL_MANAGE_REPORTS)
        return context


# ── Workflow action views ────────────────────────────────────────────────


class TheoryOfChangeTransitionView(MealTransitionView):
    service_class = FrameworkService
    model = TheoryOfChange
    permission_required = (MEAL_SUBMIT, MEAL_APPROVE)
    transition_permission = MEAL_SUBMIT
    entity_label = "Theory of Change"
    permission_by_status: ClassVar[dict[str, str]] = {
        "APPROVED": MEAL_APPROVE,
        "REJECTED": MEAL_APPROVE,
        "SUBMITTED": MEAL_SUBMIT,
        "DRAFT": MEAL_SUBMIT,
        "ARCHIVED": MEAL_ARCHIVE,
    }


class ResultsFrameworkTransitionView(MealTransitionView):
    service_class = FrameworkService
    model = ResultsFramework
    permission_required = (MEAL_SUBMIT, MEAL_APPROVE)
    transition_permission = MEAL_SUBMIT
    entity_label = "Results Framework"
    permission_by_status: ClassVar[dict[str, str]] = {
        "APPROVED": MEAL_APPROVE,
        "REJECTED": MEAL_APPROVE,
        "SUBMITTED": MEAL_SUBMIT,
        "DRAFT": MEAL_SUBMIT,
        "ARCHIVED": MEAL_ARCHIVE,
    }


class LogicalFrameworkTransitionView(MealTransitionView):
    service_class = FrameworkService
    model = LogicalFramework
    permission_required = (MEAL_SUBMIT, MEAL_APPROVE)
    transition_permission = MEAL_SUBMIT
    entity_label = "Logical Framework"
    permission_by_status: ClassVar[dict[str, str]] = {
        "APPROVED": MEAL_APPROVE,
        "REJECTED": MEAL_APPROVE,
        "SUBMITTED": MEAL_SUBMIT,
        "DRAFT": MEAL_SUBMIT,
        "ARCHIVED": MEAL_ARCHIVE,
    }


class EvaluationTransitionView(MealTransitionView):
    service_class = EvaluationService
    model = Evaluation
    permission_required = (MEAL_MANAGE_EVALUATIONS, MEAL_APPROVE)
    transition_permission = MEAL_MANAGE_EVALUATIONS
    entity_label = "Evaluation"
    permission_by_status: ClassVar[dict[str, str]] = {
        "APPROVED": MEAL_APPROVE,
        "PUBLISHED": MEAL_APPROVE,
        "REJECTED": MEAL_APPROVE,
        "ARCHIVED": MEAL_ARCHIVE,
    }


class DataCollectionPlanTransitionView(MealTransitionView):
    service_class = DataCollectionService
    model = DataCollectionPlan
    permission_required = MEAL_MANAGE_DATA_COLLECTION
    transition_permission = MEAL_MANAGE_DATA_COLLECTION
    entity_label = "Data Collection Plan"
    permission_by_status: ClassVar[dict[str, str]] = {"ARCHIVED": MEAL_ARCHIVE}


class MonitoringVisitTransitionView(MealTransitionView):
    service_class = MonitoringService
    model = MonitoringVisit
    permission_required = MEAL_MANAGE_MONITORING
    transition_permission = MEAL_MANAGE_MONITORING
    entity_label = "Monitoring Visit"
    permission_by_status: ClassVar[dict[str, str]] = {"ARCHIVED": MEAL_ARCHIVE}


class DQATransitionView(MealTransitionView):
    service_class = DQAService
    model = DataQualityAssessment
    permission_required = MEAL_MANAGE_DQA
    transition_permission = MEAL_MANAGE_DQA
    entity_label = "Data Quality Assessment"
    permission_by_status: ClassVar[dict[str, str]] = {"ARCHIVED": MEAL_ARCHIVE}


class MEALReportTransitionView(MealTransitionView):
    service_class = ReportService
    model = MEALReport
    permission_required = (MEAL_SUBMIT, MEAL_APPROVE)
    transition_permission = MEAL_SUBMIT
    entity_label = "MEAL Report"
    permission_by_status: ClassVar[dict[str, str]] = {
        "APPROVED": MEAL_APPROVE,
        "RETURNED": MEAL_APPROVE,
        "SUBMITTED": MEAL_SUBMIT,
        "DRAFT": MEAL_SUBMIT,
        "ARCHIVED": MEAL_ARCHIVE,
    }


class BestPracticeTransitionView(MealTransitionView):
    service_class = LearningService
    model = BestPractice
    permission_required = (MEAL_MANAGE_LEARNING, MEAL_APPROVE)
    transition_permission = MEAL_MANAGE_LEARNING
    entity_label = "Best Practice"
    permission_by_status: ClassVar[dict[str, str]] = {
        "APPROVED": MEAL_APPROVE,
        "REJECTED": MEAL_APPROVE,
        "ARCHIVED": MEAL_ARCHIVE,
    }


class ScorecardTransitionView(MealTransitionView):
    service_class = ScorecardService
    model = PerformanceScorecard
    permission_required = MEAL_MANAGE_SCORECARDS
    transition_permission = MEAL_MANAGE_SCORECARDS
    entity_label = "Performance Scorecard"
    permission_by_status: ClassVar[dict[str, str]] = {"ARCHIVED": MEAL_ARCHIVE}


# ── Exports ──────────────────────────────────────────────────────────────


class IndicatorRegisterExportView(MealPermissionMixin, View):
    permission_required = MEAL_EXPORT

    def get(self, request, *args, **kwargs) -> HttpResponse:
        return indicator_register_csv_response(request.user)


class MonitoringVisitRegisterExportView(MealPermissionMixin, View):
    permission_required = MEAL_EXPORT

    def get(self, request, *args, **kwargs) -> HttpResponse:
        return monitoring_visit_register_csv_response(request.user)


class ComplaintRegisterExportView(MealPermissionMixin, View):
    permission_required = MEAL_EXPORT

    def get(self, request, *args, **kwargs) -> HttpResponse:
        return complaint_register_csv_response(request.user)


class FeedbackRegisterExportView(MealPermissionMixin, View):
    permission_required = MEAL_EXPORT

    def get(self, request, *args, **kwargs) -> HttpResponse:
        return feedback_register_csv_response(request.user)


class EvaluationRegisterExportView(MealPermissionMixin, View):
    permission_required = MEAL_EXPORT

    def get(self, request, *args, **kwargs) -> HttpResponse:
        return evaluation_register_csv_response(request.user)


class LessonRegisterExportView(MealPermissionMixin, View):
    permission_required = MEAL_EXPORT

    def get(self, request, *args, **kwargs) -> HttpResponse:
        return lesson_register_csv_response(request.user)


class MEALReportRegisterExportView(MealPermissionMixin, View):
    permission_required = MEAL_EXPORT

    def get(self, request, *args, **kwargs) -> HttpResponse:
        return meal_report_register_csv_response(request.user)


class MEALReportExportView(MealPermissionMixin, View):
    permission_required = MEAL_EXPORT

    def get(self, request, *args, **kwargs) -> HttpResponse:
        report = _scoped(request.user, MEALReport, kwargs["pk"])
        return meal_report_export_response(request.user, report, kwargs["fmt"])
