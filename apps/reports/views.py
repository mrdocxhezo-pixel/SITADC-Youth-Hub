"""Views for the Phase 19 Dynamic Report Builder module.

All views are permission checked (``report_templates.*`` codes with a
``report_templates.manage`` override) and read through the fail-closed
selectors so that unauthorized actors can neither see nor modify report
templates, categories, versions or settings.
"""

from __future__ import annotations

import logging
import re

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView

from apps.rbac.authorization import user_has_permission

from .constants import ReportTemplateStatus
from .exceptions import DynamicTemplateError
from .forms import (
    ReportCategoryForm,
    ReportTemplateForm,
    ReportTemplateSettingsForm,
    SchemaEditorForm,
    TemplateCloneForm,
    TemplateImportForm,
    TemplatePublishForm,
    VersionRestoreForm,
)
from .models import ReportCategory, ReportTemplateSettings
from .permissions import (
    REPORT_TEMPLATE_ARCHIVE,
    REPORT_TEMPLATE_CLONE,
    REPORT_TEMPLATE_CONFIGURE,
    REPORT_TEMPLATE_CREATE,
    REPORT_TEMPLATE_DELETE,
    REPORT_TEMPLATE_EXPORT,
    REPORT_TEMPLATE_IMPORT,
    REPORT_TEMPLATE_MANAGE,
    REPORT_TEMPLATE_PREVIEW,
    REPORT_TEMPLATE_PUBLISH,
    REPORT_TEMPLATE_RESTORE,
    REPORT_TEMPLATE_UPDATE,
    REPORT_TEMPLATE_VIEW,
)
from apps.report_instances.permissions import can_create_report
from .selectors import category_queryset, template_queryset, visible_audit_records
from .services import (
    ReportBuilderSettingsService,
    ReportCategoryService,
    ReportTemplateService,
    TemplateCloneService,
    TemplateComparisonService,
    TemplateImportService,
    TemplatePreviewService,
    TemplatePublicationService,
    TemplateSchemaService,
    TemplateVersionService,
)

logger = logging.getLogger(__name__)


