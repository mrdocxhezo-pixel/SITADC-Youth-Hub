"""Views for the Export Engine (Phase 27).

Every request is authorized server-side.  Generation runs synchronously:
validate -> collect (permission-scaled providers) -> render -> store under the
private media tree, then redirect to the history/detail page.
"""

from __future__ import annotations

import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, View

from .exceptions import (
    ExportDownloadDenied,
    ExportError,
    ExportExpiredError,
    ExportNotFoundError,
    ExportPermissionDenied,
)
from .forms import ExportFiltersForm, ExportRequestForm
from .permissions import (
    user_can_create_export,
    user_can_download,
    user_can_manage_exports,
    user_can_view_exports,
)
from .providers import registry
from .selectors import (
    active_export_configuration,
    downloadable_exports,
    export_requests_for_user,
    get_export_request_for_user,
    visible_export_templates,
)
from .services import (
    CancelExportService,
    DownloadExportService,
    GenerateExportService,
    RegenerateExportService,
    RequestExportService,
)

logger = logging.getLogger(__name__)


def _require_view(user) -> None:
    if not user_can_view_exports(user):
        raise PermissionDenied(
            _("You do not have permission to use the Export Engine.")
        )


def _require_create(user) -> None:
    if not user_can_create_export(user):
        raise PermissionDenied(_("You do not have permission to create exports."))


def _require_download(user) -> None:
    if not user_can_download(user):
        raise PermissionDenied(_("You do not have permission to download exports."))


def _provider_choices(user):
    """(source_type, label) pairs for providers the actor may use."""
    available = registry.available(
        user,
        source_types=[
            "REPORT",
            "REGISTER",
            "DIRECTORY",
            "BENEFICIARY",
            "PROGRAM",
            "PROJECT",
            "MEAL",
            "MEETING",
            "DOCUMENT",
        ],
    )
    seen = set()
    choices = []
    for provider in available:
        if provider.source_type in seen:
            continue
        seen.add(provider.source_type)
        choices.append((provider.source_type, str(provider.label)))
    return choices


def _format_choices(user):
    from .constants import DEFAULT_ENABLED_FORMATS

    config = active_export_configuration()
    enabled = config.enabled_formats or list(DEFAULT_ENABLED_FORMATS)
    from .permissions import user_can_use_format

    return [
        (fmt, fmt)
        for fmt in enabled
        if user_can_use_format(user, fmt)
    ]


class ExportHomeView(TemplateView):
    """The Export Engine landing page with a request form."""

    template_name = "exports/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        _require_view(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["request_form"] = ExportRequestForm(
            source_choices=_provider_choices(self.request.user),
            format_choices=_format_choices(self.request.user),
        )
        context["filters_form"] = ExportFiltersForm()
        context["recent_exports"] = export_requests_for_user(self.request.user)[:10]
        context["can_create"] = user_can_create_export(self.request.user)
        context["can_download"] = user_can_download(self.request.user)
        context["can_manage"] = user_can_manage_exports(self.request.user)
        context["config"] = active_export_configuration()
        context["templates"] = visible_export_templates(self.request.user)[:10]
        context["downloadable"] = downloadable_exports(self.request.user)[:10]
        return context


class ExportCreateView(View):
    """Create + synchronously generate an export request."""

    def post(self, request, *args, **kwargs):
        _require_create(request.user)
        form = ExportRequestForm(
            request.POST,
            source_choices=_provider_choices(request.user),
            format_choices=_format_choices(request.user),
        )
        if not form.is_valid():
            messages.error(
                request, _("Please correct the export form and try again.")
            )
            return redirect(reverse("exports:home"))

        source_type = form.cleaned_data["source_type"]
        format_code = form.cleaned_data["format"]
        include_sensitive = form.cleaned_data.get("include_sensitive", False)

        try:
            export_request = RequestExportService(user=request.user).execute(
                source_type=source_type,
                format=format_code,
                requested_by=request.user,
                request_obj=request,
            )
            export_request.is_sensitive = bool(
                include_sensitive
                and export_request.source_type == "BENEFICIARY"
            )
            export_request.save(update_fields=["is_sensitive", "updated_at"])
            generated = GenerateExportService(user=request.user).execute(
                export_request, request_obj=request
            )
        except (ExportError, ValueError) as exc:
            messages.error(request, str(exc))
            return redirect(reverse("exports:home"))

        messages.success(
            request,
            _("Export %(reference)s generated successfully.")
            % {"reference": generated.reference_number},
        )
        return redirect(reverse("exports:detail", kwargs={"pk": generated.pk}))


