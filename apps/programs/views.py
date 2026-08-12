"""Permission-aware, service-backed program and project management views."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, ClassVar

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from apps.rbac.authorization import user_has_permission
from apps.rbac.mixins import PermissionRequiredMixin

from .constants import (
    ChangeStatus,
    IssueStatus,
    ProgramStatus,
    ProjectStatus,
    RiskStatus,
)
from .exports import program_register_csv_response, project_register_csv_response
from .forms import (
    ActivityForm,
    BeneficiaryParticipationForm,
    BeneficiaryRecordForm,
    ChangeDecisionForm,
    ChangeRequestForm,
    ClosureActionForm,
    IssueForm,
    LessonsLearnedForm,
    ProcurementRequestForm,
    ProgramBudgetForm,
    ProgramDocumentForm,
    ProgramEvaluationForm,
    ProgramForm,
    ProgramIndicatorForm,
    ProgramRiskForm,
    ProgramStakeholderLinkForm,
    ProgramStatusTransitionForm,
    ProgramTeamMemberForm,
    ProgressUpdateForm,
    ProjectApprovalActionForm,
    ProjectClosureForm,
    ProjectForm,
    ProjectReportForm,
    ProjectResultForm,
    ProjectStatusTransitionForm,
    ProjectTimelineForm,
    ReasonArchiveForm,
    ResourceAllocationForm,
    TaskForm,
    WBSNodeForm,
    WorkPlanForm,
)
from .models import (
    Activity,
    BeneficiaryParticipation,
    BeneficiaryRecord,
    ChangeRequest,
    Deliverable,
    Issue,
    LessonsLearned,
    Milestone,
    ProcurementRequest,
    Program,
    ProgramBudget,
    ProgramDocument,
    ProgramEvaluation,
    ProgramIndicator,
    ProgramReferenceData,
    ProgramRisk,
    ProgramStakeholderLink,
    ProgramTeamMember,
    ProgressUpdate,
    Project,
    ProjectReport,
    ResourceAllocation,
    Task,
    WBSNode,
    WorkPlan,
)
from .permissions import (
    PROGRAMMES_ARCHIVE,
    PROGRAMMES_CREATE,
    PROGRAMMES_EXPORT,
    PROGRAMMES_MANAGE,
    PROGRAMMES_RESTORE,
    PROGRAMMES_UPDATE,
    PROGRAMMES_VIEW,
    PROJECTS_ARCHIVE,
    PROJECTS_CREATE,
    PROJECTS_EXPORT,
    PROJECTS_MANAGE,
    PROJECTS_RESTORE,
    PROJECTS_UPDATE,
    PROJECTS_VIEW,
)
from .report_exports import (
    lessons_learned_xlsx_response,
    program_closure_docx_response,
    program_register_docx_response,
    program_register_pdf_response,
    program_register_xlsx_response,
    project_register_docx_response,
    project_register_pdf_response,
    project_register_xlsx_response,
)
from .selectors import visible_programs, visible_projects
from .services import (
    ChangeRequestService,
    ProgramChildRecordService,
    ProgramDocumentService,
    ProgramService,
    ProjectAnalyticsService,
    ProjectApprovalService,
    ProjectClosureService,
    ProjectReportService,
    ProjectResultService,
    ProjectService,
    ProjectTimelineService,
    WbsService,
)

logger = logging.getLogger(__name__)


def _can(user, *permission_codes: str) -> bool:
    return bool(
        user_has_permission(user, PROGRAMMES_MANAGE)
        or user_has_permission(user, PROJECTS_MANAGE)
        or any(user_has_permission(user, code) for code in permission_codes)
    )


def _apply_service_errors(form, exc: ValidationError) -> None:
    if hasattr(exc, "message_dict"):
        for field_name, field_messages in exc.message_dict.items():
            target = field_name if field_name in form.fields else None
            for message in field_messages:
                form.add_error(target, message)
        return
    for message in exc.messages:
        form.add_error(None, message)


def _scoped_program(user, pk, *, include_archived: bool = False) -> Program:
    return get_object_or_404(
        visible_programs(user, include_archived=include_archived), pk=pk
    )


def _scoped_project(user, pk, *, include_archived: bool = False) -> Project:
    return get_object_or_404(
        visible_projects(user, include_archived=include_archived), pk=pk
    )


def _scoped_document(user, pk) -> ProgramDocument:
    return get_object_or_404(
        ProgramDocument.objects.filter(
            Q(program__in=visible_programs(user, include_archived=True))
            | Q(project__in=visible_projects(user, include_archived=True))
        ).select_related("program", "project"),
        pk=pk,
    )


def _child_service(user):
    return ProgramChildRecordService(user=user)


class ProgramPermissionMixin(PermissionRequiredMixin):
    """Allow any listed operation permission, with module-manager override."""

    any_permission = True

    def test_func(self) -> bool:
        required = self.permission_required
        permissions = (required,) if isinstance(required, str) else tuple(required)
        return _can(self.request.user, *permissions)


class ProgramDashboardView(ProgramPermissionMixin, TemplateView):
    template_name = "programs/dashboard.html"
    permission_required = (PROGRAMMES_VIEW, PROJECTS_VIEW)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        programs = visible_programs(user)
        projects = visible_projects(user)
        metrics = programs.aggregate(
            total=Count("id"),
            active=Count(
                "id",
                filter=Q(
                    status__in=[
                        ProgramStatus.ACTIVE,
                        ProgramStatus.ON_HOLD,
                        ProgramStatus.DELAYED,
                        ProgramStatus.SUSPENDED,
                    ]
                ),
            ),
            completed=Count(
                "id",
                filter=Q(status__in=[ProgramStatus.COMPLETED, ProgramStatus.CLOSED]),
            ),
        )
        project_metrics = projects.aggregate(
            total=Count("id"),
            execution=Count("id", filter=Q(status=ProjectStatus.EXECUTION)),
        )
        context.update(
            {
                "metrics": metrics,
                "project_metrics": project_metrics,
                "status_summary": list(
                    programs.values("status")
                    .annotate(total=Count("id"))
                    .order_by("status")
                ),
                "recent_programs": programs.select_related(
                    "category", "program_manager"
                )[:6],
                "recent_projects": projects.select_related("program")[:6],
                "open_risks": ProgramRisk.objects.filter(
                    program__in=programs,
                    status__in=[RiskStatus.OPEN, RiskStatus.MONITORING],
                ).count(),
                "open_issues": Issue.objects.filter(
                    Q(program__in=programs) | Q(project__in=projects),
                    status__in=[IssueStatus.OPEN, IssueStatus.IN_PROGRESS],
                ).count(),
                "pending_changes": ChangeRequest.objects.filter(
                    Q(program__in=programs) | Q(project__in=projects),
                    status__in=[
                        ChangeStatus.SUBMITTED,
                        ChangeStatus.PENDING_APPROVAL,
                    ],
                ).count(),
                "can_create_program": _can(user, PROGRAMMES_CREATE),
                "can_create_project": _can(user, PROJECTS_CREATE),
            }
        )
        return context


class ProgramDirectoryView(ProgramPermissionMixin, ListView):
    model = Program
    template_name = "programs/program_directory.html"
    context_object_name = "programs"
    paginate_by = 24
    permission_required = (PROGRAMMES_VIEW,)

    SORTS: ClassVar[dict[str, tuple[str, ...]]] = {
        "title": ("title",),
        "title_desc": ("-title",),
        "reference": ("reference_number",),
        "status": ("status", "title"),
        "recent": ("-created_at",),
    }

    def get_queryset(self):
        queryset = visible_programs(self.request.user).select_related(
            "category", "portfolio", "program_manager", "responsible_directorate"
        )
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(reference_number__icontains=search)
                | Q(title__icontains=search)
                | Q(short_title__icontains=search)
            )
        status = self.request.GET.get("status", "")
        if status in ProgramStatus.values:
            queryset = queryset.filter(status=status)
        category = self.request.GET.get("category", "").strip()
        if category:
            queryset = queryset.filter(category__code=category)
        ordering = self.SORTS.get(
            self.request.GET.get("sort", "recent"), self.SORTS["recent"]
        )
        return queryset.order_by(*ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop("page", None)
        context.update(
            {
                "status_choices": ProgramStatus.choices,
                "categories": ProgramReferenceData.objects.filter(
                    kind="CATEGORY", active=True
                ),
                "sort_choices": (
                    ("recent", "Recently added"),
                    ("title", "Title A-Z"),
                    ("title_desc", "Title Z-A"),
                    ("reference", "Reference"),
                    ("status", "Status"),
                ),
                "query_without_page": query.urlencode(),
                "can_create": _can(self.request.user, PROGRAMMES_CREATE),
                "active_programs": visible_programs(self.request.user).count(),
            }
        )
        return context


class ProjectDirectoryView(ProgramPermissionMixin, ListView):
    model = Project
    template_name = "programs/project_directory.html"
    context_object_name = "projects"
    paginate_by = 24
    permission_required = (PROJECTS_VIEW,)

    SORTS: ClassVar[dict[str, tuple[str, ...]]] = {
        "title": ("title",),
        "title_desc": ("-title",),
        "reference": ("reference_number",),
        "status": ("status", "title"),
        "recent": ("-created_at",),
    }

    def get_queryset(self):
        queryset = visible_projects(self.request.user).select_related(
            "program", "category", "project_manager"
        )
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(reference_number__icontains=search)
                | Q(title__icontains=search)
                | Q(program__title__icontains=search)
            )
        status = self.request.GET.get("status", "")
        if status in ProjectStatus.values:
            queryset = queryset.filter(status=status)
        program_pk = self.request.GET.get("program", "")
        if program_pk:
            queryset = queryset.filter(program_id=program_pk)
        ordering = self.SORTS.get(
            self.request.GET.get("sort", "recent"), self.SORTS["recent"]
        )
        return queryset.order_by(*ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop("page", None)
        context.update(
            {
                "status_choices": ProjectStatus.choices,
                "programs": visible_programs(self.request.user).order_by("title"),
                "sort_choices": (
                    ("recent", "Recently added"),
                    ("title", "Title A-Z"),
                    ("title_desc", "Title Z-A"),
                    ("reference", "Reference"),
                    ("status", "Status"),
                ),
                "query_without_page": query.urlencode(),
                "can_create": _can(self.request.user, PROJECTS_CREATE),
            }
        )
        return context


class ProgramCreateView(ProgramPermissionMixin, FormView):
    form_class = ProgramForm
    template_name = "programs/program_form.html"
    permission_required = PROGRAMMES_CREATE

    def form_valid(self, form):
        try:
            program = ProgramService(user=self.request.user).create(**form.cleaned_data)
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Program {program.reference_number} created successfully.",
        )
        return redirect("programs:program_profile", pk=program.pk)


class ProgramUpdateView(ProgramPermissionMixin, FormView):
    form_class = ProgramForm
    template_name = "programs/program_form.html"
    permission_required = PROGRAMMES_UPDATE

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = _scoped_program(self.request.user, self.kwargs["pk"])
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def form_valid(self, form):
        try:
            program = ProgramService(user=self.request.user).update(
                self.get_object(), **form.cleaned_data
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Program profile updated successfully.")
        return redirect("programs:program_profile", pk=program.pk)


class ProgramProfileView(ProgramPermissionMixin, DetailView):
    model = Program
    template_name = "programs/program_profile.html"
    context_object_name = "program"
    permission_required = PROGRAMMES_VIEW

    def get_queryset(self):
        return visible_programs(self.request.user).prefetch_related(
            "pillars", "sdgs", "funding_sources"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        program = self.object
        can_update = _can(user, PROGRAMMES_UPDATE)
        can_archive = _can(user, PROGRAMMES_ARCHIVE)
        can_write = can_update
        context.update(
            {
                "status_history": program.status_history.select_related("changed_by")[
                    :10
                ],
                "projects": program.projects.select_related("category")[:8],
                "team_members": program.team_members.select_related("user")[:10],
                "work_plans": program.work_plans.all()[:6],
                "budgets": program.budgets.all()[:5],
                "risks": program.risks.select_related("category")[:6],
                "issues": program.issues.all()[:6],
                "indicators": program.indicators.all()[:8],
                "stakeholder_links": program.stakeholder_links.select_related(
                    "stakeholder"
                )[:8],
                "can_update": can_update,
                "can_archive": can_archive,
                "can_write": can_write,
                "can_create_project": _can(user, PROJECTS_CREATE),
            }
        )
        return context


class ProgramStatusView(ProgramPermissionMixin, FormView):
    form_class = ProgramStatusTransitionForm
    template_name = "programs/workflow_form.html"
    permission_required = PROGRAMMES_UPDATE

    def get_program(self):
        if not hasattr(self, "program"):
            self.program = _scoped_program(self.request.user, self.kwargs["pk"])
        return self.program

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["program"] = self.get_program()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Change program status",
                "entity": self.get_program(),
                "cancel_url": reverse(
                    "programs:program_profile",
                    kwargs={"pk": self.get_program().pk},
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            ProgramService(user=self.request.user).change_status(
                self.get_program(),
                form.cleaned_data["new_status"],
                form.cleaned_data["reason"],
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Program status updated.")
        return redirect("programs:program_profile", pk=self.get_program().pk)


class ProgramArchiveView(ProgramPermissionMixin, FormView):
    form_class = ReasonArchiveForm
    template_name = "programs/workflow_form.html"
    permission_required = PROGRAMMES_ARCHIVE

    def get_program(self):
        return _scoped_program(self.request.user, self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Archive program",
                "entity": self.get_program(),
                "cancel_url": reverse(
                    "programs:program_profile",
                    kwargs={"pk": self.get_program().pk},
                ),
            }
        )
        return context

    def form_valid(self, form):
        ProgramService(user=self.request.user).archive(
            self.get_program(), form.cleaned_data["reason"]
        )
        messages.success(self.request, "Program archived.")
        return redirect("programs:program_directory")


class ProgramRestoreView(ProgramPermissionMixin, FormView):
    form_class = ReasonArchiveForm
    template_name = "programs/workflow_form.html"
    permission_required = PROGRAMMES_RESTORE

    def get_program(self):
        return _scoped_program(
            self.request.user, self.kwargs["pk"], include_archived=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Restore program",
                "entity": self.get_program(),
                "cancel_url": reverse("programs:program_directory"),
            }
        )
        return context

    def form_valid(self, form):
        program = ProgramService(user=self.request.user).restore(
            self.get_program(), form.cleaned_data["reason"]
        )
        messages.success(self.request, "Program restored as draft.")
        return redirect("programs:program_profile", pk=program.pk)


class ProjectCreateView(ProgramPermissionMixin, FormView):
    form_class = ProjectForm
    template_name = "programs/project_form.html"
    permission_required = PROJECTS_CREATE

    def get_program(self):
        return _scoped_program(self.request.user, self.kwargs.get("pk"))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.kwargs.get("pk"):
            kwargs["program"] = self.get_program()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        program = self.get_program() if self.kwargs.get("pk") else None
        context["program"] = program
        return context

    def form_valid(self, form):
        cleaned = dict(form.cleaned_data)
        program = cleaned.pop("program", None)
        if program is None and self.kwargs.get("pk"):
            program = self.get_program()
        try:
            project = ProjectService(user=self.request.user).create(program, **cleaned)
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Project {project.reference_number} created successfully.",
        )
        return redirect("programs:project_profile", pk=project.pk)


class ProjectUpdateView(ProgramPermissionMixin, FormView):
    form_class = ProjectForm
    template_name = "programs/project_form.html"
    permission_required = PROJECTS_UPDATE

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = _scoped_project(self.request.user, self.kwargs["pk"])
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def form_valid(self, form):
        try:
            project = ProjectService(user=self.request.user).update(
                self.get_object(), **form.cleaned_data
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Project profile updated successfully.")
        return redirect("programs:project_profile", pk=project.pk)


class ProjectProfileView(ProgramPermissionMixin, DetailView):
    model = Project
    template_name = "programs/project_profile.html"
    context_object_name = "project"
    permission_required = PROJECTS_VIEW

    def get_queryset(self):
        return visible_projects(self.request.user).select_related(
            "program", "category", "project_manager"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        project = self.object
        context.update(
            {
                "status_history": project.status_history.select_related("changed_by")[
                    :10
                ],
                "work_plans": project.work_plans.all()[:6],
                "milestones": project.milestones.all()[:8],
                "deliverables": project.deliverables.all()[:8],
                "issues": project.issues.all()[:6],
                "evidence": project.evidence.all()[:6],
                "beneficiaries": project.beneficiaries.all()[:8],
                "documents": project.documents.all()[:5],
                "can_update": _can(user, PROJECTS_UPDATE),
                "can_archive": _can(user, PROJECTS_ARCHIVE),
            }
        )
        return context


class ProjectStatusView(ProgramPermissionMixin, FormView):
    form_class = ProjectStatusTransitionForm
    template_name = "programs/workflow_form.html"
    permission_required = PROJECTS_UPDATE

    def get_project(self):
        if not hasattr(self, "project"):
            self.project = _scoped_project(self.request.user, self.kwargs["pk"])
        return self.project

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Change project status",
                "entity": self.get_project(),
                "cancel_url": reverse(
                    "programs:project_profile", kwargs={"pk": self.get_project().pk}
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            ProjectService(user=self.request.user).change_status(
                self.get_project(),
                form.cleaned_data["new_status"],
                form.cleaned_data["reason"],
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Project status updated.")
        return redirect("programs:project_profile", pk=self.get_project().pk)


class ProjectArchiveView(ProgramPermissionMixin, FormView):
    form_class = ReasonArchiveForm
    template_name = "programs/workflow_form.html"
    permission_required = PROJECTS_ARCHIVE

    def get_project(self):
        return _scoped_project(self.request.user, self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Archive project",
                "entity": self.get_project(),
                "cancel_url": reverse(
                    "programs:project_profile",
                    kwargs={"pk": self.get_project().pk},
                ),
            }
        )
        return context

    def form_valid(self, form):
        ProjectService(user=self.request.user).archive(
            self.get_project(), form.cleaned_data["reason"]
        )
        messages.success(self.request, "Project archived.")
        return redirect("programs:project_directory")


class ProjectRestoreView(ProgramPermissionMixin, FormView):
    form_class = ReasonArchiveForm
    template_name = "programs/workflow_form.html"
    permission_required = PROJECTS_RESTORE

    def get_project(self):
        return _scoped_project(
            self.request.user, self.kwargs["pk"], include_archived=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Restore project",
                "entity": self.get_project(),
                "cancel_url": reverse("programs:project_directory"),
            }
        )
        return context

    def form_valid(self, form):
        project = ProjectService(user=self.request.user).restore(
            self.get_project(), form.cleaned_data["reason"]
        )
        messages.success(self.request, "Project restored as concept.")
        return redirect("programs:project_profile", pk=project.pk)


class ProgramRelatedView(ProgramPermissionMixin, TemplateView):
    """Render and create one scoped child collection for a program."""

    template_name = "programs/related_records.html"
    permission_required: str | tuple[str, ...] = (PROGRAMMES_VIEW,)
    write_permission = PROGRAMMES_UPDATE
    form_class: ClassVar[type[forms.BaseForm] | None] = None
    route_name = ""
    title = "Related records"
    description = ""
    columns: tuple[str, ...] = ()
    program: Program | None = None
    form_needs_program = False

    def get_program(self):
        if self.program is None:
            self.program = _scoped_program(
                self.request.user, self.kwargs["pk"], include_archived=True
            )
        return self.program

    def can_write(self):
        return bool(
            self.write_permission and _can(self.request.user, self.write_permission)
        )

    def get_form_kwargs(self):
        if not self.form_needs_program:
            return {}
        return {"program": self.get_program()}

    def get_form(self, data=None, files=None):
        if not self.can_write() or self.form_class is None:
            return None
        return self.form_class(data, files, **self.get_form_kwargs())

    def get_rows(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def perform_service(self, cleaned_data: dict):
        raise NotImplementedError

    @property
    def child_service(self):
        return _child_service(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "program": self.get_program(),
                "entity": self.get_program(),
                "title": self.title,
                "description": self.description,
                "columns": self.columns,
                "rows": self.get_rows(),
                "form": kwargs.get("form") or self.get_form(),
                "can_write": self.can_write(),
                "cancel_url": reverse(
                    "programs:program_profile", kwargs={"pk": self.get_program().pk}
                ),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        if not self.can_write():
            raise PermissionDenied
        form = self.get_form(request.POST, request.FILES)
        if form is None:
            raise PermissionDenied
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(**kwargs, form=form))
        self.perform_service(form.cleaned_data)
        messages.success(self.request, f"{self.title} saved successfully.")
        return redirect(self.route_name, pk=self.get_program().pk)


class WorkPlanView(ProgramRelatedView):
    form_class = WorkPlanForm
    route_name = "programs:work_plans"
    title = "Work plans"
    description = "Time-bound work plans for this program."
    columns = ("Reference", "Title", "Period", "Status")
    form_needs_program = True

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.reference_number,
                "title": row.title,
                "period": row.reporting_period,
                "status": row.get_status_display(),
            }
            for row in self.get_program().work_plans.select_related().all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            WorkPlan, program=self.get_program(), fields=cleaned_data
        )


class ActivityView(ProgramRelatedView):
    form_class = ActivityForm
    route_name = "programs:activities"
    title = "Activities"
    description = "Measurable activities across program work plans."
    columns = ("Reference", "Title", "Planned date", "Status")

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.reference_number,
                "title": row.title,
                "date": row.planned_date,
                "status": row.get_status_display(),
            }
            for row in Activity.objects.filter(work_plan__program=self.get_program())
            .select_related("work_plan")
            .order_by("planned_date")[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            Activity, program=self.get_program(), fields=cleaned_data
        )


class TaskView(ProgramRelatedView):
    form_class = TaskForm
    route_name = "programs:tasks"
    title = "Tasks"
    description = "Tasks tracked against program activities."
    columns = ("Reference", "Title", "Assignee", "Status")

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.reference_number,
                "title": row.title,
                "assignee": (
                    row.assigned_user.full_name if row.assigned_user else "Unassigned"
                ),
                "status": row.get_status_display(),
            }
            for row in Task.objects.filter(
                activity__work_plan__program=self.get_program()
            )
            .select_related("assigned_user")
            .order_by("-created_at")[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(Task, program=self.get_program(), fields=cleaned_data)


class RiskView(ProgramRelatedView):
    form_class = ProgramRiskForm
    route_name = "programs:risks"
    title = "Risks"
    description = "Program risk register entries."
    columns = ("Category", "Title", "Score", "Status")

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.category.name if row.category else "Uncategorized",
                "title": row.title,
                "score": row.risk_score,
                "status": row.get_status_display(),
            }
            for row in self.get_program().risks.select_related("category").all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            ProgramRisk, program=self.get_program(), fields=cleaned_data
        )


class IssueView(ProgramRelatedView):
    form_class = IssueForm
    route_name = "programs:issues"
    title = "Issues"
    description = "Operational issues raised during implementation."
    columns = ("Reference", "Title", "Priority", "Status")
    form_needs_program = True

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.reference_number,
                "title": row.title,
                "priority": row.get_priority_display(),
                "status": row.get_status_display(),
            }
            for row in self.get_program().issues.all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            Issue, program=self.get_program(), fields=cleaned_data
        )


class ChangeRequestView(ProgramRelatedView):
    form_class = ChangeRequestForm
    route_name = "programs:change_requests"
    title = "Change requests"
    description = "Controlled change requests affecting this program."
    columns = ("Reference", "Title", "Impact", "Status")
    form_needs_program = True

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.reference_number,
                "title": row.title,
                "impact": row.budget_impact or row.timeline_impact or "Not stated",
                "status": row.get_status_display(),
            }
            for row in self.get_program().change_requests.all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            ChangeRequest, program=self.get_program(), fields=cleaned_data
        )


class BudgetView(ProgramRelatedView):
    form_class = ProgramBudgetForm
    route_name = "programs:budgets"
    title = "Budgets"
    description = "Period budgets for this program."
    columns = ("Period", "Approved", "Utilized", "Active")

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.period_label,
                "title": row.currency,
                "score": row.approved_amount,
                "status": row.utilized_amount,
            }
            for row in self.get_program().budgets.all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            ProgramBudget, program=self.get_program(), fields=cleaned_data
        )


class TeamMemberView(ProgramRelatedView):
    form_class = ProgramTeamMemberForm
    route_name = "programs:team_members"
    title = "Team members"
    description = "Role-based members of the program delivery team."
    columns = ("Member", "Role", "Active")
    form_needs_program = True

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.user.full_name or row.user.email,
                "title": row.role_title,
                "score": row.start_date,
                "status": "Active" if row.is_active else "Inactive",
            }
            for row in self.get_program().team_members.select_related("user").all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            ProgramTeamMember, program=self.get_program(), fields=cleaned_data
        )


class StakeholderLinkView(ProgramRelatedView):
    form_class = ProgramStakeholderLinkForm
    route_name = "programs:stakeholder_links"
    title = "Stakeholder links"
    description = "Partners, donors, sponsors, and other linked stakeholders."
    columns = ("Stakeholder", "Link kind", "Active")
    form_needs_program = True

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.stakeholder.legal_name,
                "title": row.get_link_kind_display(),
                "score": "",
                "status": "Active" if row.is_active else "Inactive",
            }
            for row in self.get_program()
            .stakeholder_links.select_related("stakeholder")
            .all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            ProgramStakeholderLink, program=self.get_program(), fields=cleaned_data
        )


class IndicatorView(ProgramRelatedView):
    form_class = ProgramIndicatorForm
    route_name = "programs:indicators"
    title = "Indicators"
    description = "Performance indicators supporting MEAL reporting."
    columns = ("Code", "Description", "Baseline", "Target")

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.code,
                "title": row.description,
                "score": row.baseline,
                "status": row.target,
            }
            for row in self.get_program().indicators.all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            ProgramIndicator, program=self.get_program(), fields=cleaned_data
        )


class EvaluationView(ProgramRelatedView):
    form_class = ProgramEvaluationForm
    route_name = "programs:evaluations"
    title = "Evaluations"
    description = "Baseline, midline, endline, outcome, and impact evaluations."
    columns = ("Type", "Title", "Date", "Published")

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.get_evaluation_type_display(),
                "title": row.title,
                "score": row.evaluation_date,
                "status": "Yes" if row.is_published else "No",
            }
            for row in self.get_program().evaluations.all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            ProgramEvaluation, program=self.get_program(), fields=cleaned_data
        )


class DocumentView(ProgramRelatedView):
    form_class = ProgramDocumentForm
    route_name = "programs:documents"
    title = "Documents"
    description = "Protected program documents."
    columns = ("Title", "Type", "Status")
    form_needs_program = True

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.title,
                "title": (
                    row.document_type.name if row.document_type else "Unclassified"
                ),
                "score": row.file_size,
                "status": row.get_status_display(),
            }
            for row in self.get_program()
            .documents.select_related("document_type")
            .all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        program = self.get_program()
        file = cleaned_data.pop("file", None)
        document_type = cleaned_data.pop("document_type", None)
        ProgramDocumentService(user=self.request.user).upload(
            program=program,
            project=None,
            title=cleaned_data.pop("title", ""),
            file=file,
            document_type=document_type,
            description=cleaned_data.get("description", ""),
        )


class BeneficiaryView(ProgramRelatedView):
    form_class = BeneficiaryRecordForm
    route_name = "programs:beneficiaries"
    title = "Beneficiaries"
    description = "Beneficiaries enrolled in this program."
    columns = ("Reference", "Name", "Category", "Status")
    form_needs_program = True

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.reference_number,
                "title": row.name,
                "score": row.category.name if row.category else "Uncategorized",
                "status": row.get_status_display(),
            }
            for row in self.get_program()
            .beneficiaries.select_related("category")
            .all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            BeneficiaryRecord, program=self.get_program(), fields=cleaned_data
        )


class ProgressUpdateView(ProgramRelatedView):
    form_class = ProgressUpdateForm
    route_name = "programs:progress_updates"
    title = "Progress updates"
    description = "Periodic progress updates on this program."
    columns = ("Period", "Completion", "Budget utilization", "Status")
    form_needs_program = True

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.period_label,
                "title": row.overall_completion,
                "score": row.budget_utilization,
                "status": row.get_status_display(),
            }
            for row in self.get_program().progress_updates.all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            ProgressUpdate, program=self.get_program(), fields=cleaned_data
        )


class ResourceAllocationView(ProgramRelatedView):
    form_class = ResourceAllocationForm
    route_name = "programs:resource_allocations"
    title = "Resource allocations"
    description = "Human, financial, and material resources allocated to this program."
    columns = ("Type", "Description", "Cost", "Period")
    form_needs_program = True

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.get_resource_type_display(),
                "title": row.description,
                "score": f"{row.estimated_cost} {row.currency}",
                "status": (f"{row.start_date or '-'} → {row.end_date or '-'}"),
            }
            for row in self.get_program().resource_allocations.all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            ResourceAllocation, program=self.get_program(), fields=cleaned_data
        )


class ProcurementRequestView(ProgramRelatedView):
    form_class = ProcurementRequestForm
    route_name = "programs:procurement_requests"
    title = "Procurement requests"
    description = "Procurement requests raised against this program."
    columns = ("Reference", "Title", "Estimated cost", "Status")
    form_needs_program = True

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.reference_number,
                "title": row.title,
                "score": f"{row.estimated_cost} {row.currency}",
                "status": row.get_status_display(),
            }
            for row in self.get_program().procurement_requests.all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            ProcurementRequest, program=self.get_program(), fields=cleaned_data
        )


class LessonsLearnedView(ProgramRelatedView):
    form_class = LessonsLearnedForm
    route_name = "programs:lessons_learned"
    title = "Lessons learned"
    description = "Success stories, best practices, challenges, and innovations."
    columns = ("Reference", "Title", "Category", "Recorded at")
    form_needs_program = True

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "reference": row.reference_number,
                "title": row.title,
                "score": row.get_category_display(),
                "status": row.recorded_at,
            }
            for row in self.get_program().lessons_learned.all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        self.child_service.create(
            LessonsLearned, program=self.get_program(), fields=cleaned_data
        )


class DocumentDownloadView(ProgramPermissionMixin, View):
    permission_required = (PROGRAMMES_VIEW,)

    def get(self, request, pk):
        document = _scoped_document(request.user, pk)
        if not document.file:
            raise Http404("The document has no file.")
        try:
            file_handle = document.file.open("rb")
        except OSError as exc:
            raise Http404("The document file is unavailable.") from exc
        logger.info(
            "program_document_downloaded",
            extra={
                "program_event": {
                    "action": "document.downloaded",
                    "entity_id": str(document.pk),
                    "program_id": str(document.program_id),
                    "project_id": str(document.project_id),
                    "actor_id": str(request.user.pk),
                }
            },
        )
        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=Path(document.original_filename or document.file.name).name,
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        response["Pragma"] = "no-cache"
        return response


class ProgramRegisterExportView(ProgramPermissionMixin, View):
    permission_required = PROGRAMMES_EXPORT

    def get(self, request):
        return program_register_csv_response(request.user)


class ProjectRegisterExportView(ProgramPermissionMixin, View):
    permission_required = PROJECTS_EXPORT

    def get(self, request):
        return project_register_csv_response(request.user)


class ProgramRegisterXlsxExportView(ProgramPermissionMixin, View):
    permission_required = PROGRAMMES_EXPORT

    def get(self, request):
        return program_register_xlsx_response(request.user)


class ProgramRegisterDocxExportView(ProgramPermissionMixin, View):
    permission_required = PROGRAMMES_EXPORT

    def get(self, request):
        return program_register_docx_response(request.user)


class ProgramRegisterPdfExportView(ProgramPermissionMixin, View):
    permission_required = PROGRAMMES_EXPORT

    def get(self, request):
        return program_register_pdf_response(request.user)


class ProjectRegisterXlsxExportView(ProgramPermissionMixin, View):
    permission_required = PROJECTS_EXPORT

    def get(self, request):
        return project_register_xlsx_response(request.user)


class ProjectRegisterDocxExportView(ProgramPermissionMixin, View):
    permission_required = PROJECTS_EXPORT

    def get(self, request):
        return project_register_docx_response(request.user)


class ProjectRegisterPdfExportView(ProgramPermissionMixin, View):
    permission_required = PROJECTS_EXPORT

    def get(self, request):
        return project_register_pdf_response(request.user)


class LessonsLearnedExportView(ProgramPermissionMixin, View):
    permission_required = PROGRAMMES_EXPORT

    def get(self, request):
        return lessons_learned_xlsx_response(request.user)


class ProgramClosureReportView(ProgramPermissionMixin, View):
    permission_required = PROGRAMMES_EXPORT

    def get(self, request, program_id):
        return program_closure_docx_response(request.user, program_id)


class ProjectRelatedView(ProgramPermissionMixin, TemplateView):
    """Render and create one scoped child collection for a project."""

    template_name = "programs/project_related_records.html"
    permission_required: str | tuple[str, ...] = (PROJECTS_VIEW,)
    write_permission = PROJECTS_UPDATE
    form_class: ClassVar[type[forms.BaseForm] | None] = None
    route_name = ""
    title = "Project records"
    description = ""
    columns: tuple[str, ...] = ()
    project: Project | None = None
    form_needs_project = False

    def get_project(self):
        if self.project is None:
            self.project = _scoped_project(
                self.request.user, self.kwargs["pk"], include_archived=True
            )
        return self.project

    def can_write(self):
        return bool(
            self.write_permission and _can(self.request.user, self.write_permission)
        )

    def get_form_kwargs(self):
        if not self.form_needs_project:
            return {}
        return {"project": self.get_project()}

    def get_form(self, data=None, files=None):
        if not self.can_write() or self.form_class is None:
            return None
        return self.form_class(data, files, **self.get_form_kwargs())

    def get_rows(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def perform_service(self, cleaned_data: dict):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "project": self.get_project(),
                "entity": self.get_project(),
                "title": self.title,
                "description": self.description,
                "columns": self.columns,
                "rows": self.get_rows(),
                "form": kwargs.get("form") or self.get_form(),
                "can_write": self.can_write(),
                "cancel_url": reverse(
                    "programs:project_profile", kwargs={"pk": self.get_project().pk}
                ),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        if not self.can_write():
            raise PermissionDenied
        form = self.get_form(request.POST, request.FILES)
        if form is None:
            raise PermissionDenied
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(**kwargs, form=form))
        self.perform_service(form.cleaned_data)
        messages.success(self.request, f"{self.title} saved successfully.")
        return redirect(self.route_name, pk=self.get_project().pk)


class ProjectWbsView(ProjectRelatedView):
    form_class = WBSNodeForm
    route_name = "programs:project_wbs"
    title = "Work breakdown structure"
    description = "Hierarchical project WBS with progress roll-up."
    columns = ("Code", "Node", "Type", "Progress", "Status")
    template_name = "programs/project_wbs.html"
    form_needs_project = True

    def get_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for node in self.get_project().wbs_nodes.select_related("parent").all():
            rows.append(
                {
                    "code": node.code,
                    "title": node.title,
                    "node_type": node.get_node_type_display(),
                    "progress": f"{node.completion_percentage}%",
                    "status": node.get_status_display(),
                    "node": node,
                    "depth": self._depth(node),
                }
            )
        return rows

    def _depth(self, node: WBSNode) -> int:
        depth = 0
        cursor = node.parent
        seen: set = set()
        while cursor is not None and depth < 64 and cursor.pk not in seen:
            seen.add(cursor.pk)
            depth += 1
            cursor = cursor.parent
        return depth

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "root_nodes": [node for node in self.get_rows() if node["depth"] == 0],
            }
        )
        return context

    def perform_service(self, cleaned_data: dict):
        WbsService(user=self.request.user).create_node(
            self.get_project(), **cleaned_data
        )


class ProjectResultsView(ProjectRelatedView):
    form_class = ProjectResultForm
    route_name = "programs:project_results"
    title = "Project results"
    description = "Structured outputs, outcomes, and impacts."
    columns = ("Type", "Code", "Description", "Target", "Status")

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "code": row.get_result_type_display(),
                "title": row.code,
                "node_type": row.description[:60],
                "progress": row.target,
                "status": row.get_status_display(),
            }
            for row in self.get_project().results.all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        ProjectResultService(user=self.request.user).create_result(
            self.get_project(), **cleaned_data
        )


class ProjectTimelineView(ProjectRelatedView):
    form_class = ProjectTimelineForm
    route_name = "programs:project_timeline"
    title = "Project timeline"
    description = "Scheduled entries for Gantt-style planning."
    columns = ("Title", "Planned start", "Planned end", "Status")
    form_needs_project = True

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "code": row.title,
                "title": row.planned_start_date,
                "node_type": row.planned_end_date,
                "progress": row.get_status_display(),
                "status": "",
            }
            for row in self.get_project().timeline_entries.all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        ProjectTimelineService(user=self.request.user).create_entry(
            self.get_project(), **cleaned_data
        )


class ProjectParticipationView(ProjectRelatedView):
    form_class = BeneficiaryParticipationForm
    route_name = "programs:project_participations"
    title = "Beneficiary participation"
    description = "Participation events against project beneficiaries."
    columns = ("Beneficiary", "Activity", "Date", "Outcomes")

    def get_rows(self) -> list[dict[str, Any]]:
        records = BeneficiaryParticipation.objects.filter(
            beneficiary__project=self.get_project()
        ).select_related("beneficiary")[:40]
        return [
            {
                "code": row.beneficiary.name,
                "title": row.activity_title,
                "node_type": row.participation_date,
                "progress": row.outcomes_achieved[:40],
                "status": "",
            }
            for row in records
        ]

    def perform_service(self, cleaned_data: dict):
        raise NotImplementedError


class ProjectClosureView(ProgramPermissionMixin, FormView):
    form_class = ProjectClosureForm
    template_name = "programs/project_closure.html"
    permission_required = PROJECTS_UPDATE

    def get_project(self):
        if not hasattr(self, "project"):
            self.project = _scoped_project(
                self.request.user, self.kwargs["pk"], include_archived=True
            )
        return self.project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context.update(
            {
                "project": project,
                "closure": getattr(project, "closure", None),
                "can_verify": _can(self.request.user, PROJECTS_UPDATE),
                "can_approve": _can(self.request.user, PROJECTS_MANAGE),
            }
        )
        return context

    def form_valid(self, form):
        project = self.get_project()
        try:
            ProjectClosureService(user=self.request.user).create(
                project, **form.cleaned_data
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Project closure record created.")
        return redirect("programs:project_closure", pk=project.pk)


class ProjectClosureActionView(ProgramPermissionMixin, FormView):
    form_class = ClosureActionForm
    template_name = "programs/workflow_form.html"
    permission_required = PROJECTS_UPDATE

    def get_project(self):
        if not hasattr(self, "project"):
            self.project = _scoped_project(
                self.request.user, self.kwargs["pk"], include_archived=True
            )
        return self.project

    def get_closure(self):
        return getattr(self.get_project(), "closure", None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        action = self.kwargs.get("action", "")
        context.update(
            {
                "title": f"Project closure — {action.replace('-', ' ')}",
                "entity": self.get_project(),
                "cancel_url": reverse(
                    "programs:project_closure",
                    kwargs={"pk": self.get_project().pk},
                ),
            }
        )
        return context

    def form_valid(self, form):
        project = self.get_project()
        closure = self.get_closure()
        if closure is None:
            raise Http404("No closure record for this project.")
        action = self.kwargs.get("action", "")
        notes = form.cleaned_data.get("notes", "")
        service = ProjectClosureService(user=self.request.user)
        if action == "verify":
            service.verify(closure, notes)
            messages.success(self.request, "Closure verified.")
        elif action == "approve":
            service.approve(closure, notes)
            messages.success(self.request, "Closure approved; project closed.")
        else:
            raise Http404("Unknown closure action.")
        return redirect("programs:project_closure", pk=project.pk)


class ProjectReportsView(ProjectRelatedView):
    form_class = ProjectReportForm
    route_name = "programs:project_reports"
    title = "Project reports"
    description = "Report records for the project reporting workflow."
    columns = ("Title", "Type", "Period", "Status")

    def get_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "code": row.title,
                "title": row.get_report_type_display(),
                "node_type": row.period_label,
                "progress": row.get_status_display(),
                "status": "",
            }
            for row in self.get_project().reports.all()[:40]
        ]

    def perform_service(self, cleaned_data: dict):
        file = cleaned_data.pop("report_file", None)
        service = ProjectReportService(user=self.request.user)
        report = service.create(self.get_project(), **cleaned_data)
        if file:
            report.report_file = file
            report.save()


class ProjectAnalyticsView(ProgramPermissionMixin, TemplateView):
    template_name = "programs/project_analytics.html"
    permission_required = PROJECTS_VIEW

    def get_project(self):
        if not hasattr(self, "project"):
            self.project = _scoped_project(
                self.request.user, self.kwargs["pk"], include_archived=True
            )
        return self.project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        analytics = ProjectAnalyticsService(user=self.request.user).summarize(project)
        context.update(
            {
                "project": project,
                "analytics": analytics,
                "recent_reports": project.reports.all()[:5],
            }
        )
        return context


class ProjectMilestoneApprovalView(ProgramPermissionMixin, FormView):
    form_class = ProjectApprovalActionForm
    template_name = "programs/workflow_form.html"
    permission_required = PROJECTS_UPDATE

    def get_milestone(self):
        return get_object_or_404(
            Milestone.objects.select_related("project"),
            pk=self.kwargs["milestone_pk"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        milestone = self.get_milestone()
        context.update(
            {
                "title": f"Review milestone — {milestone.title}",
                "entity": milestone,
                "cancel_url": reverse(
                    "programs:project_profile",
                    kwargs={"pk": milestone.project_id},
                ),
            }
        )
        return context

    def form_valid(self, form):
        milestone = self.get_milestone()
        action = self.kwargs.get("action", "")
        notes = form.cleaned_data.get("notes", "")
        service = ProjectApprovalService(user=self.request.user)
        try:
            if action == "submit":
                service.submit_milestone(milestone, notes)
            elif action == "approve":
                service.approve_milestone(milestone, notes)
            elif action == "reject":
                service.reject_milestone(milestone, notes)
            else:
                raise Http404("Unknown milestone action.")
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Milestone updated.")
        return redirect("programs:project_profile", pk=milestone.project_id)


class ProjectDeliverableApprovalView(ProgramPermissionMixin, FormView):
    form_class = ProjectApprovalActionForm
    template_name = "programs/workflow_form.html"
    permission_required = PROJECTS_UPDATE

    def get_deliverable(self):
        return get_object_or_404(
            Deliverable.objects.select_related("project"),
            pk=self.kwargs["deliverable_pk"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        deliverable = self.get_deliverable()
        context.update(
            {
                "title": f"Review deliverable — {deliverable.title}",
                "entity": deliverable,
                "cancel_url": reverse(
                    "programs:project_profile",
                    kwargs={"pk": deliverable.project_id},
                ),
            }
        )
        return context

    def form_valid(self, form):
        deliverable = self.get_deliverable()
        action = self.kwargs.get("action", "")
        notes = form.cleaned_data.get("notes", "")
        service = ProjectApprovalService(user=self.request.user)
        try:
            if action == "submit":
                service.submit_deliverable(deliverable, notes)
            elif action == "approve":
                service.approve_deliverable(deliverable, notes)
            elif action == "reject":
                service.reject_deliverable(deliverable, notes)
            else:
                raise Http404("Unknown deliverable action.")
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Deliverable updated.")
        return redirect("programs:project_profile", pk=deliverable.project_id)


class ChangeRequestDecisionView(ProgramPermissionMixin, FormView):
    form_class = ChangeDecisionForm
    template_name = "programs/workflow_form.html"
    permission_required = PROJECTS_UPDATE

    def get_change(self):
        return get_object_or_404(
            ChangeRequest.objects.select_related("project"),
            pk=self.kwargs["pk"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        change = self.get_change()
        context.update(
            {
                "title": f"Decide change request — {change.title}",
                "entity": change,
                "cancel_url": reverse(
                    "programs:project_profile",
                    kwargs={"pk": change.project_id},
                ),
            }
        )
        return context

    def form_valid(self, form):
        change = self.get_change()
        service = ChangeRequestService(user=self.request.user)
        try:
            service.decide(
                change,
                form.cleaned_data["decision"],
                form.cleaned_data["reviewer_notes"],
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Change request decided.")
        return redirect("programs:project_profile", pk=change.project_id)


class ProjectReportExportView(ProgramPermissionMixin, View):
    permission_required = PROJECTS_EXPORT

    def get(self, request, pk, fmt):
        report = get_object_or_404(
            ProjectReport.objects.select_related("project"), pk=pk
        )
        if fmt not in {"xlsx", "docx", "pdf", "csv"}:
            raise Http404("Unsupported report format.")
        from .report_exports import (
            project_report_csv_response,
            project_report_docx_response,
            project_report_pdf_response,
            project_report_xlsx_response,
        )

        response_map = {
            "xlsx": project_report_xlsx_response,
            "docx": project_report_docx_response,
            "pdf": project_report_pdf_response,
            "csv": project_report_csv_response,
        }
        return response_map[fmt](request.user, report)