def _can(user, *permission_codes: str) -> bool:
    return bool(
        user_has_permission(user, REPORT_TEMPLATE_MANAGE)
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


def _scoped_template(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        template_queryset(user, include_archived=include_archived), pk=pk
    )


def _status_summary(queryset, status_field: str = "status"):
    return list(
        queryset.values(status_field).annotate(total=Count("id")).order_by(status_field)
    )


class ReportPermissionMixin(PermissionRequiredMixin):
    """Allow any listed report builder permission, with module-manager override.

    The ``report_templates.*`` codes are stored as literal permission
    codenames, so the inherited ``has_perm()`` lookup (``<app>.<codename>``)
    can never match.  ``has_permission()`` is therefore overridden to resolve
    the codes through ``user_has_permission`` instead.
    """

    request: HttpRequest

    def has_permission(self) -> bool:
        required = self.permission_required
        permissions = (required,) if isinstance(required, str) else tuple(required)
        return _can(self.request.user, *permissions)


# ── Dashboard ────────────────────────────────────────────────────────────


class ReportBuilderDashboardView(ReportPermissionMixin, TemplateView):
    template_name = "reports/dashboard.html"
    permission_required = REPORT_TEMPLATE_MANAGE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        templates = template_queryset(user)
        context.update(
            {
                "metrics": {
                    "templates": templates.count(),
                    "drafts": templates.filter(
                        status=ReportTemplateStatus.DRAFT
                    ).count(),
                    "published": templates.filter(
                        status=ReportTemplateStatus.PUBLISHED
                    ).count(),
                    "archived": templates.filter(
                        status=ReportTemplateStatus.ARCHIVED
                    ).count(),
                },
                "template_status_summary": _status_summary(templates),
                "categories": category_queryset(user)
                .annotate(template_count=Count("templates"))
                .order_by("code"),
                "recent_activity": visible_audit_records(user, limit=10),
                "can_create": _can(user, REPORT_TEMPLATE_CREATE),
                "can_configure": _can(user, REPORT_TEMPLATE_CONFIGURE),
            }
        )
        return context


# ── Template directory & CRUD ────────────────────────────────────────────


class TemplateDirectoryView(ReportPermissionMixin, ListView):
    template_name = "reports/template_list.html"
    paginate_by = 20
    permission_required = REPORT_TEMPLATE_VIEW

    def get_queryset(self):
        qs = template_queryset(self.request.user).select_related("category")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(reference_number__icontains=q)
                | Q(code__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["records"] = context["object_list"]
        context["entity_label"] = "Report template"
        context["detail_url_name"] = "reports:template_detail"
        context["create_url_name"] = "reports:template_create"
        context["status_choices"] = ReportTemplateStatus.choices
        context["can_create"] = _can(self.request.user, REPORT_TEMPLATE_CREATE)
        return context


class TemplateCreateView(ReportPermissionMixin, FormView):
    template_name = "reports/template_form.html"
    form_class = ReportTemplateForm
    permission_required = REPORT_TEMPLATE_CREATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Report template"
        context["is_update"] = False
        context["cancel_url"] = redirect("reports:template_list").url
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            template = ReportTemplateService(user=self.request.user).create(
                code=data["code"],
                title=data["title"],
                category=data["category"],
                reporting_frequency=data["reporting_frequency"],
                description=data.get("description", ""),
                department=data.get("department", ""),
                owner=data.get("owner"),
                confidentiality=data.get("confidentiality"),
                effective_from=data.get("effective_from"),
                expires_on=data.get("expires_on"),
                retention_period_days=data.get("retention_period_days", 365),
                notes=data.get("notes", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Report template created successfully.")
        return redirect("reports:template_detail", pk=template.pk)


class TemplateUpdateView(ReportPermissionMixin, FormView):
    template_name = "reports/template_form.html"
    form_class = ReportTemplateForm
    permission_required = REPORT_TEMPLATE_UPDATE

    def dispatch(self, request, *args, **kwargs):
        self.template = _scoped_template(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        template = self.template
        return {
            "code": template.code,
            "title": template.title,
            "category": template.category_id,
            "reporting_frequency": template.reporting_frequency,
            "description": template.description,
            "department": template.department,
            "owner": template.owner_id,
            "confidentiality": template.confidentiality,
            "effective_from": template.effective_from,
            "expires_on": template.expires_on,
            "retention_period_days": template.retention_period_days,
            "notes": template.notes,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Report template"
        context["is_update"] = True
        context["object"] = self.template
        context["cancel_url"] = redirect(
            "reports:template_detail", pk=self.template.pk
        ).url
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            template = ReportTemplateService(user=self.request.user).update(
                self.template,
                title=data.get("title"),
                category=data.get("category"),
                reporting_frequency=data.get("reporting_frequency"),
                description=data.get("description"),
                department=data.get("department"),
                owner=data.get("owner"),
                confidentiality=data.get("confidentiality"),
                effective_from=data.get("effective_from"),
                expires_on=data.get("expires_on"),
                retention_period_days=data.get("retention_period_days"),
                notes=data.get("notes"),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Report template updated successfully.")
        return redirect("reports:template_detail", pk=template.pk)


class TemplateDetailView(ReportPermissionMixin, DetailView):
    template_name = "reports/template_detail.html"
    permission_required = REPORT_TEMPLATE_VIEW

    def get_queryset(self):
        return template_queryset(
            self.request.user, include_archived=True
        ).select_related("category", "current_version")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template = self.object
        user = self.request.user
        context["can_edit"] = _can(user, REPORT_TEMPLATE_UPDATE)
        context["can_publish"] = _can(user, REPORT_TEMPLATE_PUBLISH)
        context["can_archive"] = _can(user, REPORT_TEMPLATE_ARCHIVE)
        context["can_restore"] = _can(user, REPORT_TEMPLATE_RESTORE)
        context["can_delete"] = _can(user, REPORT_TEMPLATE_DELETE)
        context["can_preview"] = _can(user, REPORT_TEMPLATE_PREVIEW)
        context["can_clone"] = _can(user, REPORT_TEMPLATE_CLONE)
        context["can_export"] = _can(user, REPORT_TEMPLATE_EXPORT)
        context["can_import"] = _can(user, REPORT_TEMPLATE_IMPORT)
        context["can_configure"] = _can(user, REPORT_TEMPLATE_CONFIGURE)
        context["can_create_report"] = can_create_report(user)
        context["sections"] = template.sections.filter(parent__isnull=True).order_by(
            "sort_order", "name"
        )
        context["versions"] = template.versions.order_by("-major", "-minor")
        context["history"] = template.status_history.all()
        return context


# ── Schema designer ──────────────────────────────────────────────────────


class SchemaDesignerView(ReportPermissionMixin, FormView):
    template_name = "reports/schema_editor.html"
    form_class = SchemaEditorForm
    permission_required = REPORT_TEMPLATE_UPDATE

    def dispatch(self, request, *args, **kwargs):
        self.template = _scoped_template(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        schema = TemplateSchemaService(user=self.request.user).build_schema(
            self.template
        )
        return {"schema": _json_dumps(schema)}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.template
        context["current_schema"] = _json_dumps(
            TemplateSchemaService(user=self.request.user).build_schema(self.template)
        )
        return context

    def form_valid(self, form):
        schema = form.cleaned_data["schema"]
        try:
            working = TemplateSchemaService(user=self.request.user).save_schema(
                self.template, schema
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        except DynamicTemplateError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Schema saved on version {working.version_number}.",
        )
        return redirect("reports:template_detail", pk=self.template.pk)


def _json_dumps(value) -> str:
    import json

    return json.dumps(value, indent=2, default=str)


# ── Preview ──────────────────────────────────────────────────────────────


class TemplatePreviewView(ReportPermissionMixin, TemplateView):
    template_name = "reports/template_preview.html"
    permission_required = REPORT_TEMPLATE_PREVIEW

    def dispatch(self, request, *args, **kwargs):
        self.template = _scoped_template(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        preview = TemplatePreviewService(user=self.request.user).build_preview(
            self.template
        )
        context["object"] = self.template
        context["can_create_report"] = can_create_report(self.request.user)
        context.update(preview)
        return context


# ── Publish / unpublish ──────────────────────────────────────────────────


class TemplatePublishView(ReportPermissionMixin, FormView):
    template_name = "reports/template_publish.html"
    form_class = TemplatePublishForm
    permission_required = REPORT_TEMPLATE_PUBLISH

    def dispatch(self, request, *args, **kwargs):
        self.template = _scoped_template(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = TemplatePublicationService(user=self.request.user)
        context["object"] = self.template
        context["blockers"] = service.validate_ready(self.template)
        return context

    def form_valid(self, form):
        try:
            version = TemplatePublicationService(user=self.request.user).publish(
                self.template, notes=form.cleaned_data["notes"]
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(
            self.request, f"Template published as version {version.version_number}."
        )
        return redirect("reports:template_detail", pk=self.template.pk)


class TemplateUnpublishView(ReportPermissionMixin, View):
    permission_required = REPORT_TEMPLATE_PUBLISH

    def post(self, request, pk, *args, **kwargs):
        template = _scoped_template(request.user, pk)
        try:
            TemplatePublicationService(user=request.user).unpublish(template)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return redirect("reports:template_detail", pk=pk)
        messages.success(self.request, "Template unpublished and returned to draft.")
        return redirect("reports:template_detail", pk=pk)


# ── Archive / restore / delete ───────────────────────────────────────────


class TemplateArchiveView(ReportPermissionMixin, View):
    permission_required = REPORT_TEMPLATE_ARCHIVE

    def post(self, request, pk, *args, **kwargs):
        template = _scoped_template(request.user, pk)
        try:
            ReportTemplateService(user=request.user).archive(template)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
        else:
            messages.success(self.request, "Template archived.")
        return redirect("reports:template_detail", pk=pk)


class TemplateRestoreView(ReportPermissionMixin, View):
    permission_required = REPORT_TEMPLATE_RESTORE

    def post(self, request, pk, *args, **kwargs):
        template = _scoped_template(request.user, pk, include_archived=True)
        try:
            ReportTemplateService(user=request.user).restore(template)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
        else:
            messages.success(self.request, "Template restored to draft.")
        return redirect("reports:template_detail", pk=pk)


class TemplateDeleteView(ReportPermissionMixin, View):
    permission_required = REPORT_TEMPLATE_DELETE

    def post(self, request, pk, *args, **kwargs):
        template = _scoped_template(request.user, pk)
        try:
            ReportTemplateService(user=request.user).soft_delete(template)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
            return redirect("reports:template_detail", pk=pk)
        messages.success(self.request, "Draft template deleted.")
        return redirect("reports:template_list")


# ── Clone / import / export ──────────────────────────────────────────────


class TemplateCloneView(ReportPermissionMixin, FormView):
    template_name = "reports/template_clone.html"
    form_class = TemplateCloneForm
    permission_required = REPORT_TEMPLATE_CLONE

    def dispatch(self, request, *args, **kwargs):
        self.template = _scoped_template(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {
            "new_code": f"{self.template.code}_copy",
            "new_title": f"{self.template.title} (copy)",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.template
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            clone = TemplateCloneService(user=self.request.user).clone(
                self.template,
                new_code=data["new_code"],
                new_title=data["new_title"] or data["new_code"],
                notes=data.get("notes", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, f"Template cloned as {clone.reference_number}.")
        return redirect("reports:template_detail", pk=clone.pk)


class TemplateImportView(ReportPermissionMixin, FormView):
    template_name = "reports/template_import.html"
    form_class = TemplateImportForm
    permission_required = REPORT_TEMPLATE_IMPORT

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create"] = _can(self.request.user, REPORT_TEMPLATE_CREATE)
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            template = TemplateImportService(user=self.request.user).import_json(
                data["payload"],
                category=data["category"],
                code=data.get("code"),
                title=data.get("title"),
                notes="Imported from JSON payload.",
                dry_run=data.get("dry_run", False),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        if data.get("dry_run"):
            messages.success(self.request, "Payload validated successfully (dry run).")
            return redirect("reports:template_import")
        messages.success(
            self.request, f"Template imported as {template.reference_number}."
        )
        return redirect("reports:template_detail", pk=template.pk)


class TemplateExportView(ReportPermissionMixin, View):
    permission_required = REPORT_TEMPLATE_EXPORT

    def get(self, request, pk, *args, **kwargs):
        template = _scoped_template(request.user, pk)
        payload = TemplateSchemaService(user=request.user).export_json(template)
        filename = f"{template.code}.json"
        response = JsonResponse(payload, safe=False)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


# ── Versions ─────────────────────────────────────────────────────────────


class TemplateVersionListView(ReportPermissionMixin, DetailView):
    template_name = "reports/template_versions.html"
    permission_required = REPORT_TEMPLATE_VIEW

    def get_queryset(self):
        return template_queryset(self.request.user, include_archived=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template = self.object
        context["versions"] = template.versions.select_related("published_by").order_by(
            "-major", "-minor"
        )
        context["can_restore"] = _can(self.request.user, REPORT_TEMPLATE_RESTORE)
        context["can_compare"] = _can(self.request.user, REPORT_TEMPLATE_VIEW)
        return context


class TemplateVersionRestoreView(ReportPermissionMixin, FormView):
    template_name = "reports/template_version_restore.html"
    form_class = VersionRestoreForm
    permission_required = REPORT_TEMPLATE_UPDATE

    def dispatch(self, request, *args, **kwargs):
        self.template = _scoped_template(request.user, kwargs["pk"])
        self.version = get_object_or_404(
            self.template.versions, pk=kwargs["version_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.template
        context["version"] = self.version
        return context

    def form_valid(self, form):
        try:
            restored = TemplateVersionService(user=self.request.user).restore_version(
                self.template,
                self.version,
                change_summary=form.cleaned_data["change_summary"],
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(
            self.request, f"Restored as version {restored.version_number}."
        )
        return redirect("reports:template_version_list", pk=self.template.pk)


class TemplateVersionCompareView(ReportPermissionMixin, TemplateView):
    template_name = "reports/template_version_compare.html"
    permission_required = REPORT_TEMPLATE_VIEW

    def dispatch(self, request, *args, **kwargs):
        self.template = _scoped_template(request.user, kwargs["pk"])
        self.left = get_object_or_404(self.template.versions, pk=kwargs["left_pk"])
        self.right = get_object_or_404(self.template.versions, pk=kwargs["right_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comparison = TemplateComparisonService(user=self.request.user).compare_versions(
            self.left, self.right
        )
        context["object"] = self.template
        context["left"] = self.left
        context["right"] = self.right
        context.update(comparison)
        return context


# ── Categories ───────────────────────────────────────────────────────────


class CategoryDirectoryView(ReportPermissionMixin, ListView):
    template_name = "reports/category_list.html"
    paginate_by = 20
    permission_required = REPORT_TEMPLATE_VIEW

    def get_queryset(self):
        qs = category_queryset(self.request.user, include_inactive=False).annotate(
            template_count=Count("templates")
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["records"] = context["object_list"]
        context["entity_label"] = "Report category"
        context["can_configure"] = _can(self.request.user, REPORT_TEMPLATE_CONFIGURE)
        return context


class CategoryCreateView(ReportPermissionMixin, FormView):
    template_name = "reports/category_form.html"
    form_class = ReportCategoryForm
    permission_required = REPORT_TEMPLATE_CONFIGURE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        context["cancel_url"] = redirect("reports:category_list").url
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            ReportCategoryService(user=self.request.user).create(
                code=data["code"],
                name=data["name"],
                description=data.get("description", ""),
                color=data.get("color", ""),
                icon=data.get("icon", ""),
                sort_order=data.get("sort_order", 0),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Report category created.")
        return redirect("reports:category_list")


class CategoryUpdateView(ReportPermissionMixin, FormView):
    template_name = "reports/category_form.html"
    form_class = ReportCategoryForm
    permission_required = REPORT_TEMPLATE_CONFIGURE

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(ReportCategory.all_objects, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {
            "code": self.category.code,
            "name": self.category.name,
            "description": self.category.description,
            "color": self.category.color,
            "icon": self.category.icon,
            "sort_order": self.category.sort_order,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True
        context["object"] = self.category
        context["cancel_url"] = redirect("reports:category_list").url
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            ReportCategoryService(user=self.request.user).update(
                self.category,
                code=data.get("code"),
                name=data.get("name"),
                description=data.get("description"),
                color=data.get("color"),
                icon=data.get("icon"),
                sort_order=data.get("sort_order"),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Report category updated.")
        return redirect("reports:category_list")


class CategoryToggleView(ReportPermissionMixin, View):
    permission_required = REPORT_TEMPLATE_CONFIGURE

    def post(self, request, pk, *args, **kwargs):
        category = get_object_or_404(ReportCategory.all_objects, pk=pk)
        try:
            ReportCategoryService(user=request.user).set_active(
                category, not category.is_active
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(self.request, str(exc))
        return redirect("reports:category_list")


# ── Settings ─────────────────────────────────────────────────────────────


class ReportBuilderSettingsView(ReportPermissionMixin, FormView):
    template_name = "reports/settings.html"
    form_class = ReportTemplateSettingsForm
    permission_required = REPORT_TEMPLATE_CONFIGURE

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        settings = ReportTemplateSettings.load()
        for field in form.fields:
            if field in ("default_page_layout", "default_export_settings"):
                form.initial.setdefault(
                    field, _json_dumps(getattr(settings, field) or {})
                )
            elif field in form.fields:
                form.initial.setdefault(field, getattr(settings, field))
        return form

    def form_valid(self, form):
        data = form.cleaned_data
        for field in ("default_page_layout", "default_export_settings"):
            raw = data.get(field)
            data[field] = _parse_json(raw) if isinstance(raw, str) else raw
        try:
            ReportBuilderSettingsService(user=self.request.user).update(**data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Report builder settings updated.")
        return redirect("reports:settings")


def _parse_json(raw):
    import json

    if not raw:
        return {}
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


# ── Category Browse / Template Selection ─────────────────────────────────


def _natural_sort_key(code: str):
    """Return a sort key that handles A1, A2, ..., A10 correctly."""
    parts = re.split(r"(\d+)", code)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def _sort_templates_naturally(queryset):
    """Sort a template queryset by code in natural order (A1, A2, ..., A10)."""
    return sorted(queryset, key=lambda t: _natural_sort_key(t.code))


class CategoryBrowseView(ReportPermissionMixin, TemplateView):
    """Dashboard-style view showing all 16 categories (A-P) with their templates."""

    template_name = "reports/category_browse.html"
    permission_required = REPORT_TEMPLATE_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        search = self.request.GET.get("q", "").strip()

        categories = (
            category_queryset(user, include_inactive=False)
            .annotate(template_count=Count("templates"))
            .order_by("code")
        )

        cat_data = []
        for cat in categories:
            templates_qs = template_queryset(user).filter(category=cat)
            if search:
                templates_qs = templates_qs.filter(
                    Q(title__icontains=search) | Q(code__icontains=search)
                )
            templates = _sort_templates_naturally(templates_qs)
            cat_data.append(
                {
                    "category": cat,
                    "templates": templates,
                    "template_count": len(templates),
                }
            )

        context["categories"] = cat_data
        context["search_query"] = search
        context["total_templates"] = sum(c["template_count"] for c in cat_data)
        return context


class CategoryTemplateListView(ReportPermissionMixin, ListView):
    """List all templates in a specific category."""

    template_name = "reports/category_template_list.html"
    paginate_by = 20
    permission_required = REPORT_TEMPLATE_VIEW

    def get_queryset(self):
        self.category = get_object_or_404(
            ReportCategory.objects.filter(is_active=True),
            pk=self.kwargs["pk"],
        )
        qs = template_queryset(self.request.user).filter(category=self.category)
        return qs.order_by("code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        context["search_query"] = self.request.GET.get("q", "")
        context["template_count"] = self.get_queryset().count()
        return context
