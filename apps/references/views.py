"""
Views for the reference numbering module.

Every protected view enforces server-side authorization through the RBAC
permission decorators; hiding navigation or buttons is never treated as a
security control.
"""

from __future__ import annotations

import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from apps.core.exceptions import CoreException
from apps.rbac.decorators import permission_required

from . import selectors
from .constants import ReferenceModules, ReferenceNumberStatus
from .forms import ReferenceNumberSchemeForm, ReferencePreviewForm, SequenceResetForm
from .models import GeneratedReferenceNumber, ReferenceNumberScheme
from .permissions import (
    REFERENCE_NUMBERS_ACTIVATE,
    REFERENCE_NUMBERS_ARCHIVE,
    REFERENCE_NUMBERS_CORRECT,
    REFERENCE_NUMBERS_CREATE,
    REFERENCE_NUMBERS_PREVIEW,
    REFERENCE_NUMBERS_RESET,
    REFERENCE_NUMBERS_UPDATE,
    REFERENCE_NUMBERS_VIEW,
    REFERENCE_NUMBERS_VIEW_REGISTRY,
)
from .services import (
    ActivateReferenceNumberSchemeService,
    ArchiveReferenceNumberSchemeService,
    CreateReferenceNumberSchemeService,
    DeactivateReferenceNumberSchemeService,
    ManualReferenceCorrectionService,
    ResetReferenceSequenceService,
    RestoreReferenceNumberSchemeService,
    UpdateReferenceNumberSchemeService,
)

logger = logging.getLogger(__name__)


@permission_required(REFERENCE_NUMBERS_VIEW)
def references_index_view(request):
    """Landing index for the reference numbering area."""
    summary = selectors.get_reference_summary()
    schemes = selectors.get_schemes()[:8]
    return render(
        request,
        "references/index.html",
        {"summary": summary, "schemes": schemes},
    )


@permission_required(REFERENCE_NUMBERS_VIEW)
def scheme_list_view(request):
    """List reference number schemes."""
    module = request.GET.get("module", "")
    schemes = ReferenceNumberScheme.objects.with_sequences().filter(
        **({"module": module} if module else {})
    )
    return render(
        request,
        "references/scheme_list.html",
        {
            "schemes": schemes,
            "active_module": module,
            "module_choices": ReferenceModules.choices,
        },
    )


@permission_required(REFERENCE_NUMBERS_VIEW)
def scheme_detail_view(request, scheme_id):
    """Show a scheme, its sequences, recent numbers and history."""
    scheme = get_object_or_404(ReferenceNumberScheme, pk=scheme_id)
    sequences = selectors.get_sequences(scheme=scheme)
    generated = selectors.get_generated_numbers(scheme=scheme)[:20]
    history = selectors.get_reference_audit_history(
        "ReferenceNumberScheme", str(scheme.pk)
    )[:20]
    return render(
        request,
        "references/scheme_detail.html",
        {
            "scheme": scheme,
            "sequences": sequences,
            "generated": generated,
            "history": history,
        },
    )


@permission_required(REFERENCE_NUMBERS_CREATE)
def scheme_create_view(request):
    """Create a new reference number scheme."""
    if request.method == "POST":
        form = ReferenceNumberSchemeForm(request.POST)
        if form.is_valid():
            try:
                scheme = CreateReferenceNumberSchemeService(user=request.user).execute(
                    name=form.cleaned_data["name"],
                    code=form.cleaned_data["code"],
                    module=form.cleaned_data["module"],
                    record_type=form.cleaned_data["record_type"],
                    description=form.cleaned_data["description"],
                    prefix=form.cleaned_data["prefix"],
                    pattern=form.cleaned_data["pattern"],
                    organization_code=form.cleaned_data["organization_code"],
                    sequence_length=form.cleaned_data["sequence_length"],
                    start_value=form.cleaned_data["start_value"],
                    reset_period=form.cleaned_data["reset_period"],
                    fiscal_start_month=form.cleaned_data["fiscal_start_month"],
                    custom_reset_interval_days=form.cleaned_data[
                        "custom_reset_interval_days"
                    ],
                    is_default_for_module=form.cleaned_data["is_default_for_module"],
                    is_default_for_record_type=form.cleaned_data[
                        "is_default_for_record_type"
                    ],
                    is_fallback=form.cleaned_data["is_fallback"],
                    notes=form.cleaned_data["notes"],
                )
                messages.success(request, _("Reference number scheme created."))
                return redirect("core:scheme_detail", scheme_id=scheme.pk)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = ReferenceNumberSchemeForm()

    return render(
        request,
        "references/scheme_form.html",
        {"form": form, "mode": "create"},
    )


