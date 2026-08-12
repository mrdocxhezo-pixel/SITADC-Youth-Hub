"""Permission-aware, service-backed document management views.

All views are permission checked and read through the fail-closed selectors
so that unauthorized actors can neither see nor modify documents.
"""

from __future__ import annotations

import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView

from apps.rbac.authorization import user_has_permission
from apps.rbac.mixins import PermissionRequiredMixin

from .constants import (
    ConfidentialityLevel,
    DocumentPermissions,
    DocumentStatus,
    HoldStatus,
)
from .forms import (
    DocumentCheckinForm,
    DocumentCheckoutForm,
    DocumentDisposalRequestForm,
    DocumentFolderForm,
    DocumentHoldForm,
    DocumentMetadataForm,
    DocumentSearchForm,
    DocumentShareForm,
    DocumentUploadForm,
    DocumentVersionUploadForm,
    DocumentWorkflowActionForm,
)
from .models import (
    Document,
    DocumentAuditRecord,
    DocumentCategory,
    DocumentFolder,
    DocumentHold,
    DocumentShare,
    DocumentTag,
    DocumentType,
)
from .permissions import (
    can_download,
    can_view_document,
)
from .selectors import (
    get_active_checkout,
    get_all_categories,
    get_document_dashboard_stats,
    get_document_holds,
    get_document_shares,
    get_folder_breadcrumbs,
    get_folder_by_id,
    get_folder_children,
    get_root_folders,
    get_version_history,
)
from .services import (
    apply_hold,
    approve_document,
    archive_document,
    cancel_checkout,
    checkin_document,
    checkout_document,
    create_folder,
    delete_document,
    publish_document,
    release_hold,
    request_disposal,
    restore_document,
    review_document,
    revoke_share,
    share_document,
    submit_for_review,
    unpublish_document,
    update_document_metadata,
    upload_document,
    upload_new_version,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Permission Mixin
# ---------------------------------------------------------------------------


class DocumentPermissionMixin(PermissionRequiredMixin):
    """Allow any listed document permission, with module-manager override."""

    any_permission = True

    def test_func(self) -> bool:
        required = self.permission_required
        permissions = (required,) if isinstance(required, str) else tuple(required)
        return any(user_has_permission(self.request.user, code) for code in permissions)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _can(user, *permission_codes: str) -> bool:
    return any(user_has_permission(user, code) for code in permission_codes)


def _available_workflow_actions(user, document: Document) -> list:
    """Return valid ``(value, label, permission)`` next actions for a document."""
    status = document.status
    actions = []

    if status in {
        DocumentStatus.DRAFT,
        DocumentStatus.UPLOADED,
        DocumentStatus.RETURNED_FOR_CORRECTION,
    }:
        actions.append(("submit", _("Submit for Review"), DocumentPermissions.SUBMIT))

    if status in {DocumentStatus.PENDING_REVIEW, DocumentStatus.UNDER_REVIEW}:
        actions.append(
            ("approve_review", _("Approve & Forward"), DocumentPermissions.REVIEW)
        )
        actions.append(
            (
                "return",
                _("Return for Correction"),
                DocumentPermissions.RETURN_FOR_CORRECTION,
            )
        )

    if status == DocumentStatus.PENDING_APPROVAL:
        actions.append(("approve", _("Approve"), DocumentPermissions.APPROVE))

    if status == DocumentStatus.APPROVED:
        actions.append(("publish", _("Publish"), DocumentPermissions.PUBLISH))

    if status == DocumentStatus.PUBLISHED:
        actions.append(("unpublish", _("Unpublish"), DocumentPermissions.UNPUBLISH))

    if status not in {DocumentStatus.ARCHIVED, DocumentStatus.DISPOSED}:
        actions.append(("archive", _("Archive"), DocumentPermissions.ARCHIVE))

    if status == DocumentStatus.ARCHIVED:
        actions.append(("restore", _("Restore"), DocumentPermissions.RESTORE))

    return [
        (value, label) for value, label, permission in actions if _can(user, permission)
    ]


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


def _scoped_document(user, pk, *, include_archived: bool = False) -> Document:
    return get_object_or_404(
        (
            Document.objects.filter(
                Q(owner=user) | Q(created_by=user) | Q(is_deleted=False),
                pk=pk,
            )
            if not include_archived
            else Document.objects.filter(pk=pk)
        ),
        pk=pk,
    )


def _format_file_size(size_bytes: int) -> str:
    """Return human-readable file size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# ── Dashboard ────────────────────────────────────────────────────────────


class DocumentDashboardView(DocumentPermissionMixin, TemplateView):
    template_name = "documents/dashboard.html"
    permission_required = DocumentPermissions.VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        stats = get_document_dashboard_stats(user)
        context.update(
            {
                "stats": stats,
                "recent_documents": (
                    Document.objects.filter(is_deleted=False)
                    .select_related("category", "document_type", "owner")
                    .order_by("-created_at")[:6]
                ),
                "my_documents": (
                    Document.objects.filter(owner=user, is_deleted=False)
                    .select_related("category", "document_type")
                    .order_by("-created_at")[:6]
                ),
                "can_upload": _can(
                    user, DocumentPermissions.UPLOAD, DocumentPermissions.CREATE
                ),
                "can_manage_categories": _can(
                    user, DocumentPermissions.MANAGE_CATEGORIES
                ),
                "can_view_audit": _can(user, DocumentPermissions.VIEW_AUDIT),
            }
        )
        return context


# ── Document Directory ───────────────────────────────────────────────────


class DocumentListView(DocumentPermissionMixin, ListView):
    model = Document
    template_name = "documents/document_list.html"
    context_object_name = "documents"
    paginate_by = 20
    permission_required = DocumentPermissions.VIEW

    def get_queryset(self):
        qs = Document.objects.filter(is_deleted=False).select_related(
            "category", "document_type", "folder", "owner", "created_by"
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(reference_number__icontains=q)
                | Q(description__icontains=q)
                | Q(original_filename__icontains=q)
            )
        category = self.request.GET.get("category", "")
        if category:
            qs = qs.filter(category_id=category)
        document_type = self.request.GET.get("document_type", "")
        if document_type:
            qs = qs.filter(document_type_id=document_type)
        status = self.request.GET.get("status", "")
        if status:
            qs = qs.filter(status=status)
        confidentiality = self.request.GET.get("confidentiality_level", "")
        if confidentiality:
            qs = qs.filter(confidentiality_level=confidentiality)
        sort_by = self.request.GET.get("sort", "-created_at")
        valid_sorts = {
            "-created_at",
            "created_at",
            "-updated_at",
            "updated_at",
            "title",
            "-title",
            "-file_size",
            "file_size",
        }
        if sort_by not in valid_sorts:
            sort_by = "-created_at"
        return qs.order_by(sort_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = DocumentSearchForm(self.request.GET)
        context["status_choices"] = DocumentStatus.choices
        context["confidentiality_choices"] = ConfidentialityLevel.choices
        context["categories"] = DocumentCategory.objects.filter(is_active=True)
        context["document_types"] = DocumentType.objects.filter(is_active=True)
        context["can_upload"] = _can(
            self.request.user, DocumentPermissions.UPLOAD, DocumentPermissions.CREATE
        )
        query = self.request.GET.copy()
        query.pop("page", None)
        context["query_without_page"] = query.urlencode()
        return context


# ── My Documents ─────────────────────────────────────────────────────────


class MyDocumentsView(DocumentPermissionMixin, ListView):
    model = Document
    template_name = "documents/my_documents.html"
    context_object_name = "documents"
    paginate_by = 20
    permission_required = DocumentPermissions.VIEW

    def get_queryset(self):
        return (
            Document.objects.filter(
                Q(owner=self.request.user) | Q(created_by=self.request.user),
                is_deleted=False,
            )
            .select_related(
                "category", "document_type", "folder", "owner", "created_by"
            )
            .order_by("-updated_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_upload"] = _can(
            self.request.user, DocumentPermissions.UPLOAD, DocumentPermissions.CREATE
        )
        return context


# ── Upload ───────────────────────────────────────────────────────────────


class DocumentCreateView(DocumentPermissionMixin, FormView):
    template_name = "documents/document_form.html"
    form_class = DocumentUploadForm
    permission_required = DocumentPermissions.UPLOAD

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Document"
        context["is_update"] = False
        context["cancel_url"] = redirect("documents:list").url
        context["categories"] = DocumentCategory.objects.filter(is_active=True)
        context["document_types"] = DocumentType.objects.filter(is_active=True)
        context["folders"] = DocumentFolder.objects.filter(is_deleted=False)
        context["confidentiality_choices"] = ConfidentialityLevel.choices
        context["tags"] = DocumentTag.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            document = upload_document(
                user=self.request.user,
                file_obj=data["file"],
                title=data["title"],
                description=data.get("description", ""),
                category=data.get("category"),
                document_type=data.get("document_type"),
                folder=data.get("folder"),
                confidentiality_level=data.get(
                    "confidentiality_level", ConfidentialityLevel.INTERNAL
                ),
                tags=data.get("tags"),
                effective_date=data.get("effective_date"),
                expiry_date=data.get("expiry_date"),
                keywords=(
                    data.get("keywords", "").split(",") if data.get("keywords") else []
                ),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Document {document.reference_number} uploaded successfully.",
        )
        return redirect("documents:detail", pk=document.pk)


# ── Detail ───────────────────────────────────────────────────────────────


class DocumentDetailView(DocumentPermissionMixin, DetailView):
    template_name = "documents/document_detail.html"
    context_object_name = "document"
    permission_required = DocumentPermissions.VIEW

    def get_queryset(self):
        return Document.objects.filter(is_deleted=False).select_related(
            "category",
            "document_type",
            "folder",
            "owner",
            "created_by",
            "updated_by",
            "approved_by",
            "published_by",
            "retention_category",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = self.object
        user = self.request.user
        active_checkout = get_active_checkout(document)
        context.update(
            {
                "active_checkout": active_checkout,
                "versions": get_version_history(document),
                "shares": get_document_shares(document),
                "holds": get_document_holds(document),
                "timeline": document.timeline_events.select_related("actor").order_by(
                    "-created_at"
                )[:20],
                "file_size_display": _format_file_size(document.file_size or 0),
                "can_edit": _can(user, DocumentPermissions.UPDATE_METADATA),
                "can_upload_version": _can(user, DocumentPermissions.UPLOAD_VERSION),
                "can_checkout": _can(user, DocumentPermissions.CHECKOUT),
                "can_checkin": _can(user, DocumentPermissions.CHECKIN),
                "can_cancel_checkout": _can(user, DocumentPermissions.CANCEL_CHECKOUT),
                "can_submit": _can(user, DocumentPermissions.SUBMIT),
                "can_review": _can(user, DocumentPermissions.REVIEW),
                "can_approve": _can(user, DocumentPermissions.APPROVE),
                "can_publish": _can(user, DocumentPermissions.PUBLISH),
                "can_unpublish": _can(user, DocumentPermissions.UNPUBLISH),
                "can_archive": _can(user, DocumentPermissions.ARCHIVE),
                "can_restore": _can(user, DocumentPermissions.RESTORE),
                "can_share": _can(user, DocumentPermissions.SHARE_INTERNAL),
                "can_hold": _can(user, DocumentPermissions.ARCHIVE),
                "can_disposal": _can(user, DocumentPermissions.REQUEST_DISPOSAL),
                "can_delete": _can(user, DocumentPermissions.MANAGE_CATEGORIES),
                "can_download": _can(user, DocumentPermissions.DOWNLOAD),
                "can_view_audit": _can(user, DocumentPermissions.VIEW_AUDIT),
                "is_checked_out": active_checkout is not None,
                "is_checked_out_by_me": (
                    active_checkout.checked_out_by_id == user.pk
                    if active_checkout
                    else False
                ),
            }
        )
        return context


# ── Metadata Update ──────────────────────────────────────────────────────


class DocumentMetadataUpdateView(DocumentPermissionMixin, FormView):
    template_name = "documents/document_form.html"
    form_class = DocumentMetadataForm
    permission_required = DocumentPermissions.UPDATE_METADATA

    def dispatch(self, request, *args, **kwargs):
        self.document = _scoped_document(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        doc = self.document
        return {
            "title": doc.title,
            "short_title": doc.short_title,
            "description": doc.description,
            "category": doc.category_id,
            "document_type": doc.document_type_id,
            "folder": doc.folder_id,
            "confidentiality_level": doc.confidentiality_level,
            "is_sensitive": doc.is_sensitive,
            "effective_date": doc.effective_date,
            "expiry_date": doc.expiry_date,
            "review_date": doc.review_date,
            "renewal_date": doc.renewal_date,
            "keywords": ", ".join(doc.keywords) if doc.keywords else "",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity_label"] = "Document"
        context["is_update"] = True
        context["object"] = self.document
        context["cancel_url"] = redirect("documents:detail", pk=self.document.pk).url
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            update_document_metadata(
                user=self.request.user,
                document=self.document,
                title=data.get("title"),
                short_title=data.get("short_title"),
                description=data.get("description"),
                category=data.get("category"),
                document_type=data.get("document_type"),
                folder=data.get("folder"),
                confidentiality_level=data.get("confidentiality_level"),
                is_sensitive=data.get("is_sensitive"),
                effective_date=data.get("effective_date"),
                expiry_date=data.get("expiry_date"),
                review_date=data.get("review_date"),
                renewal_date=data.get("renewal_date"),
                keywords=(
                    data.get("keywords", "").split(",") if data.get("keywords") else []
                ),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Document metadata updated.")
        return redirect("documents:detail", pk=self.document.pk)


# ── Preview ──────────────────────────────────────────────────────────────


class DocumentPreviewView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.VIEW

    def get(self, request, pk, *args, **kwargs):
        document = _scoped_document(request.user, pk)
        if not can_view_document(request.user, document):
            raise PermissionDenied
        if not document.file:
            raise Http404("No file available for preview.")
        content_type = document.mime_type or "application/octet-stream"
        try:
            response = FileResponse(
                document.file.open("rb"),
                content_type=content_type,
            )
            response["Content-Disposition"] = (
                f'inline; filename="{document.original_filename}"'
            )
            return response
        except (OSError, FileNotFoundError):
            raise Http404("File not found.") from None


# ── Download ─────────────────────────────────────────────────────────────


class DocumentDownloadView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.DOWNLOAD

    def get(self, request, pk, *args, **kwargs):
        document = _scoped_document(request.user, pk)
        if not can_download(request.user, document):
            raise PermissionDenied
        if not document.file:
            raise Http404("No file available for download.")
        try:
            response = FileResponse(
                document.file.open("rb"),
                content_type=document.mime_type or "application/octet-stream",
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{document.original_filename}"'
            )
            return response
        except (OSError, FileNotFoundError):
            raise Http404("File not found.") from None


# ── Version Upload ───────────────────────────────────────────────────────


class DocumentVersionUploadView(DocumentPermissionMixin, FormView):
    template_name = "documents/document_version_form.html"
    form_class = DocumentVersionUploadForm
    permission_required = DocumentPermissions.UPLOAD_VERSION

    def dispatch(self, request, *args, **kwargs):
        self.document = _scoped_document(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.document
        context["cancel_url"] = redirect("documents:detail", pk=self.document.pk).url
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            version = upload_new_version(
                user=self.request.user,
                document=self.document,
                file_obj=data["file"],
                version_type=data.get("version_type", "MAJOR"),
                change_summary=data.get("change_summary", ""),
                change_reason=data.get("change_reason", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Version {version.version_label} uploaded successfully.",
        )
        return redirect("documents:detail", pk=self.document.pk)


# ── Version History ──────────────────────────────────────────────────────


class DocumentVersionHistoryView(DocumentPermissionMixin, DetailView):
    template_name = "documents/document_versions.html"
    context_object_name = "document"
    permission_required = DocumentPermissions.VIEW

    def get_queryset(self):
        return Document.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["versions"] = get_version_history(self.object)
        return context


# ── Checkout ─────────────────────────────────────────────────────────────


class DocumentCheckoutView(DocumentPermissionMixin, FormView):
    template_name = "documents/document_workflow_form.html"
    form_class = DocumentCheckoutForm
    permission_required = DocumentPermissions.CHECKOUT

    def dispatch(self, request, *args, **kwargs):
        self.document = _scoped_document(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.document
        context["title"] = "Check out document"
        context["cancel_url"] = redirect("documents:detail", pk=self.document.pk).url
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            checkout_document(
                user=self.request.user,
                document=self.document,
                expected_return_date=data.get("expected_return_date"),
                checkout_reason=data.get("checkout_reason", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Document checked out.")
        return redirect("documents:detail", pk=self.document.pk)


# ── Checkin ──────────────────────────────────────────────────────────────


class DocumentCheckinView(DocumentPermissionMixin, FormView):
    template_name = "documents/document_workflow_form.html"
    form_class = DocumentCheckinForm
    permission_required = DocumentPermissions.CHECKIN

    def dispatch(self, request, *args, **kwargs):
        self.document = _scoped_document(request.user, kwargs["pk"])
        self.checkout = get_active_checkout(self.document)
        if not self.checkout:
            messages.error(request, "Document is not checked out.")
            return redirect("documents:detail", pk=self.document.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.document
        context["title"] = "Check in document"
        context["cancel_url"] = redirect("documents:detail", pk=self.document.pk).url
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            checkin_document(
                user=self.request.user,
                checkout=self.checkout,
                file_obj=data.get("file"),
                checkin_notes=data.get("checkin_notes", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Document checked in.")
        return redirect("documents:detail", pk=self.document.pk)


# ── Cancel Checkout ──────────────────────────────────────────────────────


class DocumentCancelCheckoutView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.CANCEL_CHECKOUT

    def post(self, request, pk, *args, **kwargs):
        document = _scoped_document(request.user, pk)
        checkout = get_active_checkout(document)
        if not checkout:
            messages.error(request, "Document is not checked out.")
            return redirect("documents:detail", pk=pk)
        try:
            cancel_checkout(user=request.user, checkout=checkout)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
            return redirect("documents:detail", pk=pk)
        messages.success(request, "Checkout cancelled.")
        return redirect("documents:detail", pk=pk)


# ── Submit for Review ────────────────────────────────────────────────────


class DocumentWorkflowActionView(DocumentPermissionMixin, FormView):
    """Execute the next workflow action selected by the user."""

    template_name = "documents/document_workflow_form.html"
    form_class = DocumentWorkflowActionForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        self.document = _scoped_document(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    @property
    def permission_required(self):
        return DocumentPermissions.VIEW

    def get_permission_denied_message(self):
        return "You do not have permission to perform workflow actions."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["action_choices"] = _available_workflow_actions(
            self.request.user, self.document
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.document
        context["title"] = "Workflow action"
        context["action_choices"] = _available_workflow_actions(
            self.request.user, self.document
        )
        context["cancel_url"] = redirect("documents:detail", pk=self.document.pk).url
        return context

    def form_valid(self, form):
        user = self.request.user
        document = self.document
        action = form.cleaned_data["action"]
        comments = form.cleaned_data.get("comments", "")
        try:
            if action == "submit":
                submit_for_review(user=user, document=document)
            elif action == "approve_review":
                review_document(
                    user=user, document=document, approve=True, comments=comments
                )
            elif action == "return":
                review_document(
                    user=user, document=document, approve=False, comments=comments
                )
            elif action == "approve":
                approve_document(user=user, document=document, comments=comments)
            elif action == "publish":
                publish_document(user=user, document=document)
            elif action == "unpublish":
                unpublish_document(user=user, document=document)
            elif action == "archive":
                archive_document(user=user, document=document, reason=comments)
            elif action == "restore":
                restore_document(user=user, document=document, reason=comments)
            else:
                raise ValidationError("Unknown workflow action selected.")
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Workflow action completed successfully.")
        return redirect("documents:detail", pk=document.pk)


# ── Submit for Review ────────────────────────────────────────────────────


class DocumentSubmitReviewView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.SUBMIT

    def post(self, request, pk, *args, **kwargs):
        document = _scoped_document(request.user, pk)
        try:
            submit_for_review(user=request.user, document=document)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
            return redirect("documents:detail", pk=pk)
        messages.success(request, "Document submitted for review.")
        return redirect("documents:detail", pk=pk)


# ── Review ───────────────────────────────────────────────────────────────


class DocumentReviewView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.REVIEW

    def post(self, request, pk, *args, **kwargs):
        document = _scoped_document(request.user, pk)
        approve = request.POST.get("approve", "true") == "true"
        comments = request.POST.get("comments", "")
        try:
            review_document(
                user=request.user,
                document=document,
                approve=approve,
                comments=comments,
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
            return redirect("documents:detail", pk=pk)
        if approve:
            messages.success(request, "Document reviewed and forwarded for approval.")
        else:
            messages.warning(request, "Document returned for correction.")
        return redirect("documents:detail", pk=pk)


# ── Approve ──────────────────────────────────────────────────────────────


class DocumentApproveView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.APPROVE

    def post(self, request, pk, *args, **kwargs):
        document = _scoped_document(request.user, pk)
        comments = request.POST.get("comments", "")
        try:
            approve_document(user=request.user, document=document, comments=comments)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
            return redirect("documents:detail", pk=pk)
        messages.success(request, "Document approved.")
        return redirect("documents:detail", pk=pk)


# ── Publish ──────────────────────────────────────────────────────────────


class DocumentPublishView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.PUBLISH

    def post(self, request, pk, *args, **kwargs):
        document = _scoped_document(request.user, pk)
        try:
            publish_document(user=request.user, document=document)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
            return redirect("documents:detail", pk=pk)
        messages.success(request, "Document published.")
        return redirect("documents:detail", pk=pk)


# ── Unpublish ────────────────────────────────────────────────────────────


class DocumentUnpublishView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.UNPUBLISH

    def post(self, request, pk, *args, **kwargs):
        document = _scoped_document(request.user, pk)
        try:
            unpublish_document(user=request.user, document=document)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
            return redirect("documents:detail", pk=pk)
        messages.success(request, "Document unpublished.")
        return redirect("documents:detail", pk=pk)


# ── Archive ──────────────────────────────────────────────────────────────


class DocumentArchiveView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.ARCHIVE

    def post(self, request, pk, *args, **kwargs):
        document = _scoped_document(request.user, pk)
        reason = request.POST.get("reason", "")
        try:
            archive_document(user=request.user, document=document, reason=reason)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "Document archived.")
        return redirect("documents:detail", pk=pk)


# ── Restore ──────────────────────────────────────────────────────────────


class DocumentRestoreView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.RESTORE

    def post(self, request, pk, *args, **kwargs):
        document = _scoped_document(request.user, pk)
        reason = request.POST.get("reason", "")
        try:
            restore_document(user=request.user, document=document, reason=reason)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "Document restored.")
        return redirect("documents:detail", pk=pk)


# ── Share Create ─────────────────────────────────────────────────────────


class DocumentShareCreateView(DocumentPermissionMixin, FormView):
    template_name = "documents/document_workflow_form.html"
    form_class = DocumentShareForm
    permission_required = DocumentPermissions.SHARE_INTERNAL

    def dispatch(self, request, *args, **kwargs):
        self.document = _scoped_document(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.document
        context["title"] = "Share document"
        context["cancel_url"] = redirect("documents:detail", pk=self.document.pk).url
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            share_document(
                user=self.request.user,
                document=self.document,
                shared_with_user=data["shared_with_user"],
                permission_level=data.get("permission_level", "VIEW"),
                download_allowed=data.get("download_allowed", False),
                print_allowed=data.get("print_allowed", False),
                expiry_date=data.get("expiry_date"),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Document shared successfully.")
        return redirect("documents:detail", pk=self.document.pk)


# ── Share Revoke ─────────────────────────────────────────────────────────


class DocumentShareRevokeView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.SHARE_INTERNAL

    def post(self, request, share_pk, *args, **kwargs):
        share = get_object_or_404(
            DocumentShare.objects.filter(
                document__in=Document.objects.filter(
                    Q(owner=request.user) | Q(created_by=request.user)
                )
            ),
            pk=share_pk,
        )
        try:
            revoke_share(user=request.user, share=share)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
            return redirect("documents:detail", pk=share.document_id)
        messages.success(request, "Share revoked.")
        return redirect("documents:detail", pk=share.document_id)


# ── Hold Create ──────────────────────────────────────────────────────────


class DocumentHoldCreateView(DocumentPermissionMixin, FormView):
    template_name = "documents/document_workflow_form.html"
    form_class = DocumentHoldForm
    permission_required = DocumentPermissions.ARCHIVE

    def dispatch(self, request, *args, **kwargs):
        self.document = _scoped_document(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.document
        context["title"] = "Apply hold"
        context["cancel_url"] = redirect("documents:detail", pk=self.document.pk).url
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            apply_hold(
                user=self.request.user,
                document=self.document,
                hold_type=data["hold_type"],
                reason=data["reason"],
                review_date=data.get("review_date"),
                restricted_notes=data.get("restricted_notes", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Hold applied to document.")
        return redirect("documents:detail", pk=self.document.pk)


# ── Hold Release ─────────────────────────────────────────────────────────


class DocumentHoldReleaseView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.ARCHIVE

    def post(self, request, hold_pk, *args, **kwargs):
        hold = get_object_or_404(DocumentHold, pk=hold_pk, status=HoldStatus.ACTIVE)
        if not can_view_document(request.user, hold.document):
            raise PermissionDenied
        reason = request.POST.get("reason", "")
        try:
            release_hold(user=request.user, hold=hold, reason=reason)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "Hold released.")
        return redirect("documents:detail", pk=hold.document_id)


# ── Disposal Request ─────────────────────────────────────────────────────


class DocumentDisposalRequestView(DocumentPermissionMixin, FormView):
    template_name = "documents/document_workflow_form.html"
    form_class = DocumentDisposalRequestForm
    permission_required = DocumentPermissions.REQUEST_DISPOSAL

    def dispatch(self, request, *args, **kwargs):
        self.document = _scoped_document(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.document
        context["title"] = "Request disposal"
        context["cancel_url"] = redirect("documents:detail", pk=self.document.pk).url
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            request_disposal(
                user=self.request.user,
                document=self.document,
                disposal_reason=data.get("disposal_reason", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Disposal requested.")
        return redirect("documents:detail", pk=self.document.pk)


# ── Delete (Soft) ────────────────────────────────────────────────────────


class DocumentDeleteView(DocumentPermissionMixin, View):
    permission_required = DocumentPermissions.ARCHIVE

    def post(self, request, pk, *args, **kwargs):
        document = _scoped_document(request.user, pk)
        try:
            delete_document(user=request.user, document=document)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
            return redirect("documents:detail", pk=pk)
        messages.success(request, "Document deleted.")
        return redirect("documents:list")


# ── Folder Create ────────────────────────────────────────────────────────


class DocumentFolderCreateView(DocumentPermissionMixin, FormView):
    template_name = "documents/folder_form.html"
    form_class = DocumentFolderForm
    permission_required = DocumentPermissions.MANAGE_FOLDERS

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent_pk = self.request.GET.get("parent")
        context["parent_folder"] = get_folder_by_id(parent_pk) if parent_pk else None
        context["cancel_url"] = redirect("documents:folder_list").url
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            folder = create_folder(
                user=self.request.user,
                name=data["name"],
                description=data.get("description", ""),
                parent=data.get("parent"),
                confidentiality_level=data.get(
                    "confidentiality_level", ConfidentialityLevel.INTERNAL
                ),
            )
        except (ValidationError, PermissionDenied) as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, f"Folder '{folder.name}' created.")
        if folder.parent:
            return redirect("documents:folder_detail", pk=folder.parent_id)
        return redirect("documents:folder_list")


# ── Folder List ────────────────────────────────────────────────────────


class DocumentFolderListView(DocumentPermissionMixin, ListView):
    model = DocumentFolder
    template_name = "documents/folder_list.html"
    context_object_name = "folders"
    paginate_by = 20
    permission_required = DocumentPermissions.VIEW

    def get_queryset(self):
        return get_root_folders().annotate(document_count=Count("documents"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create_folder"] = _can(
            self.request.user, DocumentPermissions.MANAGE_FOLDERS
        )
        return context


# ── Folder Detail ────────────────────────────────────────────────────────


class DocumentFolderView(DocumentPermissionMixin, DetailView):
    model = DocumentFolder
    template_name = "documents/folder_detail.html"
    context_object_name = "folder"
    permission_required = DocumentPermissions.VIEW

    def get_queryset(self):
        return DocumentFolder.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        folder = self.object
        context["subfolders"] = get_folder_children(folder)
        context["documents"] = (
            Document.objects.filter(folder=folder, is_deleted=False)
            .select_related("category", "document_type", "owner")
            .order_by("-created_at")
        )
        context["breadcrumbs"] = get_folder_breadcrumbs(folder)
        context["can_create_folder"] = _can(
            self.request.user, DocumentPermissions.MANAGE_FOLDERS
        )
        context["can_upload"] = _can(
            self.request.user, DocumentPermissions.UPLOAD, DocumentPermissions.CREATE
        )
        return context


# ── Category List ────────────────────────────────────────────────────────


class DocumentCategoryListView(DocumentPermissionMixin, ListView):
    model = DocumentCategory
    template_name = "documents/category_list.html"
    context_object_name = "categories"
    paginate_by = 20
    permission_required = DocumentPermissions.VIEW

    def get_queryset(self):
        return get_all_categories().annotate(document_count=Count("documents"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage"] = _can(
            self.request.user, DocumentPermissions.MANAGE_CATEGORIES
        )
        return context


# ── Category Detail ──────────────────────────────────────────────────────


class DocumentCategoryDetailView(DocumentPermissionMixin, DetailView):
    model = DocumentCategory
    template_name = "documents/category_detail.html"
    context_object_name = "category"
    permission_required = DocumentPermissions.VIEW

    def get_queryset(self):
        return DocumentCategory.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documents"] = (
            Document.objects.filter(category=self.object, is_deleted=False)
            .select_related("document_type", "folder", "owner")
            .order_by("-created_at")
        )
        return context


# ── Audit Log ────────────────────────────────────────────────────────────


class DocumentAuditLogView(DocumentPermissionMixin, DetailView):
    template_name = "documents/document_audit_log.html"
    context_object_name = "document"
    permission_required = DocumentPermissions.VIEW_AUDIT

    def get_queryset(self):
        return Document.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["audit_records"] = (
            DocumentAuditRecord.objects.filter(
                Q(entity_type="Document", entity_id=str(self.object.pk))
                | Q(
                    entity_type="DocumentVersion",
                    entity_id__in=[str(v.pk) for v in self.object.versions.all()],
                )
            )
            .select_related("changed_by")
            .order_by("-created_at")
        )
        return context


class DocumentAuditLogListView(DocumentPermissionMixin, ListView):
    """Global audit log across all documents."""

    template_name = "documents/document_audit_log.html"
    context_object_name = "audit_records"
    permission_required = DocumentPermissions.VIEW_AUDIT
    paginate_by = 50

    def get_queryset(self):
        return DocumentAuditRecord.objects.select_related("changed_by").order_by(
            "-created_at"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["global_audit"] = True
        return context