class ExportHistoryView(TemplateView):
    """The actor's export history (or all history for those permitted)."""

    template_name = "exports/history.html"

    def dispatch(self, request, *args, **kwargs):
        _require_view(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exports"] = export_requests_for_user(self.request.user)
        context["can_manage"] = user_can_manage_exports(self.request.user)
        context["can_view_all"] = (
            self.request.user.is_superuser
            or self.request.user.has_perm("exports.view_all_history")
        )
        context["downloadable"] = downloadable_exports(self.request.user)
        return context


class ExportDetailView(TemplateView):
    """Details and activity timeline for a single export request."""

    template_name = "exports/detail.html"

    def dispatch(self, request, *args, **kwargs):
        _require_view(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        export_request = get_export_request_for_user(kwargs["pk"], self.request.user)
        context["export"] = export_request
        context["activity"] = export_request.activity.all()
        context["can_download"] = user_can_download(self.request.user)
        context["can_cancel"] = (
            not export_request.is_finished
            and (
                self.request.user.is_superuser
                or self.request.user.has_perm("exports.cancel")
            )
        )
        return context


class ExportDownloadView(View):
    """Stream a generated export file to an authorized actor."""

    def get(self, request, pk, *args, **kwargs):
        _require_download(request.user)
        export_request = get_export_request_for_user(pk, request.user)
        try:
            service = DownloadExportService(user=request.user)
            service.execute(export_request, request_obj=request)
            handle = service.file_handle(export_request)
        except (
            ExportExpiredError,
            ExportNotFoundError,
            ExportDownloadDenied,
            ExportPermissionDenied,
        ) as exc:
            messages.error(request, str(exc))
            return redirect(reverse("exports:detail", kwargs={"pk": pk}))
        response = FileResponse(
            handle,
            content_type=export_request.mime_type or "application/octet-stream",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{export_request.filename}"'
        )
        return response


class ExportCancelView(View):
    """Cancel a pending/queued/processing export request."""

    def post(self, request, pk, *args, **kwargs):
        _require_view(request.user)
        export_request = get_export_request_for_user(pk, request.user)
        try:
            CancelExportService(user=request.user).execute(
                export_request, request_obj=request
            )
            messages.success(
                request,
                _("Export %(reference)s cancelled.")
                % {"reference": export_request.reference_number},
            )
        except ExportError as exc:
            messages.error(request, str(exc))
        return redirect(reverse("exports:detail", kwargs={"pk": pk}))


class ExportRegenerateView(View):
    """Regenerate a completed export with the same criteria."""

    def post(self, request, pk, *args, **kwargs):
        _require_view(request.user)
        export_request = get_export_request_for_user(pk, request.user)
        try:
            regenerated = RegenerateExportService(user=request.user).execute(
                export_request, request_obj=request
            )
            messages.success(request, _("Export regenerated successfully."))
            return redirect(reverse("exports:detail", kwargs={"pk": regenerated.pk}))
        except ExportError as exc:
            messages.error(request, str(exc))
            return redirect(reverse("exports:detail", kwargs={"pk": pk}))


class ExportSettingsView(TemplateView):
    """Read-only engine configuration (admin view)."""

    template_name = "exports/settings.html"

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_exports(request.user):
            raise PermissionDenied(_("You do not have permission to view settings."))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = active_export_configuration()
        context["templates"] = visible_export_templates(self.request.user)
        return context


class ExportTemplateListView(TemplateView):
    """List active export templates (admin view)."""

    template_name = "exports/templates.html"

    def dispatch(self, request, *args, **kwargs):
        if not user_can_manage_exports(request.user):
            raise PermissionDenied(_("You do not have permission to manage templates."))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["templates"] = visible_export_templates(self.request.user)
        return context
