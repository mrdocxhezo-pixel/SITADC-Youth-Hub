from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.qa.forms import (
    DefectForm,
    QAConfigurationForm,
    QualityDashboardForm,
    QualityMetricForm,
    ReleaseCandidateForm,
    TestCaseForm,
    TestDataSetForm,
    TestEnvironmentForm,
    TestPlanForm,
    TestScenarioForm,
    TestSuiteForm,
)
from apps.qa.models import (
    Defect,
    DefectSeverity,
    DefectStatus,
    QAAuditReference,
    QAConfiguration,
    QANotification,
    QualityDashboard,
    QualityMetric,
    QualityMetricType,
    ReleaseCandidate,
    TestCase,
    TestDataSet,
    TestEnvironment,
    TestExecution,
    TestExecutionStatus,
    TestPlan,
    TestPriority,
    TestScenario,
    TestSuite,
)
from apps.qa.selectors import (
    get_active_test_environments,
    get_defect,
    get_defects,
    get_qa_configuration,
    get_qa_notifications,
    get_quality_dashboard,
    get_quality_metrics,
    get_release_candidates,
    get_test_case,
    get_test_cases,
    get_test_data_sets,
    get_test_executions,
    get_test_plan,
    get_test_plans,
    get_test_scenarios,
    get_test_suite,
    get_test_suites,
    user_can_manage_qa,
    user_can_manage_quality_dashboards,
    user_can_view_defects,
    user_can_view_qa,
    user_can_view_quality_dashboards,
    user_can_view_test_cases,
)
from apps.qa.services import (
    DefectService,
    QAConfigurationService,
    QANotificationService,
    QualityDashboardService,
    QualityMetricService,
    ReleaseCandidateService,
    TestCaseService,
    TestDataSetService,
    TestEnvironmentService,
    TestExecutionService,
    TestPlanService,
    TestScenarioService,
    TestSuiteService,
)

User = get_user_model()


class QAPermissionMixin:
    """Mixin to check QA permissions."""

    def dispatch(self, request, *args, **kwargs):
        if not user_can_view_qa(request.user):
            messages.error(request, "You do not have permission to access QA module.")
            return redirect("dashboard:index")
        return super().dispatch(request, *args, **kwargs)


class QAManagePermissionMixin:
    """Mixin to check QA management permissions."""

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_qa(request.user):
            messages.error(request, "You do not have permission to manage QA.")
            return redirect("qa:dashboard")
        return super().dispatch(request, *args, **kwargs)


# Dashboard Views


class QADashboardView(QAPermissionMixin, LoginRequiredMixin, TemplateView):
    """QA Dashboard view."""

    template_name = "qa/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get default dashboard
        dashboard = get_quality_dashboard(self.request.user)
        if dashboard:
            context["dashboard_data"] = QualityDashboardService.get_dashboard_data(
                dashboard
            )
            context["dashboard"] = dashboard

        # Get recent activity
        context["recent_test_plans"] = get_test_plans(self.request.user).order_by(
            "-created_at"
        )[:5]
        context["recent_defects"] = get_defects(user=self.request.user).order_by(
            "-created_at"
        )[:5]
        context["recent_executions"] = get_test_executions(
            user=self.request.user
        ).order_by("-started_at")[:5]
        context["recent_release_candidates"] = get_release_candidates(
            self.request.user
        ).order_by("-created_at")[:5]

        # Get notifications
        context["notifications"] = get_qa_notifications(
            self.request.user, unread_only=True
        )[:10]
        context["unread_count"] = QANotificationService.get_unread_count(
            self.request.user
        )

        return context


# Configuration Views


class QAConfigurationView(QAManagePermissionMixin, LoginRequiredMixin, UpdateView):
    """QA Configuration view."""

    model = QAConfiguration
    form_class = QAConfigurationForm
    template_name = "qa/configuration.html"
    success_url = reverse_lazy("qa:configuration")

    def get_object(self, queryset=None):
        return get_qa_configuration()

    def form_valid(self, form):
        QAConfigurationService.update_configuration(
            self.request.user, **form.cleaned_data
        )
        messages.success(self.request, "QA Configuration updated successfully.")
        return HttpResponseRedirect(self.get_success_url())


# Test Environment Views


