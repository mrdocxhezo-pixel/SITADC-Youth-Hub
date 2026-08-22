"""Views for the Accessibility Review module (Phase 33)."""

from __future__ import annotations

import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView

from apps.accessibility.permissions import (
    ACCESSIBILITY_APPROVE,
    ACCESSIBILITY_AUDIT,
    ACCESSIBILITY_CONFIGURE,
    ACCESSIBILITY_CREATE,
    ACCESSIBILITY_MANAGE,
    ACCESSIBILITY_REPORT,
    ACCESSIBILITY_UPDATE,
    ACCESSIBILITY_VIEW,
)
from apps.rbac.authorization import user_has_permission

from .forms import (
    AccessibilityAuditForm,
    AccessibilityConfigurationForm,
    AccessibilityExceptionForm,
    AccessibilityFindingForm,
    AccessibilityIssueForm,
    AccessibilityPolicyForm,
    AccessibilityPreferenceForm,
    AccessibilityRecommendationForm,
    AccessibilityStandardForm,
    WCAGCriterionForm,
)
from .models import (
    AccessibilityAnalytics,
    AccessibilityAudit,
    AccessibilityComplianceRecord,
    AccessibilityConfiguration,
    AccessibilityFinding,
    AccessibilityIssue,
    AccessibilityPolicy,
    AccessibilityRecommendation,
    AccessibilityStandardRecord,
    AccessibilityTimeline,
    WCAGCriterion,
)
from .services import (
    AccessibilityAnalyticsService,
    AccessibilityAuditService,
    AccessibilityConfigurationService,
    AccessibilityExceptionService,
    AccessibilityIssueService,
    AccessibilityPolicyService,
    AccessibilityPreferenceService,
    AccessibilityRecommendationService,
    AccessibilityStandardService,
    WCAGCriterionService,
)


def _can(user, *permission_codes: str) -> bool:
    return user_has_permission(user, ACCESSIBILITY_MANAGE) or any(
        user_has_permission(user, code) for code in permission_codes
    )


class AccessibilityPermissionMixin(LoginRequiredMixin):
    """Mixin that checks accessibility permissions."""

    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        required = self.permission_required
        permissions = (required,) if isinstance(required, str) else tuple(required)
        if not _can(request.user, *permissions):
            messages.error(request, "You do not have permission to access this page.")
            return redirect("accessibility:dashboard")
        return super().dispatch(request, *args, **kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────────────────────────────────────

class AccessibilityDashboardView(AccessibilityPermissionMixin, TemplateView):
    template_name = "accessibility/dashboard.html"
    permission_required = ACCESSIBILITY_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()
        today - timedelta(days=30)

        # Overall metrics
        context["metrics"] = {
            "standards": AccessibilityStandardRecord.objects.filter(is_active=True).count(),
            "policies": AccessibilityPolicy.objects.filter(is_active=True).count(),
            "audits_total": AccessibilityAudit.objects.count(),
            "audits_completed": AccessibilityAudit.objects.filter(status="COMPLIANT").count(),
            "open_findings": AccessibilityFinding.objects.filter(status__in=["OPEN", "IN_PROGRESS", "NEEDS_REVIEW"]).count(),
            "critical_findings": AccessibilityFinding.objects.filter(severity="CRITICAL", status__in=["OPEN", "IN_PROGRESS"]).count(),
            "open_issues": AccessibilityIssue.objects.filter(status__in=["OPEN", "IN_PROGRESS", "NEEDS_REVIEW"]).count(),
            "critical_issues": AccessibilityIssue.objects.filter(severity="CRITICAL", status__in=["OPEN", "IN_PROGRESS"]).count(),
            "recommendations_open": AccessibilityRecommendation.objects.filter(status__in=["OPEN", "IN_PROGRESS"]).count(),
        }

        # Compliance by module
        context["compliance_by_module"] = list(
            AccessibilityComplianceRecord.objects.values("module")
            .annotate(
                total=Count("id"),
                compliant=Count("id", filter=Q(compliance_status="COMPLIANT")),
                non_compliant=Count("id", filter=Q(compliance_status="NON_COMPLIANT")),
                partial=Count("id", filter=Q(compliance_status="PARTIAL")),
            )
            .order_by("-total")
        )

        # Recent audits
        context["recent_audits"] = AccessibilityAudit.objects.select_related("standard", "auditor").order_by("-created_at")[:5]

        # Open findings by severity
        context["findings_by_severity"] = list(
            AccessibilityFinding.objects.filter(status__in=["OPEN", "IN_PROGRESS"])
            .values("severity")
            .annotate(count=Count("id"))
            .order_by("severity")
        )

        # Issues by source
        context["issues_by_source"] = list(
            AccessibilityIssue.objects.filter(status__in=["OPEN", "IN_PROGRESS"])
            .values("source")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Latest analytics snapshot
        context["latest_analytics"] = AccessibilityAnalytics.objects.order_by("-snapshot_date").first()

        # Permissions
        context["can_create"] = _can(user, ACCESSIBILITY_CREATE)
        context["can_audit"] = _can(user, ACCESSIBILITY_AUDIT)
        context["can_configure"] = _can(user, ACCESSIBILITY_CONFIGURE)
        context["can_report"] = _can(user, ACCESSIBILITY_REPORT)
        context["can_approve"] = _can(user, ACCESSIBILITY_APPROVE)

        return context


# ──────────────────────────────────────────────────────────────────────────────
# Standard CRUD
# ──────────────────────────────────────────────────────────────────────────────

class StandardListView(AccessibilityPermissionMixin, ListView):
    model = AccessibilityStandardRecord
    template_name = "accessibility/standard_list.html"
    context_object_name = "standards"
    paginate_by = 20
    permission_required = ACCESSIBILITY_VIEW

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q))
        return qs