@permission_required(REFERENCE_NUMBERS_UPDATE)
def scheme_update_view(request, scheme_id):
    """Update an existing reference number scheme."""
    scheme = get_object_or_404(ReferenceNumberScheme, pk=scheme_id)
    if request.method == "POST":
        form = ReferenceNumberSchemeForm(request.POST, instance=scheme)
        if form.is_valid():
            try:
                UpdateReferenceNumberSchemeService(user=request.user).execute(
                    scheme=scheme,
                    name=form.cleaned_data["name"],
                    description=form.cleaned_data["description"],
                    record_type=form.cleaned_data["record_type"],
                    prefix=form.cleaned_data["prefix"],
                    pattern=form.cleaned_data["pattern"],
                    organization_code=form.cleaned_data["organization_code"],
                    sequence_length=form.cleaned_data["sequence_length"],
                    start_value=form.cleaned_data["start_value"],
                    reset_period=form.cleaned_data["reset_period"],
                    fiscal_start_month=form.cleaned_data["fiscal_start_month"],
                    custom_reset_interval_days=form.cleaned_data[
                        "custom_reset_interval_days"
                    ],
                    is_default_for_module=form.cleaned_data["is_default_for_module"],
                    is_default_for_record_type=form.cleaned_data[
                        "is_default_for_record_type"
                    ],
                    is_fallback=form.cleaned_data["is_fallback"],
                    notes=form.cleaned_data["notes"],
                )
                messages.success(request, _("Reference number scheme updated."))
                return redirect("core:scheme_detail", scheme_id=scheme.pk)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = ReferenceNumberSchemeForm(instance=scheme)

    return render(
        request,
        "references/scheme_form.html",
        {"form": form, "mode": "update", "scheme": scheme},
    )