class TestEnvironmentListView(QAPermissionMixin, LoginRequiredMixin, ListView):
    """Test Environment list view."""

    model = TestEnvironment
    template_name = "qa/test_environment_list.html"
    context_object_name = "environments"
    paginate_by = 20

    def get_queryset(self):
        return get_active_test_environments(self.request.user).order_by(
            "environment_type", "name"
        )


class TestEnvironmentDetailView(QAPermissionMixin, LoginRequiredMixin, DetailView):
    """Test Environment detail view."""

    model = TestEnvironment
    template_name = "qa/test_environment_detail.html"
    context_object_name = "environment"

    def get_queryset(self):
        return get_active_test_environments(self.request.user)


class TestEnvironmentCreateView(
    QAManagePermissionMixin, LoginRequiredMixin, CreateView
):
    """Test Environment create view."""

    model = TestEnvironment
    form_class = TestEnvironmentForm
    template_name = "qa/test_environment_form.html"
    success_url = reverse_lazy("qa:test_environment_list")

    def form_valid(self, form):
        TestEnvironmentService.create_environment(
            self.request.user, **form.cleaned_data
        )
        messages.success(self.request, "Test Environment created successfully.")
        return HttpResponseRedirect(self.get_success_url())


class TestEnvironmentUpdateView(
    QAManagePermissionMixin, LoginRequiredMixin, UpdateView
):
    """Test Environment update view."""

    model = TestEnvironment
    form_class = TestEnvironmentForm
    template_name = "qa/test_environment_form.html"
    success_url = reverse_lazy("qa:test_environment_list")

    def get_queryset(self):
        return get_active_test_environments(self.request.user)

    def form_valid(self, form):
        TestEnvironmentService.update_environment(
            self.request.user, self.object, **form.cleaned_data
        )
        messages.success(self.request, "Test Environment updated successfully.")
        return HttpResponseRedirect(self.get_success_url())


# Test Data Set Views


class TestDataSetListView(QAPermissionMixin, LoginRequiredMixin, ListView):
    """Test Data Set list view."""

    model = TestDataSet
    template_name = "qa/test_data_set_list.html"
    context_object_name = "data_sets"
    paginate_by = 20

    def get_queryset(self):
        return get_test_data_sets(self.request.user).order_by("-created_at")


class TestDataSetDetailView(QAPermissionMixin, LoginRequiredMixin, DetailView):
    """Test Data Set detail view."""

    model = TestDataSet
    template_name = "qa/test_data_set_detail.html"
    context_object_name = "data_set"

    def get_queryset(self):
        return get_test_data_sets(self.request.user)


class TestDataSetCreateView(QAManagePermissionMixin, LoginRequiredMixin, CreateView):
    """Test Data Set create view."""

    model = TestDataSet
    form_class = TestDataSetForm
    template_name = "qa/test_data_set_form.html"
    success_url = reverse_lazy("qa:test_data_set_list")

    def form_valid(self, form):
        TestDataSetService.create_data_set(self.request.user, **form.cleaned_data)
        messages.success(self.request, "Test Data Set created successfully.")
        return HttpResponseRedirect(self.get_success_url())


# Test Plan Views


class TestPlanListView(QAPermissionMixin, LoginRequiredMixin, ListView):
    """Test Plan list view."""

    model = TestPlan
    template_name = "qa/test_plan_list.html"
    context_object_name = "test_plans"
    paginate_by = 20

    def get_queryset(self):
        return get_test_plans(self.request.user).order_by("-created_at")