class StandardCreateView(AccessibilityPermissionMixin, FormView):
    template_name = "accessibility/standard_form.html"
    form_class = AccessibilityStandardForm
    permission_required = ACCESSIBILITY_CREATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Accessibility Standard"
        context["is_update"] = False
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AccessibilityStandardService(user=self.request.user).create(
                code=data["code"],
                name=data["name"],
                standard_type=data["standard_type"],
                version=data.get("version", "2.2"),
                target_level=data.get("target_level", "AA"),
                description=data.get("description", ""),
                reference_url=data.get("reference_url", ""),
                effective_date=data["effective_date"],
                review_date=data.get("review_date"),
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Accessibility standard created.")
        return redirect("accessibility:standard_list")


class StandardUpdateView(AccessibilityPermissionMixin, FormView):
    template_name = "accessibility/standard_form.html"
    form_class = AccessibilityStandardForm
    permission_required = ACCESSIBILITY_UPDATE

    def dispatch(self, request, *args, **kwargs):
        self.standard = get_object_or_404(AccessibilityStandardRecord, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        std = self.standard
        return {
            "code": std.code,
            "name": std.name,
            "standard_type": std.standard_type,
            "version": std.version,
            "target_level": std.target_level,
            "description": std.description,
            "reference_url": std.reference_url,
            "effective_date": std.effective_date,
            "review_date": std.review_date,
            "is_active": std.is_active,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Accessibility Standard"
        context["is_update"] = True
        context["object"] = self.standard
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AccessibilityStandardService(user=self.request.user).update(self.standard, **data)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Accessibility standard updated.")
        return redirect("accessibility:standard_list")


# ──────────────────────────────────────────────────────────────────────────────
# Policy CRUD
# ──────────────────────────────────────────────────────────────────────────────

class PolicyListView(AccessibilityPermissionMixin, ListView):
    model = AccessibilityPolicy
    template_name = "accessibility/policy_list.html"
    context_object_name = "policies"
    paginate_by = 20
    permission_required = ACCESSIBILITY_VIEW

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)
        q = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(reference_number__icontains=q))
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category_choices"] = AccessibilityPolicy._meta.get_field("category").choices
        return context


class PolicyCreateView(AccessibilityPermissionMixin, FormView):
    template_name = "accessibility/policy_form.html"
    form_class = AccessibilityPolicyForm
    permission_required = ACCESSIBILITY_CREATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Accessibility Policy"
        context["is_update"] = False
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AccessibilityPolicyService(user=self.request.user).create(
                reference_number=data["reference_number"],
                title=data["title"],
                standard=data["standard"],
                category=data["category"],
                description=data.get("description", ""),
                requirements=data.get("requirements", []),
                scope=data.get("scope", ""),
                exceptions=data.get("exceptions", ""),
                version=data.get("version", "1.0"),
                approved_by=data.get("approved_by"),
                approved_date=data.get("approved_date"),
                effective_date=data["effective_date"],
                review_date=data["review_date"],
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Accessibility policy created.")
        return redirect("accessibility:policy_list")


class PolicyUpdateView(AccessibilityPermissionMixin, FormView):
    template_name = "accessibility/policy_form.html"
    form_class = AccessibilityPolicyForm
    permission_required = ACCESSIBILITY_UPDATE

    def dispatch(self, request, *args, **kwargs):
        self.policy = get_object_or_404(AccessibilityPolicy, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        p = self.policy
        return {
            "reference_number": p.reference_number,
            "title": p.title,
            "standard": p.standard_id,
            "category": p.category,
            "description": p.description,
            "requirements": p.requirements,
            "scope": p.scope,
            "exceptions": p.exceptions,
            "version": p.version,
            "approved_by": p.approved_by_id,
            "approved_date": p.approved_date,
            "effective_date": p.effective_date,
            "review_date": p.review_date,
            "is_active": p.is_active,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Accessibility Policy"
        context["is_update"] = True
        context["object"] = self.policy
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AccessibilityPolicyService(user=self.request.user).update(self.policy, **data)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Accessibility policy updated.")
        return redirect("accessibility:policy_list")


# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

class ConfigurationView(AccessibilityPermissionMixin, FormView):
    template_name = "accessibility/configuration.html"
    form_class = AccessibilityConfigurationForm
    permission_required = ACCESSIBILITY_CONFIGURE

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        config = AccessibilityConfiguration.load()
        for field in form.fields:
            if field in form.initial:
                continue
            if hasattr(config, field):
                value = getattr(config, field)
                if value is not None:
                    if isinstance(value, list | dict):
                        form.initial[field] = json.dumps(value, indent=2)
                    else:
                        form.initial[field] = value
        return form

    def form_valid(self, form):
        data = form.cleaned_data
        for field in ("scan_modules", "notification_recipients"):
            raw = data.get(field)
            if isinstance(raw, str):
                try:
                    data[field] = json.loads(raw)
                except json.JSONDecodeError:
                    data[field] = []
        try:
            AccessibilityConfigurationService(user=self.request.user).update(**data)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Accessibility configuration updated.")
        return redirect("accessibility:configuration")


# ──────────────────────────────────────────────────────────────────────────────
# User Preferences
# ──────────────────────────────────────────────────────────────────────────────

class UserPreferenceView(AccessibilityPermissionMixin, FormView):
    template_name = "accessibility/user_preferences.html"
    form_class = AccessibilityPreferenceForm
    permission_required = ACCESSIBILITY_VIEW

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = AccessibilityPreferenceService().get_or_create_for_user(self.request.user)
        return kwargs

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AccessibilityPreferenceService(user=self.request.user).update_preferences(
                self.request.user, **data
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Accessibility preferences saved.")
        return redirect("accessibility:user_preferences")


# ──────────────────────────────────────────────────────────────────────────────
# WCAG Criteria
# ──────────────────────────────────────────────────────────────────────────────

class WCAGCriterionListView(AccessibilityPermissionMixin, ListView):
    model = WCAGCriterion
    template_name = "accessibility/criterion_list.html"
    context_object_name = "criteria"
    paginate_by = 50
    permission_required = ACCESSIBILITY_VIEW

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True).select_related("standard")
        q = self.request.GET.get("q", "").strip()
        principle = self.request.GET.get("principle", "").strip()
        level = self.request.GET.get("level", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(guideline_number__icontains=q) | Q(criterion_number__icontains=q))
        if principle:
            qs = qs.filter(principle=principle)
        if level:
            qs = qs.filter(level=level)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["principle_choices"] = WCAGCriterion._meta.get_field("principle").choices
        context["level_choices"] = WCAGCriterion._meta.get_field("level").choices
        return context


class WCAGCriterionCreateView(AccessibilityPermissionMixin, FormView):
    template_name = "accessibility/criterion_form.html"
    form_class = WCAGCriterionForm
    permission_required = ACCESSIBILITY_CONFIGURE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "WCAG Criterion"
        context["is_update"] = False
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            WCAGCriterionService(user=self.request.user).create(
                standard=data["standard"],
                guideline_number=data["guideline_number"],
                criterion_number=data["criterion_number"],
                title=data["title"],
                description=data.get("description", ""),
                principle=data["principle"],
                level=data["level"],
                category=data["category"],
                understanding_url=data.get("understanding_url", ""),
                techniques_url=data.get("techniques_url", ""),
                how_to_meet_url=data.get("how_to_meet_url", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "WCAG criterion added.")
        return redirect("accessibility:criterion_list")


# ──────────────────────────────────────────────────────────────────────────────
# Audit & Finding Views
# ──────────────────────────────────────────────────────────────────────────────

class AuditListView(AccessibilityPermissionMixin, ListView):
    model = AccessibilityAudit
    template_name = "accessibility/audit_list.html"
    context_object_name = "audits"
    paginate_by = 20
    permission_required = ACCESSIBILITY_VIEW

    def get_queryset(self):
        qs = super().get_queryset().select_related("standard", "auditor")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        audit_type = self.request.GET.get("audit_type", "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(reference_number__icontains=q) | Q(module__icontains=q))
        if status:
            qs = qs.filter(status=status)
        if audit_type:
            qs = qs.filter(audit_type=audit_type)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = AccessibilityAudit._meta.get_field("status").choices
        context["audit_type_choices"] = AccessibilityAudit._meta.get_field("audit_type").choices
        return context


class AuditCreateView(AccessibilityPermissionMixin, FormView):
    template_name = "accessibility/audit_form.html"
    form_class = AccessibilityAuditForm
    permission_required = ACCESSIBILITY_AUDIT

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Accessibility Audit"
        context["is_update"] = False
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            audit = AccessibilityAuditService(user=self.request.user).create_audit(
                name=data["name"],
                audit_type=data["audit_type"],
                scope=data["scope"],
                standard=data["standard"],
                module=data.get("module", ""),
                component=data.get("component", ""),
                page_url=data.get("page_url", ""),
                auditor=data.get("auditor"),
                target_level=data.get("target_level", "AA"),
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, f"Audit created: {audit.reference_number}")
        return redirect("accessibility:audit_detail", pk=audit.pk)


class AuditDetailView(AccessibilityPermissionMixin, DetailView):
    model = AccessibilityAudit
    template_name = "accessibility/audit_detail.html"
    context_object_name = "audit"
    permission_required = ACCESSIBILITY_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        audit = self.object
        context["findings"] = audit.findings.select_related("criterion", "assigned_to").order_by("-severity", "-created_at")
        context["can_add_finding"] = _can(self.request.user, ACCESSIBILITY_AUDIT)
        context["can_complete"] = _can(self.request.user, ACCESSIBILITY_AUDIT)
        context["finding_form"] = AccessibilityFindingForm(initial={"audit": audit})
        return context


class AuditCompleteView(AccessibilityPermissionMixin, View):
    permission_required = ACCESSIBILITY_AUDIT

    def post(self, request, pk, *args, **kwargs):
        audit = get_object_or_404(AccessibilityAudit, pk=pk)
        try:
            AccessibilityAuditService(user=request.user).complete_audit(
                audit,
                summary=request.POST.get("summary", ""),
                recommendations=request.POST.get("recommendations", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
            return redirect("accessibility:audit_detail", pk=pk)
        messages.success(request, "Audit completed.")
        return redirect("accessibility:audit_detail", pk=pk)


class FindingCreateView(AccessibilityPermissionMixin, FormView):
    template_name = "accessibility/finding_form.html"
    form_class = AccessibilityFindingForm
    permission_required = ACCESSIBILITY_AUDIT

    def dispatch(self, request, *args, **kwargs):
        self.audit = get_object_or_404(AccessibilityAudit, pk=kwargs["audit_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {"audit": self.audit}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["audit"] = self.audit
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AccessibilityAuditService(user=self.request.user).add_finding(
                self.audit,
                criterion=data["criterion"],
                component=data["component"],
                page_url=data.get("page_url", ""),
                description=data["description"],
                severity=data.get("severity", "MEDIUM"),
                assigned_to=data.get("assigned_to"),
                code_snippet=data.get("code_snippet", ""),
                recommended_fix=data.get("recommended_fix", ""),
                wcag_technique_ref=data.get("wcag_technique_ref", ""),
                due_date=data.get("due_date"),
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Finding added.")
        return redirect("accessibility:audit_detail", pk=self.audit.pk)


# ──────────────────────────────────────────────────────────────────────────────
# Issue Views
# ──────────────────────────────────────────────────────────────────────────────

class IssueListView(AccessibilityPermissionMixin, ListView):
    model = AccessibilityIssue
    template_name = "accessibility/issue_list.html"
    context_object_name = "issues"
    paginate_by = 20
    permission_required = ACCESSIBILITY_VIEW

    def get_queryset(self):
        qs = super().get_queryset().select_related("reporter", "assigned_to", "criterion")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        severity = self.request.GET.get("severity", "").strip()
        module = self.request.GET.get("module", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(reference_number__icontains=q) | Q(module__icontains=q))
        if status:
            qs = qs.filter(status=status)
        if severity:
            qs = qs.filter(severity=severity)
        if module:
            qs = qs.filter(module=module)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = AccessibilityIssue._meta.get_field("status").choices
        context["severity_choices"] = AccessibilityIssue._meta.get_field("severity").choices
        return context


class IssueCreateView(AccessibilityPermissionMixin, FormView):
    template_name = "accessibility/issue_form.html"
    form_class = AccessibilityIssueForm
    permission_required = ACCESSIBILITY_CREATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Accessibility Issue"
        context["is_update"] = False
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AccessibilityIssueService(user=self.request.user).create_issue(
                title=data["title"],
                source=data["source"],
                module=data["module"],
                component=data["component"],
                page_url=data.get("page_url", ""),
                description=data["description"],
                severity=data.get("severity", "MEDIUM"),
                reporter=data.get("reporter"),
                assigned_to=data.get("assigned_to"),
                steps_to_reproduce=data.get("steps_to_reproduce", ""),
                expected_behavior=data.get("expected_behavior", ""),
                actual_behavior=data.get("actual_behavior", ""),
                criterion=data.get("criterion"),
                status=data.get("status", "OPEN"),
                due_date=data.get("due_date"),
                resolution_notes=data.get("resolution_notes", ""),
                is_regression=data.get("is_regression", False),
                regression_from=data.get("regression_from"),
                tags=data.get("tags", []),
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Accessibility issue reported.")
        return redirect("accessibility:issue_list")


class IssueDetailView(AccessibilityPermissionMixin, DetailView):
    model = AccessibilityIssue
    template_name = "accessibility/issue_detail.html"
    context_object_name = "issue"
    permission_required = ACCESSIBILITY_VIEW


class IssueResolveView(AccessibilityPermissionMixin, View):
    permission_required = ACCESSIBILITY_UPDATE

    def post(self, request, pk, *args, **kwargs):
        issue = get_object_or_404(AccessibilityIssue, pk=pk)
        verified = request.POST.get("verified") == "true"
        try:
            AccessibilityIssueService(user=request.user).resolve_issue(
                issue, resolution_notes=request.POST.get("resolution_notes", ""), verified=verified
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
            return redirect("accessibility:issue_detail", pk=pk)
        messages.success(request, "Issue resolved.")
        return redirect("accessibility:issue_detail", pk=pk)


# ──────────────────────────────────────────────────────────────────────────────
# Recommendation Views
# ──────────────────────────────────────────────────────────────────────────────

class RecommendationListView(AccessibilityPermissionMixin, ListView):
    model = AccessibilityRecommendation
    template_name = "accessibility/recommendation_list.html"
    context_object_name = "recommendations"
    paginate_by = 20
    permission_required = ACCESSIBILITY_VIEW

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related("related_criteria")
        q = self.request.GET.get("q", "").strip()
        priority = self.request.GET.get("priority", "").strip()
        status = self.request.GET.get("status", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if priority:
            qs = qs.filter(priority=priority)
        if status:
            qs = qs.filter(status=status)
        return qs


class RecommendationCreateView(AccessibilityPermissionMixin, FormView):
    template_name = "accessibility/recommendation_form.html"
    form_class = AccessibilityRecommendationForm
    permission_required = ACCESSIBILITY_CREATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Accessibility Recommendation"
        context["is_update"] = False
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AccessibilityRecommendationService(user=self.request.user).create(
                title=data["title"],
                description=data["description"],
                rationale=data.get("rationale", ""),
                priority=data.get("priority", "MEDIUM"),
                related_criteria=data.get("related_criteria"),
                affected_modules=data.get("affected_modules", []),
                estimated_effort=data.get("estimated_effort", ""),
                implementation_notes=data.get("implementation_notes", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Recommendation created.")
        return redirect("accessibility:recommendation_list")


# ──────────────────────────────────────────────────────────────────────────────
# Compliance & Exception Views
# ──────────────────────────────────────────────────────────────────────────────

class ComplianceRecordListView(AccessibilityPermissionMixin, ListView):
    model = AccessibilityComplianceRecord
    template_name = "accessibility/compliance_list.html"
    context_object_name = "records"
    paginate_by = 20
    permission_required = ACCESSIBILITY_VIEW

    def get_queryset(self):
        qs = super().get_queryset().select_related("standard", "last_audit")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        if q:
            qs = qs.filter(Q(module__icontains=q) | Q(component__icontains=q))
        if status:
            qs = qs.filter(compliance_status=status)
        return qs


class ComplianceRecordDetailView(AccessibilityPermissionMixin, DetailView):
    model = AccessibilityComplianceRecord
    template_name = "accessibility/compliance_detail.html"
    context_object_name = "record"
    permission_required = ACCESSIBILITY_VIEW


class ExceptionCreateView(AccessibilityPermissionMixin, FormView):
    template_name = "accessibility/exception_form.html"
    form_class = AccessibilityExceptionForm
    permission_required = ACCESSIBILITY_APPROVE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Accessibility Exception"
        context["is_update"] = False
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AccessibilityExceptionService(user=self.request.user).create(
                module=data["module"],
                component=data.get("component", ""),
                criterion=data["criterion"],
                reason=data["reason"],
                justification=data["justification"],
                alternative_provided=data.get("alternative_provided", ""),
                approved_by=data["approved_by"],
                expires_on=data["expires_on"],
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Exception granted.")
        return redirect("accessibility:compliance_list")


# ──────────────────────────────────────────────────────────────────────────────
# Analytics & Reports
# ──────────────────────────────────────────────────────────────────────────────

class AnalyticsView(AccessibilityPermissionMixin, TemplateView):
    template_name = "accessibility/analytics.html"
    permission_required = ACCESSIBILITY_REPORT

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = self.request.GET.get("module", "")
        analytics = AccessibilityAnalyticsService(user=self.request.user).generate_snapshot(module)
        context["analytics"] = analytics
        context["module"] = module
        context["history"] = AccessibilityAnalytics.objects.filter(module=module).order_by("-snapshot_date")[:12]
        return context


class TimelineView(AccessibilityPermissionMixin, ListView):
    model = AccessibilityTimeline
    template_name = "accessibility/timeline.html"
    context_object_name = "events"
    paginate_by = 50
    permission_required = ACCESSIBILITY_VIEW

    def get_queryset(self):
        qs = super().get_queryset().select_related("performed_by")
        event_type = self.request.GET.get("event_type", "").strip()
        module = self.request.GET.get("module", "").strip()
        if event_type:
            qs = qs.filter(event_type=event_type)
        if module:
            qs = qs.filter(module=module)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event_type_choices"] = AccessibilityTimeline.EVENT_TYPES
        return context


# ──────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ──────────────────────────────────────────────────────────────────────────────

class UserPreferencesAPIView(View):
    """API endpoint to get/set user accessibility preferences."""

    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        prefs = AccessibilityPreferenceService().get_or_create_for_user(request.user)
        return JsonResponse({
            "font_size": prefs.font_size,
            "custom_font_size_px": prefs.custom_font_size_px,
            "colour_theme": prefs.colour_theme,
            "high_contrast": prefs.high_contrast,
            "reduced_motion": prefs.reduced_motion,
            "enhanced_focus": prefs.enhanced_focus,
            "keyboard_navigation_enhanced": prefs.keyboard_navigation_enhanced,
            "screen_reader_optimized": prefs.screen_reader_optimized,
            "notification_timing": prefs.notification_timing,
            "preferred_language": prefs.preferred_language,
            "reading_line_height": float(prefs.reading_line_height),
            "reading_letter_spacing": float(prefs.reading_letter_spacing),
            "reading_word_spacing": float(prefs.reading_word_spacing),
        })

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        try:
            data = json.loads(request.body)
            AccessibilityPreferenceService(user=request.user).update_preferences(request.user, **data)
            return JsonResponse({"status": "ok"})
        except Exception as exc:
            return JsonResponse({"error": str(exc)}, status=400)


class ContrastCheckAPIView(View):
    """API endpoint to check color contrast ratio."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            fg = data.get("foreground", "#000000")
            bg = data.get("background", "#FFFFFF")
            ratio = self._calculate_contrast(fg, bg)
            return JsonResponse({
                "ratio": round(ratio, 2),
                "passes_aa_normal": ratio >= 4.5,
                "passes_aa_large": ratio >= 3.0,
                "passes_aaa_normal": ratio >= 7.0,
                "passes_aaa_large": ratio >= 4.5,
            })
        except Exception as exc:
            return JsonResponse({"error": str(exc)}, status=400)

    def _calculate_contrast(self, fg: str, bg: str) -> float:
        def luminance(hex_color: str) -> float:
            hex_color = hex_color.lstrip("#")
            rgb = tuple(int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))
            def adjust(c):
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            r, g, b = map(adjust, rgb)
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        l1 = luminance(fg)
        l2 = luminance(bg)
        return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