@permission_required(REFERENCE_NUMBERS_ACTIVATE)
@require_http_methods(["POST"])
def scheme_activate_view(request, scheme_id):
    """Activate a reference number scheme."""
    scheme = get_object_or_404(ReferenceNumberScheme, pk=scheme_id)
    try:
        ActivateReferenceNumberSchemeService(user=request.user).execute(scheme=scheme)
        messages.success(request, _("Scheme activated."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:scheme_detail", scheme_id=scheme.pk)


@permission_required(REFERENCE_NUMBERS_ACTIVATE)
@require_http_methods(["POST"])
def scheme_deactivate_view(request, scheme_id):
    """Deactivate a reference number scheme."""
    scheme = get_object_or_404(ReferenceNumberScheme, pk=scheme_id)
    try:
        DeactivateReferenceNumberSchemeService(user=request.user).execute(scheme=scheme)
        messages.success(request, _("Scheme deactivated."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:scheme_detail", scheme_id=scheme.pk)


@permission_required(REFERENCE_NUMBERS_ARCHIVE)
@require_http_methods(["POST"])
def scheme_archive_view(request, scheme_id):
    """Archive a reference number scheme."""
    scheme = get_object_or_404(ReferenceNumberScheme, pk=scheme_id)
    try:
        ArchiveReferenceNumberSchemeService(user=request.user).execute(scheme=scheme)
        messages.success(request, _("Scheme archived."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:scheme_detail", scheme_id=scheme.pk)


@permission_required(REFERENCE_NUMBERS_ACTIVATE)
@require_http_methods(["POST"])
def scheme_restore_view(request, scheme_id):
    """Restore an archived reference number scheme."""
    scheme = get_object_or_404(ReferenceNumberScheme, pk=scheme_id)
    try:
        RestoreReferenceNumberSchemeService(user=request.user).execute(scheme=scheme)
        messages.success(request, _("Scheme restored."))
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:scheme_detail", scheme_id=scheme.pk)


@permission_required(REFERENCE_NUMBERS_RESET)
def scheme_reset_view(request, scheme_id):
    """Reset a scheme's sequence to a new starting value."""
    scheme = get_object_or_404(ReferenceNumberScheme, pk=scheme_id)
    if request.method == "POST":
        form = SequenceResetForm(request.POST)
        if form.is_valid():
            try:
                sequence = ResetReferenceSequenceService(user=request.user).execute(
                    scheme=scheme,
                    start_value=form.cleaned_data["start_value"],
                    notes=form.cleaned_data["notes"],
                )
                messages.success(
                    request,
                    _("Sequence reset; next value is %(next)s.")
                    % {"next": sequence.next_value},
                )
                return redirect("core:scheme_detail", scheme_id=scheme.pk)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = SequenceResetForm(initial={"start_value": scheme.start_value})
    return render(
        request,
        "references/reset_form.html",
        {"form": form, "scheme": scheme},
    )


@permission_required(REFERENCE_NUMBERS_PREVIEW)
def scheme_preview_view(request):
    """Preview the next reference number without consuming the sequence."""
    result = None
    error = None
    if request.method == "POST":
        form = ReferencePreviewForm(request.POST)
        if form.is_valid():
            try:
                result = selectors.next_reference_number(
                    module=form.cleaned_data["module"],
                    record_type=form.cleaned_data["record_type"] or None,
                    scheme_code=(
                        form.cleaned_data["scheme"].code
                        if form.cleaned_data["scheme"]
                        else None
                    ),
                    context={
                        "year": form.cleaned_data["year"],
                        "org": form.cleaned_data["organization_code"] or None,
                    },
                )
            except CoreException as e:
                error = str(e)
    else:
        form = ReferencePreviewForm()
    return render(
        request,
        "references/preview.html",
        {"form": form, "result": result, "error": error},
    )


@permission_required(REFERENCE_NUMBERS_VIEW_REGISTRY)
def registry_view(request):
    """List the generated reference registry with filters."""
    status = request.GET.get("status", "")
    search = request.GET.get("q", "")
    scheme_id = request.GET.get("scheme", "")
    scheme = selectors.get_scheme_by_id(scheme_id) if scheme_id else None
    generated = selectors.get_generated_numbers(
        scheme=scheme, status=status or None, search=search
    )
    return render(
        request,
        "references/registry.html",
        {
            "generated": generated,
            "status": status,
            "search": search,
            "statuses": ReferenceNumberStatus.choices,
            "schemes": selectors.get_schemes(),
            "active_scheme": scheme_id,
        },
    )


@permission_required(REFERENCE_NUMBERS_VIEW)
def sequence_list_view(request):
    """List all sequence rows."""
    scheme_id = request.GET.get("scheme", "")
    scheme = selectors.get_scheme_by_id(scheme_id) if scheme_id else None
    sequences = selectors.get_sequences(scheme=scheme)
    return render(
        request,
        "references/sequence_list.html",
        {
            "sequences": sequences,
            "schemes": selectors.get_schemes(),
            "active_scheme": scheme_id,
        },
    )


ENTITY_TYPES = (
    ("ReferenceNumberScheme", "Scheme"),
    ("GeneratedReferenceNumber", "Reference"),
)


@permission_required(REFERENCE_NUMBERS_VIEW)
def audit_list_view(request):
    """List reference numbering audit records."""
    entity_type = request.GET.get("entity_type", "")
    history = selectors.get_reference_audit_history(entity_type or None)
    return render(
        request,
        "references/audit_list.html",
        {
            "history": history,
            "active_type": entity_type,
            "entity_types": ENTITY_TYPES,
        },
    )


@permission_required(REFERENCE_NUMBERS_CORRECT)
@require_http_methods(["POST"])
def correct_reference_view(request, generated_id):
    """Authorized manual correction of a misassigned reference."""
    generated = get_object_or_404(GeneratedReferenceNumber, pk=generated_id)
    reason = request.POST.get("reason", "")
    try:
        replacement = ManualReferenceCorrectionService(user=request.user).execute(
            generated=generated, reason=reason
        )
        messages.success(
            request,
            _("Reference corrected to %(reference)s.")
            % {"reference": replacement.reference_number},
        )
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect("core:reference_registry")