class TestPlanDetailView(QAPermissionMixin, LoginRequiredMixin, DetailView):
    """Test Plan detail view."""

    model = TestPlan
    template_name = "qa/test_plan_detail.html"
    context_object_name = "test_plan"

    def get_queryset(self):
        return get_test_plans(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["test_suites"] = get_test_suites(self.object, self.request.user)
        context["test_scenarios"] = get_test_scenarios(self.object, self.request.user)
        return context


class TestPlanCreateView(QAManagePermissionMixin, LoginRequiredMixin, CreateView):
    """Test Plan create view."""

    model = TestPlan
    form_class = TestPlanForm
    template_name = "qa/test_plan_form.html"
    success_url = reverse_lazy("qa:test_plan_list")

    def form_valid(self, form):
        test_plan = TestPlanService.create_test_plan(
            self.request.user, **form.cleaned_data
        )
        messages.success(self.request, "Test Plan created successfully.")
        return redirect("qa:test_plan_detail", pk=test_plan.pk)


class TestPlanUpdateView(QAManagePermissionMixin, LoginRequiredMixin, UpdateView):
    """Test Plan update view."""

    model = TestPlan
    form_class = TestPlanForm
    template_name = "qa/test_plan_form.html"

    def get_queryset(self):
        return get_test_plans(self.request.user)

    def get_success_url(self):
        return reverse("qa:test_plan_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        TestPlanService.update_test_plan(
            self.request.user, self.object, **form.cleaned_data
        )
        messages.success(self.request, "Test Plan updated successfully.")
        return HttpResponseRedirect(self.get_success_url())


class TestPlanApproveView(QAManagePermissionMixin, LoginRequiredMixin, DetailView):
    """Test Plan approve view."""

    model = TestPlan
    template_name = "qa/test_plan_approve.html"

    def get_queryset(self):
        return get_test_plans(self.request.user)

    def post(self, request, *args, **kwargs):
        test_plan = self.get_object()
        TestPlanService.approve_test_plan(request.user, test_plan)
        messages.success(request, "Test Plan approved successfully.")
        return redirect("qa:test_plan_detail", pk=test_plan.pk)


# Test Suite Views


class TestSuiteCreateView(QAManagePermissionMixin, LoginRequiredMixin, CreateView):
    """Test Suite create view."""

    model = TestSuite
    form_class = TestSuiteForm
    template_name = "qa/test_suite_form.html"

    def get_initial(self):
        initial = super().get_initial()
        test_plan = get_test_plan(self.kwargs["test_plan_pk"], self.request.user)
        initial["test_plan"] = test_plan
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["test_plan"] = get_test_plan(
            self.kwargs["test_plan_pk"], self.request.user
        )
        return context

    def form_valid(self, form):
        test_plan = get_test_plan(self.kwargs["test_plan_pk"], self.request.user)
        TestSuiteService.create_test_suite(
            self.request.user, test_plan, **form.cleaned_data
        )
        messages.success(self.request, "Test Suite created successfully.")
        return redirect("qa:test_plan_detail", pk=test_plan.pk)


class TestSuiteUpdateView(QAManagePermissionMixin, LoginRequiredMixin, UpdateView):
    """Test Suite update view."""

    model = TestSuite
    form_class = TestSuiteForm
    template_name = "qa/test_suite_form.html"

    def get_queryset(self):
        return get_test_suites(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["test_plan"] = self.object.test_plan
        return context

    def get_success_url(self):
        return reverse("qa:test_plan_detail", kwargs={"pk": self.object.test_plan.pk})

    def form_valid(self, form):
        messages.success(self.request, "Test Suite updated successfully.")
        return super().form_valid(form)


# Test Case Views


class TestCaseListView(QAPermissionMixin, LoginRequiredMixin, ListView):
    """Test Case list view."""

    model = TestCase
    template_name = "qa/test_case_list.html"
    context_object_name = "test_cases"
    paginate_by = 50

    def get_queryset(self):
        test_suite_pk = self.kwargs.get("test_suite_pk")
        test_suite = None
        if test_suite_pk:
            test_suite = get_test_suite(test_suite_pk, self.request.user)
        return get_test_cases(test_suite, self.request.user).order_by("test_id")


class TestCaseDetailView(QAPermissionMixin, LoginRequiredMixin, DetailView):
    """Test Case detail view."""

    model = TestCase
    template_name = "qa/test_case_detail.html"
    context_object_name = "test_case"

    def get_queryset(self):
        return get_test_cases(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["executions"] = get_test_executions(
            test_case=self.object, user=self.request.user
        ).order_by("-started_at")[:10]
        context["defects"] = get_defects(test_case=self.object, user=self.request.user)
        return context


class TestCaseCreateView(QAManagePermissionMixin, LoginRequiredMixin, CreateView):
    """Test Case create view."""

    model = TestCase
    form_class = TestCaseForm
    template_name = "qa/test_case_form.html"

    def get_initial(self):
        initial = super().get_initial()
        test_suite = get_test_suite(self.kwargs["test_suite_pk"], self.request.user)
        initial["test_suite"] = test_suite
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["test_suite"] = get_test_suite(
            self.kwargs["test_suite_pk"], self.request.user
        )
        return context

    def form_valid(self, form):
        test_suite = get_test_suite(self.kwargs["test_suite_pk"], self.request.user)
        test_case = TestCaseService.create_test_case(
            self.request.user, test_suite, **form.cleaned_data
        )
        messages.success(self.request, "Test Case created successfully.")
        return redirect("qa:test_case_detail", pk=test_case.pk)


class TestCaseUpdateView(QAManagePermissionMixin, LoginRequiredMixin, UpdateView):
    """Test Case update view."""

    model = TestCase
    form_class = TestCaseForm
    template_name = "qa/test_case_form.html"

    def get_queryset(self):
        return get_test_cases(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["test_suite"] = self.object.test_suite
        return context

    def get_success_url(self):
        return reverse("qa:test_case_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        TestCaseService.update_test_case(
            self.request.user, self.object, **form.cleaned_data
        )
        messages.success(self.request, "Test Case updated successfully.")
        return HttpResponseRedirect(self.get_success_url())


# Test Scenario Views


class TestScenarioCreateView(QAManagePermissionMixin, LoginRequiredMixin, CreateView):
    """Test Scenario create view."""

    model = TestScenario
    form_class = TestScenarioForm
    template_name = "qa/test_scenario_form.html"

    def get_initial(self):
        initial = super().get_initial()
        test_plan = get_test_plan(self.kwargs["test_plan_pk"], self.request.user)
        initial["test_plan"] = test_plan
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        test_plan = get_test_plan(self.kwargs["test_plan_pk"], self.request.user)
        context["test_plan"] = test_plan
        context["available_test_cases"] = get_test_cases(user=self.request.user)
        return context

    def form_valid(self, form):
        test_plan = get_test_plan(self.kwargs["test_plan_pk"], self.request.user)
        test_case_ids = self.request.POST.getlist("test_cases")
        TestScenarioService.create_test_scenario(
            self.request.user, test_plan, test_case_ids, **form.cleaned_data
        )
        messages.success(self.request, "Test Scenario created successfully.")
        return redirect("qa:test_plan_detail", pk=test_plan.pk)


# Test Execution Views


class TestExecutionListView(QAPermissionMixin, LoginRequiredMixin, ListView):
    """Test Execution list view."""

    model = TestExecution
    template_name = "qa/test_execution_list.html"
    context_object_name = "executions"
    paginate_by = 50

    def get_queryset(self):
        test_plan_pk = self.kwargs.get("test_plan_pk")
        test_suite_pk = self.kwargs.get("test_suite_pk")
        test_case_pk = self.kwargs.get("test_case_pk")

        test_plan = (
            get_test_plan(test_plan_pk, self.request.user) if test_plan_pk else None
        )
        test_suite = (
            get_test_suite(test_suite_pk, self.request.user) if test_suite_pk else None
        )
        test_case = (
            get_test_case(test_case_pk, self.request.user) if test_case_pk else None
        )

        return get_test_executions(
            test_plan, test_suite, test_case, self.request.user
        ).order_by("-started_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.kwargs.get("test_plan_pk"):
            context["test_plan"] = get_test_plan(
                self.kwargs["test_plan_pk"], self.request.user
            )
        if self.kwargs.get("test_suite_pk"):
            context["test_suite"] = get_test_suite(
                self.kwargs["test_suite_pk"], self.request.user
            )
        if self.kwargs.get("test_case_pk"):
            context["test_case"] = get_test_case(
                self.kwargs["test_case_pk"], self.request.user
            )
        return context


class TestExecutionDetailView(QAPermissionMixin, LoginRequiredMixin, DetailView):
    """Test Execution detail view."""

    model = TestExecution
    template_name = "qa/test_execution_detail.html"
    context_object_name = "execution"

    def get_queryset(self):
        return get_test_executions(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["results"] = self.object.test_results.all()
        context["evidence"] = self.object.evidence.all()
        return context


class TestExecutionStartView(QAManagePermissionMixin, LoginRequiredMixin, DetailView):
    """Start test execution view."""

    model = TestCase
    template_name = "qa/test_execution_start.html"

    def get_queryset(self):
        return get_test_cases(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["test_plan"] = get_test_plan(
            self.kwargs["test_plan_pk"], self.request.user
        )
        context["test_suite"] = get_test_suite(
            self.kwargs["test_suite_pk"], self.request.user
        )
        context["environments"] = get_active_test_environments(self.request.user)
        context["data_sets"] = get_test_data_sets(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        test_case = self.get_object()
        test_plan = get_test_plan(self.kwargs["test_plan_pk"], request.user)
        test_suite = get_test_suite(self.kwargs["test_suite_pk"], request.user)
        environment_id = request.POST.get("environment")
        data_set_id = request.POST.get("test_data_set")
        is_regression = request.POST.get("is_regression") == "on"

        environment = None
        if environment_id:
            from apps.qa.models import TestEnvironment

            environment = TestEnvironment.objects.filter(
                pk=environment_id, is_active=True
            ).first()

        data_set = None
        if data_set_id:
            from apps.qa.models import TestDataSet

            data_set = TestDataSet.objects.filter(
                pk=data_set_id, is_active=True
            ).first()

        execution = TestExecutionService.start_execution(
            request.user,
            test_case,
            test_plan,
            test_suite,
            environment,
            data_set,
            is_regression,
        )

        messages.success(request, "Test execution started.")
        return redirect("qa:test_execution_detail", pk=execution.pk)


class TestExecutionCompleteView(
    QAManagePermissionMixin, LoginRequiredMixin, DetailView
):
    """Complete test execution view."""

    model = TestExecution
    template_name = "qa/test_execution_complete.html"

    def get_queryset(self):
        return get_test_executions(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = [
            (TestExecutionStatus.PASSED, "Passed"),
            (TestExecutionStatus.FAILED, "Failed"),
            (TestExecutionStatus.BLOCKED, "Blocked"),
            (TestExecutionStatus.SKIPPED, "Skipped"),
            (TestExecutionStatus.ERROR, "Error"),
        ]
        context["defects"] = get_defects(user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        execution = self.get_object()
        status = request.POST.get("status")
        actual_results = request.POST.get("actual_results", "")
        error_message = request.POST.get("error_message", "")
        stack_trace = request.POST.get("stack_trace", "")
        duration_seconds = int(request.POST.get("duration_seconds", 0))
        defect_id = request.POST.get("defect")

        defect = None
        if defect_id:
            defect = get_defect(defect_id, request.user)

        TestExecutionService.complete_execution(
            request.user,
            execution,
            status,
            actual_results=[actual_results] if actual_results else [],
            error_message=error_message,
            stack_trace=stack_trace,
            duration_seconds=duration_seconds,
            defect=defect,
        )

        messages.success(request, "Test execution completed.")
        return redirect("qa:test_execution_detail", pk=execution.pk)


# Defect Views


class DefectListView(QAPermissionMixin, LoginRequiredMixin, ListView):
    """Defect list view."""

    model = Defect
    template_name = "qa/defect_list.html"
    context_object_name = "defects"
    paginate_by = 50

    def get_queryset(self):
        return get_defects(user=self.request.user).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = DefectStatus.CHOICES
        context["severity_choices"] = DefectSeverity.CHOICES
        context["priority_choices"] = TestPriority.CHOICES
        return context


class DefectDetailView(QAPermissionMixin, LoginRequiredMixin, DetailView):
    """Defect detail view."""

    model = Defect
    template_name = "qa/defect_detail.html"
    context_object_name = "defect"

    def get_queryset(self):
        return get_defects(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assignments"] = self.object.assignments.all()
        context["resolutions"] = self.object.resolutions.all()
        context["executions"] = self.object.test_executions.all()
        return context


class DefectCreateView(QAManagePermissionMixin, LoginRequiredMixin, CreateView):
    """Defect create view."""

    model = Defect
    form_class = DefectForm
    template_name = "qa/defect_form.html"
    success_url = reverse_lazy("qa:defect_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["test_plan_pk"] = self.kwargs.get("test_plan_pk")
        context["test_suite_pk"] = self.kwargs.get("test_suite_pk")
        context["test_case_pk"] = self.kwargs.get("test_case_pk")
        return context

    def get_initial(self):
        initial = super().get_initial()
        if self.kwargs.get("test_case_pk"):
            test_case = get_test_case(self.kwargs["test_case_pk"], self.request.user)
            initial["test_case"] = test_case
            initial["module"] = test_case.module
            initial["feature"] = test_case.feature
        if self.kwargs.get("test_execution_pk"):
            from apps.qa.models import TestExecution

            execution = TestExecution.objects.filter(
                pk=self.kwargs["test_execution_pk"]
            ).first()
            if execution:
                initial["test_execution"] = execution
        return initial

    def form_valid(self, form):
        defect = DefectService.create_defect(self.request.user, **form.cleaned_data)
        messages.success(self.request, "Defect created successfully.")
        return redirect("qa:defect_detail", pk=defect.pk)


class DefectUpdateView(QAManagePermissionMixin, LoginRequiredMixin, UpdateView):
    """Defect update view."""

    model = Defect
    form_class = DefectForm
    template_name = "qa/defect_form.html"

    def get_queryset(self):
        return get_defects(user=self.request.user)

    def get_success_url(self):
        return reverse("qa:defect_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        DefectService.update_defect(self.request.user, self.object, **form.cleaned_data)
        messages.success(self.request, "Defect updated successfully.")
        return HttpResponseRedirect(self.get_success_url())


class DefectResolveView(QAManagePermissionMixin, LoginRequiredMixin, DetailView):
    """Defect resolve view."""

    model = Defect
    template_name = "qa/defect_resolve.html"

    def get_queryset(self):
        return get_defects(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resolution_types"] = [
            ("FIXED", "Fixed"),
            ("WONT_FIX", "Won't Fix"),
            ("DUPLICATE", "Duplicate"),
            ("NOT_REPRODUCIBLE", "Not Reproducible"),
            ("BY_DESIGN", "By Design"),
            ("WORKAROUND", "Workaround"),
        ]
        return context

    def post(self, request, *args, **kwargs):
        defect = self.get_object()
        resolution_type = request.POST.get("resolution_type")
        resolution_notes = request.POST.get("resolution_notes")
        code_changes = request.POST.get("code_changes", "")

        DefectService.resolve_defect(
            request.user,
            defect,
            resolution_type,
            resolution_notes,
            code_changes=code_changes.split("\n") if code_changes else [],
        )
        messages.success(request, "Defect resolved successfully.")
        return redirect("qa:defect_detail", pk=defect.pk)


class DefectVerifyView(QAManagePermissionMixin, LoginRequiredMixin, DetailView):
    """Defect verify view."""

    model = Defect
    template_name = "qa/defect_verify.html"

    def get_queryset(self):
        return get_defects(user=self.request.user)

    def post(self, request, *args, **kwargs):
        defect = self.get_object()
        DefectService.verify_defect(request.user, defect)
        messages.success(request, "Defect verified successfully.")
        return redirect("qa:defect_detail", pk=defect.pk)


class DefectCloseView(QAManagePermissionMixin, LoginRequiredMixin, DetailView):
    """Defect close view."""

    model = Defect
    template_name = "qa/defect_close.html"

    def get_queryset(self):
        return get_defects(user=self.request.user)

    def post(self, request, *args, **kwargs):
        defect = self.get_object()
        regression_tested = request.POST.get("regression_tested") == "on"
        DefectService.close_defect(request.user, defect, regression_tested)
        messages.success(request, "Defect closed successfully.")
        return redirect("qa:defect_detail", pk=defect.pk)


# Release Candidate Views


class ReleaseCandidateListView(QAPermissionMixin, LoginRequiredMixin, ListView):
    """Release Candidate list view."""

    model = ReleaseCandidate
    template_name = "qa/release_candidate_list.html"
    context_object_name = "releases"
    paginate_by = 20

    def get_queryset(self):
        return get_release_candidates(self.request.user).order_by("-created_at")


class ReleaseCandidateDetailView(QAPermissionMixin, LoginRequiredMixin, DetailView):
    """Release Candidate detail view."""

    model = ReleaseCandidate
    template_name = "qa/release_candidate_detail.html"
    context_object_name = "release"

    def get_queryset(self):
        return get_release_candidates(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["approvals"] = self.object.approvals.all()
        context["uat_sessions"] = self.object.uat_sessions.all()
        context["regression_tests"] = self.object.regression_tests.all()
        context["test_plans"] = self.object.test_plans.all()
        return context


class ReleaseCandidateCreateView(
    QAManagePermissionMixin, LoginRequiredMixin, CreateView
):
    """Release Candidate create view."""

    model = ReleaseCandidate
    form_class = ReleaseCandidateForm
    template_name = "qa/release_candidate_form.html"
    success_url = reverse_lazy("qa:release_candidate_list")

    def form_valid(self, form):
        ReleaseCandidateService.create_release_candidate(
            self.request.user, **form.cleaned_data
        )
        messages.success(self.request, "Release Candidate created successfully.")
        return HttpResponseRedirect(self.get_success_url())


class ReleaseCandidateSubmitView(
    QAManagePermissionMixin, LoginRequiredMixin, DetailView
):
    """Submit release candidate for testing."""

    model = ReleaseCandidate
    template_name = "qa/release_candidate_submit.html"

    def get_queryset(self):
        return get_release_candidates(self.request.user)

    def post(self, request, *args, **kwargs):
        release = self.get_object()
        ReleaseCandidateService.submit_for_testing(request.user, release)
        messages.success(request, "Release Candidate submitted for testing.")
        return redirect("qa:release_candidate_detail", pk=release.pk)


class ReleaseCandidateApproveView(
    QAManagePermissionMixin, LoginRequiredMixin, DetailView
):
    """Approve release candidate."""

    model = ReleaseCandidate
    template_name = "qa/release_candidate_approve.html"

    def get_queryset(self):
        return get_release_candidates(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["required_roles"] = [
            "QA Lead",
            "Security Lead",
            "Performance Lead",
            "Product Owner",
        ]
        return context

    def post(self, request, *args, **kwargs):
        release = self.get_object()
        role = request.POST.get("role")
        comments = request.POST.get("comments", "")
        conditions = request.POST.get("conditions", "")

        ReleaseCandidateService.approve_release(
            request.user, release, role, comments, conditions
        )
        messages.success(request, "Release approval recorded.")
        return redirect("qa:release_candidate_detail", pk=release.pk)


# Quality Metrics Views


class QualityMetricListView(QAPermissionMixin, LoginRequiredMixin, ListView):
    """Quality Metric list view."""

    model = QualityMetric
    template_name = "qa/quality_metric_list.html"
    context_object_name = "metrics"
    paginate_by = 50

    def get_queryset(self):
        return get_quality_metrics(user=self.request.user).order_by("-period_end")


class QualityMetricCreateView(QAManagePermissionMixin, LoginRequiredMixin, CreateView):
    """Quality Metric create view."""

    model = QualityMetric
    form_class = QualityMetricForm
    template_name = "qa/quality_metric_form.html"
    success_url = reverse_lazy("qa:quality_metric_list")

    def form_valid(self, form):
        # Metrics are typically calculated, not manually created
        # This is for manual entry if needed
        messages.success(self.request, "Quality Metric recorded.")
        return super().form_valid(form)


class QualityMetricCalculateView(
    QAManagePermissionMixin, LoginRequiredMixin, TemplateView
):
    """Calculate quality metrics view."""

    template_name = "qa/quality_metric_calculate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["metric_types"] = QualityMetricType.CHOICES
        return context

    def post(self, request, *args, **kwargs):
        period_start = request.POST.get("period_start")
        period_end = request.POST.get("period_end")
        module = request.POST.get("module", "")

        if period_start and period_end:
            period_start = timezone.datetime.fromisoformat(period_start)
            period_end = timezone.datetime.fromisoformat(period_end)
            metrics = QualityMetricService.calculate_metrics(
                request.user, period_start, period_end, module
            )
            messages.success(request, f"Calculated {len(metrics)} quality metrics.")
        else:
            messages.error(request, "Please provide valid period start and end dates.")

        return redirect("qa:quality_metric_list")


# Quality Dashboard Views


class QualityDashboardListView(QAPermissionMixin, LoginRequiredMixin, ListView):
    """Quality Dashboard list view."""

    model = QualityDashboard
    template_name = "qa/quality_dashboard_list.html"
    context_object_name = "dashboards"
    paginate_by = 20

    def get_queryset(self):
        if user_can_manage_quality_dashboards(self.request.user):
            return QualityDashboard.objects.filter(is_active=True).order_by("name")
        return QualityDashboard.objects.filter(
            is_active=True, is_default=True
        ).order_by("name")


class QualityDashboardDetailView(QAPermissionMixin, LoginRequiredMixin, DetailView):
    """Quality Dashboard detail view."""

    model = QualityDashboard
    template_name = "qa/quality_dashboard_detail.html"
    context_object_name = "dashboard"

    def get_queryset(self):
        if user_can_manage_quality_dashboards(self.request.user):
            return QualityDashboard.objects.filter(is_active=True)
        return QualityDashboard.objects.filter(is_active=True, is_default=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dashboard_data"] = QualityDashboardService.get_dashboard_data(
            self.object
        )
        return context


class QualityDashboardCreateView(
    QAManagePermissionMixin, LoginRequiredMixin, CreateView
):
    """Quality Dashboard create view."""

    model = QualityDashboard
    form_class = QualityDashboardForm
    template_name = "qa/quality_dashboard_form.html"
    success_url = reverse_lazy("qa:quality_dashboard_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Quality Dashboard created successfully.")
        return super().form_valid(form)


# Notification Views


class QANotificationListView(QAPermissionMixin, LoginRequiredMixin, ListView):
    """QA Notification list view."""

    model = QANotification
    template_name = "qa/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 50

    def get_queryset(self):
        unread_only = self.request.GET.get("unread") == "true"
        return get_qa_notifications(self.request.user, unread_only).order_by(
            "-created_at"
        )


class QANotificationMarkReadView(QAPermissionMixin, LoginRequiredMixin, DetailView):
    """Mark notification as read."""

    model = QANotification

    def get_queryset(self):
        return get_qa_notifications(self.request.user)

    def post(self, request, *args, **kwargs):
        notification = self.get_object()
        QANotificationService.mark_as_read(request.user, notification)
        return JsonResponse({"success": True})


class QANotificationMarkAllReadView(
    QAPermissionMixin, LoginRequiredMixin, TemplateView
):
    """Mark all notifications as read."""

    def post(self, request, *args, **kwargs):
        count = QANotificationService.mark_all_as_read(request.user)
        messages.success(request, f"Marked {count} notifications as read.")
        return redirect("qa:notification_list")


# Audit Views


class QAAuditReferenceListView(QAManagePermissionMixin, LoginRequiredMixin, ListView):
    """QA Audit Reference list view."""

    model = QAAuditReference
    template_name = "qa/audit_reference_list.html"
    context_object_name = "audit_references"
    paginate_by = 50

    def get_queryset(self):
        return QAAuditReference.objects.select_related("user").order_by("-timestamp")


class QAAuditReferenceDetailView(
    QAManagePermissionMixin, LoginRequiredMixin, DetailView
):
    """QA Audit Reference detail view."""

    model = QAAuditReference
    template_name = "qa/audit_reference_detail.html"
    context_object_name = "audit_reference"

    def get_queryset(self):
        return QAAuditReference.objects.select_related("user")


# API Views


def qa_dashboard_data_api(request):
    """API endpoint for dashboard data."""
    if not user_can_view_quality_dashboards(request.user):
        return JsonResponse({"error": "Permission denied"}, status=403)

    dashboard = get_quality_dashboard(request.user)
    if not dashboard:
        return JsonResponse({"error": "No dashboard found"}, status=404)

    data = QualityDashboardService.get_dashboard_data(dashboard)
    return JsonResponse(data)


def qa_notification_count_api(request):
    """API endpoint for notification count."""
    if not request.user.is_authenticated:
        return JsonResponse({"count": 0})

    count = QANotificationService.get_unread_count(request.user)
    return JsonResponse({"count": count})


def test_case_autocomplete_api(request):
    """API endpoint for test case autocomplete."""
    if not user_can_view_test_cases(request.user):
        return JsonResponse({"results": []})

    q = request.GET.get("q", "")
    test_cases = get_test_cases(user=request.user).filter(
        Q(test_id__icontains=q) | Q(title__icontains=q)
    )[:20]

    results = [{"id": tc.pk, "text": f"{tc.test_id}: {tc.title}"} for tc in test_cases]
    return JsonResponse({"results": results})


def defect_autocomplete_api(request):
    """API endpoint for defect autocomplete."""
    if not user_can_view_defects(request.user):
        return JsonResponse({"results": []})

    q = request.GET.get("q", "")
    defects = get_defects(user=request.user).filter(
        Q(defect_id__icontains=q) | Q(title__icontains=q)
    )[:20]

    results = [{"id": d.pk, "text": f"{d.defect_id}: {d.title}"} for d in defects]
    return JsonResponse({"results": results})
