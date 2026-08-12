"""Views for the Organizational Registers module.

All views are permission checked server side; confidentiality scoping is
applied through the fail-closed selectors.
"""

from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, FormView, ListView, TemplateView, View
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.detail import SingleObjectMixin

from .constants import RegisterStatus
from .forms import (
    RegisterAttachmentForm,
    RegisterCategoryForm,
    RegisterEntryForm,
    RegisterEntryTransitionForm,
    RegisterForm,
    RegisterSearchForm,
    RegisterTemplateForm,
)
from .models import RegisterActivity
from .permissions import (
    REGISTER_ARCHIVE,
    REGISTER_CREATE,
    REGISTER_EXPORT,
    REGISTER_MANAGE,
    REGISTER_RESTORE,
    REGISTER_UPDATE,
    REGISTER_VIEW,
    user_can_act_on_entries,
    user_can_export,
    user_can_manage_registers,
)
from .selectors import (
    category_queryset,
    entry_queryset,
    register_queryset,
    template_queryset,
    visible_entries,
    visible_registers,
)
from .services import (
    RegisterCategoryService,
    RegisterEntryService,
    RegisterService,
    RegisterTemplateService,
)

logger = logging.getLogger(__name__)


def _can(user, *permission_codes: str) -> bool:
    from apps.rbac.authorization import user_has_permission

    return bool(
        user_has_permission(user, REGISTER_MANAGE)
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


def _scoped_register(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        register_queryset(user, include_archived=include_archived), pk=pk
    )


def _scoped_visible_register(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        visible_registers(user, include_archived=include_archived), pk=pk
    )


def _scoped_entry(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        entry_queryset(user, include_archived=include_archived), pk=pk
    )


def _scoped_visible_entry(user, pk, *, include_archived: bool = False):
    return get_object_or_404(
        visible_entries(user, include_archived=include_archived), pk=pk
    )


class RegisterPermissionMixin(PermissionRequiredMixin):
    """Allow any listed registers permission with a module-manager override."""

    request: HttpRequest

    def has_permission(self) -> bool:
        required = self.permission_required
        permissions = (required,) if isinstance(required, str) else tuple(required)
        return _can(self.request.user, *permissions)


# ── Dashboard ────────────────────────────────────────────────────────────


class RegisterDashboardView(RegisterPermissionMixin, TemplateView):
    template_name = "registers/dashboard.html"
    permission_required = REGISTER_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        registers = visible_registers(user)
        entries = visible_entries(user)
        categories = category_queryset(user)
        context.update(
            {
                "total_registers": registers.count(),
                "active_registers": registers.filter(
                    status=RegisterStatus.ACTIVE
                ).count(),
                "total_entries": entries.count(),
                "active_entries": entries.filter(is_archived=False).count(),
                "pending_reviews": entries.filter(
                    approval_status__in=[
                        "SUBMITTED",
                        "PENDING_REVIEW",
                        "UNDER_REVIEW",
                    ]
                ).count(),
                "archived_entries": entries.filter(is_archived=True).count(),
                "confidential_entries": entries.filter(
                    confidentiality__in=[
                        "RESTRICTED",
                        "CONFIDENTIAL",
                        "HIGHLY_CONFIDENTIAL",
                    ]
                ).count(),
                "category_distribution": categories.annotate(
                    register_count=Count("registers")
                ).order_by("-register_count")[:8],
                "entry_distribution": (
                    entries.values("register__category__name")
                    .annotate(total=Count("id"))
                    .order_by("-total")[:8]
                ),
                "recent_entries": entries.select_related("register", "owner")[:10],
                "recent_activity": RegisterActivity.objects.filter(
                    Q(entry__isnull=False, entry__in=entries)
                    | Q(entry__isnull=True, register__in=registers)
                ).select_related("entry", "register", "actor")[:12],
                "can_create": _can(user, REGISTER_CREATE),
                "can_export": user_can_export(user),
            }
        )
        return context


# ── Register categories ──────────────────────────────────────────────────


class RegisterCategoryListView(RegisterPermissionMixin, ListView):
    template_name = "registers/category_directory.html"
    context_object_name = "categories"
    permission_required = REGISTER_VIEW
    paginate_by = 25

    def get_queryset(self):
        return (
            category_queryset(self.request.user)
            .select_related()
            .order_by("sort_order", "name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage"] = user_can_manage_registers(self.request.user)
        return context


class RegisterCategoryCreateView(RegisterPermissionMixin, FormView):
    template_name = "registers/category_form.html"
    permission_required = REGISTER_CREATE
    form_class = RegisterCategoryForm

    def form_valid(self, form):
        try:
            RegisterCategoryService(user=self.request.user).execute(**form.cleaned_data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Register category created."))
        return redirect("registers:category_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        return context


class RegisterCategoryUpdateView(RegisterPermissionMixin, FormView):
    template_name = "registers/category_form.html"
    permission_required = REGISTER_UPDATE
    form_class = RegisterCategoryForm

    def get_object(self):
        return get_object_or_404(
            category_queryset(self.request.user), pk=self.kwargs["pk"]
        )

    def get_initial(self):
        category = self.get_object()
        return {
            "name": category.name,
            "code": category.code,
            "number_prefix": category.number_prefix,
            "description": category.description,
            "default_confidentiality": category.default_confidentiality,
            "retention_policy": category.retention_policy,
            "retention_years": category.retention_years,
            "sort_order": category.sort_order,
            "is_active": category.is_active,
        }

    def form_valid(self, form):
        try:
            RegisterCategoryService(user=self.request.user).execute(
                instance=self.get_object(), **form.cleaned_data
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Register category updated."))
        return redirect("registers:category_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True
        return context


# ── Registers ────────────────────────────────────────────────────────────


class RegisterListView(RegisterPermissionMixin, ListView):
    template_name = "registers/register_directory.html"
    context_object_name = "registers"
    permission_required = REGISTER_VIEW
    paginate_by = 25

    def get_queryset(self):
        queryset = visible_registers(self.request.user).select_related(
            "category", "owner"
        )
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(code__icontains=q))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage"] = user_can_manage_registers(self.request.user)
        context["can_export"] = user_can_export(self.request.user)
        context["status_choices"] = RegisterStatus.choices
        return context


class RegisterDetailView(RegisterPermissionMixin, DetailView):
    template_name = "registers/register_detail.html"
    context_object_name = "register"
    permission_required = REGISTER_VIEW

    def get_queryset(self):
        return register_queryset(self.request.user).select_related("category", "owner")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        register = self.object
        context["entries"] = (
            visible_entries(user)
            .filter(register=register)
            .select_related("owner", "register")
            .order_by("-created_at")[:25]
        )
        context["entry_count"] = visible_entries(user).filter(register=register).count()
        context["activity"] = register.activity.select_related("actor")[:15]
        context["can_manage"] = user_can_manage_registers(user)
        context["can_act"] = user_can_act_on_entries(user)
        context["templates"] = template_queryset(user).filter(
            register=register, is_active=True
        )
        return context


class RegisterCreateView(RegisterPermissionMixin, FormView):
    template_name = "registers/register_form.html"
    permission_required = REGISTER_CREATE
    form_class = RegisterForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            instance = RegisterService(user=self.request.user).execute(
                **form.cleaned_data
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Register created."))
        return redirect("registers:register_detail", pk=instance.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        return context


class RegisterUpdateView(RegisterPermissionMixin, FormView):
    template_name = "registers/register_form.html"
    permission_required = REGISTER_UPDATE
    form_class = RegisterForm

    def get_object(self):
        return _scoped_register(self.request.user, self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        register = self.get_object()
        return {
            "name": register.name,
            "code": register.code,
            "category": register.category_id,
            "description": register.description,
            "owner": register.owner_id,
            "responsible_department": register.responsible_department,
            "numbering_scheme": register.numbering_scheme_id,
            "confidentiality": register.confidentiality,
            "approval_required": register.approval_required,
            "retention_policy": register.retention_policy,
            "retention_years": register.retention_years,
            "status": register.status,
            "is_active": register.is_active,
        }

    def form_valid(self, form):
        try:
            RegisterService(user=self.request.user).execute(
                instance=self.get_object(), **form.cleaned_data
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Register updated."))
        return redirect("registers:register_detail", pk=self.get_object().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True
        return context


class RegisterArchiveView(RegisterPermissionMixin, View):
    permission_required = REGISTER_ARCHIVE

    def post(self, request, pk):
        register = _scoped_register(request.user, pk)
        RegisterService(user=request.user).archive(instance=register)
        messages.success(request, _("Register archived."))
        return redirect("registers:register_list")


class RegisterRestoreView(RegisterPermissionMixin, View):
    permission_required = REGISTER_RESTORE

    def post(self, request, pk):
        register = _scoped_register(request.user, pk, include_archived=True)
        RegisterService(user=request.user).restore(instance=register)
        messages.success(request, _("Register restored."))
        return redirect("registers:register_detail", pk=register.pk)


# ── Templates ────────────────────────────────────────────────────────────


class RegisterTemplateListView(RegisterPermissionMixin, ListView):
    template_name = "registers/template_directory.html"
    context_object_name = "templates"
    permission_required = REGISTER_VIEW
    paginate_by = 25

    def get_queryset(self):
        return template_queryset(self.request.user).select_related("register")


class RegisterTemplateCreateView(RegisterPermissionMixin, FormView):
    template_name = "registers/template_form.html"
    permission_required = REGISTER_CREATE
    form_class = RegisterTemplateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            RegisterTemplateService(user=self.request.user).execute(**form.cleaned_data)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Register template created."))
        return redirect("registers:template_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        return context


class RegisterTemplateUpdateView(RegisterPermissionMixin, FormView):
    template_name = "registers/template_form.html"
    permission_required = REGISTER_UPDATE
    form_class = RegisterTemplateForm

    def get_object(self):
        return get_object_or_404(
            template_queryset(self.request.user), pk=self.kwargs["pk"]
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        template = self.get_object()
        import json as _json

        return {
            "name": template.name,
            "code": template.code,
            "register": template.register_id,
            "description": template.description,
            "fields": _json.dumps(template.fields or [], indent=2),
            "validation_rules": _json.dumps(template.validation_rules or [], indent=2),
            "default_confidentiality": template.default_confidentiality,
            "is_default": template.is_default,
            "is_active": template.is_active,
        }

    def form_valid(self, form):
        try:
            RegisterTemplateService(user=self.request.user).execute(
                instance=self.get_object(), **form.cleaned_data
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Register template updated."))
        return redirect("registers:template_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True
        return context


# ── Entries ──────────────────────────────────────────────────────────────


class EntryListView(RegisterPermissionMixin, ListView):
    template_name = "registers/entry_directory.html"
    context_object_name = "entries"
    permission_required = REGISTER_VIEW
    paginate_by = 25

    def get_queryset(self):
        user = self.request.user
        queryset = visible_entries(user).select_related("register__category", "owner")
        form = RegisterSearchForm(self.request.GET, user=user)
        if form.is_valid():
            queryset = form.apply_filters(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["search_form"] = RegisterSearchForm(self.request.GET, user=user)
        context["can_create"] = _can(user, REGISTER_CREATE)
        context["can_export"] = user_can_export(user)
        return context


class EntryDetailView(RegisterPermissionMixin, DetailView):
    template_name = "registers/entry_detail.html"
    context_object_name = "entry"
    permission_required = REGISTER_VIEW

    def get_queryset(self):
        return visible_entries(self.request.user).select_related(
            "register__category", "owner", "directorate", "program", "project"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        entry = self.object
        context["activity"] = entry.activity.select_related("actor")[:20]
        context["versions"] = entry.versions.select_related("author")[:10]
        context["attachments"] = entry.attachments.all()
        context["relationships"] = entry.relationships.select_related("content_type")[
            :20
        ]
        context["reviews"] = entry.reviews.select_related("reviewer")[:10]
        context["validations"] = entry.validations.order_by("-checked_at")[:20]
        context["can_edit"] = _can(user, REGISTER_UPDATE)
        context["can_act"] = user_can_act_on_entries(user)
        context["can_export"] = user_can_export(user)
        return context


class EntryCreateView(RegisterPermissionMixin, FormView):
    template_name = "registers/entry_form.html"
    permission_required = REGISTER_CREATE
    form_class = RegisterEntryForm

    def get_initial(self):
        initial = super().get_initial()
        register_pk = self.kwargs.get("register_pk")
        if register_pk:
            register = _scoped_register(self.request.user, register_pk)
            initial["register"] = register.pk
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            instance = RegisterEntryService(user=self.request.user).execute(
                **form.cleaned_data
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Register entry created."))
        return redirect("registers:entry_detail", pk=instance.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        return context


class EntryUpdateView(RegisterPermissionMixin, FormView):
    template_name = "registers/entry_form.html"
    permission_required = REGISTER_UPDATE
    form_class = RegisterEntryForm

    def get_object(self):
        return _scoped_visible_entry(self.request.user, self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        import json as _json

        entry = self.get_object()
        return {
            "register": entry.register_id,
            "template": entry.template_id,
            "title": entry.title,
            "description": entry.description,
            "owner": entry.owner_id,
            "directorate": entry.directorate_id,
            "program": entry.program_id,
            "project": entry.project_id,
            "reporting_period_start": entry.reporting_period_start,
            "reporting_period_end": entry.reporting_period_end,
            "confidentiality": entry.confidentiality,
            "field_data": _json.dumps(entry.field_data or {}, indent=2),
            "tags": ", ".join(entry.tags or []),
            "keywords": entry.keywords,
        }

    def form_valid(self, form):
        try:
            instance = RegisterEntryService(user=self.request.user).execute(
                instance=self.get_object(), **form.cleaned_data
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Register entry updated."))
        return redirect("registers:entry_detail", pk=instance.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True
        return context


class _EntryActionView(
    RegisterPermissionMixin, SingleObjectMixin, TemplateResponseMixin, View
):
    """Base view for entry workflow actions."""

    template_name = "registers/entry_action.html"
    context_object_name = "entry"
    form_class = RegisterEntryTransitionForm
    action_name: str = ""
    success_message: str | Promise = ""

    def _perform(self, comment: str) -> None:
        raise NotImplementedError

    def get_queryset(self):
        return visible_entries(self.request.user)

    def get_context_data(self, **kwargs):
        form = kwargs.pop("form", None) or RegisterEntryTransitionForm()
        context = {
            "entry": self.object,
            "form": form,
            "action_name": self.action_name,
        }
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = RegisterEntryTransitionForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        comment = form.cleaned_data.get("comment", "")
        try:
            self._perform(comment)
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.render_to_response(self.get_context_data(form=form))
        messages.success(request, str(self.success_message))
        return redirect("registers:entry_detail", pk=self.object.pk)


class EntrySubmitView(_EntryActionView):
    permission_required = "registers.submit"
    action_name = "Submit for approval"
    success_message = _("Entry submitted for approval.")

    def _perform(self, comment: str):
        RegisterEntryService(user=self.request.user).submit(
            instance=self.object, comment=comment
        )


class EntryStartReviewView(_EntryActionView):
    permission_required = "registers.review"
    action_name = "Start review"
    success_message = _("Entry review started.")

    def _perform(self, comment: str):
        RegisterEntryService(user=self.request.user).start_review(
            instance=self.object, comment=comment
        )


class EntryApproveView(_EntryActionView):
    permission_required = "registers.approve"
    action_name = "Approve"
    success_message = _("Entry approved.")

    def _perform(self, comment: str):
        RegisterEntryService(user=self.request.user).approve(
            instance=self.object, comment=comment
        )


class EntryReturnView(_EntryActionView):
    permission_required = "registers.review"
    action_name = "Return for correction"
    success_message = _("Entry returned for correction.")

    def _perform(self, comment: str):
        RegisterEntryService(user=self.request.user).return_entry(
            instance=self.object, comment=comment
        )


class EntryRejectView(_EntryActionView):
    permission_required = "registers.approve"
    action_name = "Reject"
    success_message = _("Entry rejected.")

    def _perform(self, comment: str):
        RegisterEntryService(user=self.request.user).reject(
            instance=self.object, comment=comment
        )


class EntryArchiveView(RegisterPermissionMixin, View):
    permission_required = "registers.archive"

    def post(self, request, pk):
        entry = _scoped_visible_entry(request.user, pk)
        RegisterEntryService(user=request.user).archive(instance=entry)
        messages.success(request, _("Entry archived."))
        return redirect("registers:entry_detail", pk=entry.pk)


class EntryRestoreView(RegisterPermissionMixin, View):
    permission_required = "registers.restore"

    def post(self, request, pk):
        entry = _scoped_visible_entry(request.user, pk, include_archived=True)
        RegisterEntryService(user=request.user).restore(instance=entry)
        messages.success(request, _("Entry restored."))
        return redirect("registers:entry_detail", pk=entry.pk)


class EntryAttachmentCreateView(RegisterPermissionMixin, FormView):
    template_name = "registers/attachment_form.html"
    permission_required = REGISTER_UPDATE
    form_class = RegisterAttachmentForm

    def get_entry(self):
        return _scoped_visible_entry(self.request.user, self.kwargs["entry_pk"])

    def form_valid(self, form):
        from .services import RegisterAttachmentService

        entry = self.get_entry()
        RegisterAttachmentService(user=self.request.user).add(
            instance=entry,
            file=form.cleaned_data["file"],
            original_filename=form.cleaned_data["file"].name,
            content_type=form.cleaned_data["file"].content_type,
            description=form.cleaned_data.get("description", ""),
        )
        messages.success(self.request, _("Attachment added."))
        return redirect("registers:entry_detail", pk=entry.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entry"] = self.get_entry()
        return context


# ── Exports ──────────────────────────────────────────────────────────────


class RegisterExportView(RegisterPermissionMixin, View):
    permission_required = REGISTER_EXPORT

    def get(self, request, fmt: str = "csv", pk: str | None = None):
        register = None
        if pk:
            register = _scoped_visible_register(request.user, pk)
        from .exports import register_export_response

        return register_export_response(request.user, register=register, fmt=fmt)
