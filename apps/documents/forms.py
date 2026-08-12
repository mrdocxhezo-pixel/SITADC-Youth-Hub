"""Forms for the Document Management module."""
from __future__ import annotations

import json

from django import forms
from django.utils.translation import gettext_lazy as _

from .constants import ConfidentialityLevel, VersionType
from .models import (
    Document,
    DocumentCategory,
    DocumentDisposalRequest,
    DocumentFolder,
    DocumentHold,
    DocumentRelationship,
    DocumentShare,
    DocumentTag,
    DocumentType,
    DocumentVersion,
    RetentionCategory,
)


# ---------------------------------------------------------------------------
# Document Upload Form
# ---------------------------------------------------------------------------


class DocumentUploadForm(forms.Form):
    """Form for uploading a new document."""

    file = forms.FileField(
        label=_("Document File"),
        help_text=_("Upload a document file. Maximum size depends on document type."),
    )
    title = forms.CharField(
        max_length=255,
        label=_("Document Title"),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label=_("Description"),
    )
    category = forms.ModelChoiceField(
        queryset=DocumentCategory.objects.filter(is_active=True),
        required=False,
        label=_("Category"),
    )
    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.filter(is_active=True),
        required=False,
        label=_("Document Type"),
    )
    folder = forms.ModelChoiceField(
        queryset=DocumentFolder.objects.filter(is_deleted=False),
        required=False,
        label=_("Folder"),
    )
    confidentiality_level = forms.ChoiceField(
        choices=ConfidentialityLevel.choices,
        initial=ConfidentialityLevel.INTERNAL,
        label=_("Confidentiality Level"),
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=DocumentTag.objects.filter(is_active=True),
        required=False,
        label=_("Tags"),
    )
    effective_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label=_("Effective Date"),
    )
    expiry_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label=_("Expiry Date"),
    )
    keywords = forms.CharField(
        required=False,
        help_text=_("Comma-separated keywords"),
        label=_("Keywords"),
    )


# ---------------------------------------------------------------------------
# Document Metadata Form
# ---------------------------------------------------------------------------


class DocumentMetadataForm(forms.ModelForm):
    """Form for editing document metadata."""

    keywords = forms.CharField(
        required=False,
        help_text=_("Comma-separated keywords"),
        label=_("Keywords"),
    )

    class Meta:
        model = Document
        fields = [
            "title",
            "short_title",
            "description",
            "category",
            "document_type",
            "folder",
            "confidentiality_level",
            "is_sensitive",
            "effective_date",
            "expiry_date",
            "review_date",
            "renewal_date",
            "keywords",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "effective_date": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
            "review_date": forms.DateInput(attrs={"type": "date"}),
            "renewal_date": forms.DateInput(attrs={"type": "date"}),
            "keywords": forms.TextInput(
                attrs={"placeholder": _("Comma-separated keywords")}
            ),
        }

    def clean_keywords(self):
        value = self.cleaned_data.get("keywords")
        if isinstance(value, str) and value.strip():
            keywords = [k.strip() for k in value.split(",") if k.strip()]
            return json.dumps(keywords)
        return json.dumps([])


# ---------------------------------------------------------------------------
# Document Version Upload Form
# ---------------------------------------------------------------------------


class DocumentVersionUploadForm(forms.Form):
    """Form for uploading a new document version."""

    file = forms.FileField(label=_("New Version File"))
    version_type = forms.ChoiceField(
        choices=VersionType.choices,
        initial=VersionType.MAJOR,
        label=_("Version Type"),
    )
    change_summary = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label=_("Change Summary"),
    )
    change_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        label=_("Change Reason"),
    )


# ---------------------------------------------------------------------------
# Workflow Action Form
# ---------------------------------------------------------------------------


class DocumentWorkflowActionForm(forms.Form):
    """Select and execute a single next workflow action for a document."""

    action = forms.ChoiceField(
        choices=[],
        label=_("Select Action"),
        widget=forms.Select(attrs={"class": "form-select", "required": True}),
    )
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        label=_("Comments"),
    )

    def __init__(self, *args, action_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if action_choices:
            self.fields["action"].choices = [("", _("Choose an action..."))] + list(
                action_choices
            )


# ---------------------------------------------------------------------------
# Document Checkout Form
# ---------------------------------------------------------------------------


class DocumentCheckoutForm(forms.Form):
    """Form for checking out a document."""

    expected_return_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label=_("Expected Return Date"),
    )
    checkout_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label=_("Reason for Checkout"),
    )


# ---------------------------------------------------------------------------
# Document Checkin Form
# ---------------------------------------------------------------------------


class DocumentCheckinForm(forms.Form):
    """Form for checking in a document."""

    file = forms.FileField(
        required=False,
        label=_("Updated File"),
        help_text=_("Upload the edited file, or leave empty to check in without changes."),
    )
    checkin_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label=_("Check-in Notes"),
    )


# ---------------------------------------------------------------------------
# Document Share Form
# ---------------------------------------------------------------------------


class DocumentShareForm(forms.ModelForm):
    """Form for sharing a document."""

    class Meta:
        model = DocumentShare
        fields = [
            "shared_with_user",
            "permission_level",
            "download_allowed",
            "print_allowed",
            "reshare_allowed",
            "expiry_date",
        ]
        widgets = {
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }


# ---------------------------------------------------------------------------
# Document Search Form
# ---------------------------------------------------------------------------


class DocumentSearchForm(forms.Form):
    """Form for searching documents."""

    q = forms.CharField(
        required=False,
        label=_("Search"),
        widget=forms.TextInput(
            attrs={"placeholder": _("Search documents..."), "class": "form-control"}
        ),
    )
    category = forms.ModelChoiceField(
        queryset=DocumentCategory.objects.filter(is_active=True),
        required=False,
        label=_("Category"),
    )
    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.filter(is_active=True),
        required=False,
        label=_("Document Type"),
    )
    folder = forms.ModelChoiceField(
        queryset=DocumentFolder.objects.filter(is_deleted=False),
        required=False,
        label=_("Folder"),
    )
    status = forms.ChoiceField(
        choices=[("", _("All Statuses"))] + [
            ("DRAFT", _("Draft")),
            ("UPLOADED", _("Uploaded")),
            ("PENDING_REVIEW", _("Pending Review")),
            ("UNDER_REVIEW", _("Under Review")),
            ("RETURNED_FOR_CORRECTION", _("Returned for Correction")),
            ("PENDING_APPROVAL", _("Pending Approval")),
            ("APPROVED", _("Approved")),
            ("PUBLISHED", _("Published")),
            ("ACTIVE", _("Active")),
            ("SUPERSEDED", _("Superseded")),
            ("EXPIRED", _("Expired")),
            ("ARCHIVED", _("Archived")),
        ],
        required=False,
        label=_("Status"),
    )
    confidentiality_level = forms.ChoiceField(
        choices=[("", _("All Levels"))] + ConfidentialityLevel.choices,
        required=False,
        label=_("Confidentiality"),
    )
    sort_by = forms.ChoiceField(
        choices=[
            ("-created_at", _("Newest First")),
            ("created_at", _("Oldest First")),
            ("-updated_at", _("Recently Updated")),
            ("title", _("Title A-Z")),
            ("-title", _("Title Z-A")),
            ("-file_size", _("Largest Files")),
            ("file_size", _("Smallest Files")),
        ],
        required=False,
        initial="-created_at",
        label=_("Sort By"),
    )


# ---------------------------------------------------------------------------
# Folder Forms
# ---------------------------------------------------------------------------


class DocumentFolderForm(forms.ModelForm):
    """Form for creating/editing document folders."""

    class Meta:
        model = DocumentFolder
        fields = ["name", "description", "parent", "sort_order", "confidentiality_level"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


# ---------------------------------------------------------------------------
# Category Forms
# ---------------------------------------------------------------------------


class DocumentCategoryForm(forms.ModelForm):
    """Form for creating/editing document categories."""

    class Meta:
        model = DocumentCategory
        fields = [
            "code",
            "name",
            "description",
            "parent",
            "sort_order",
            "default_confidentiality",
            "default_retention_days",
            "icon",
        ]


# ---------------------------------------------------------------------------
# Document Type Form
# ---------------------------------------------------------------------------


class DocumentTypeForm(forms.ModelForm):
    """Form for creating/editing document types."""

    class Meta:
        model = DocumentType
        fields = [
            "code",
            "name",
            "description",
            "category",
            "requires_approval",
            "requires_versioning",
            "default_confidentiality",
            "default_retention_days",
        ]


# ---------------------------------------------------------------------------
# Tag Form
# ---------------------------------------------------------------------------


class DocumentTagForm(forms.ModelForm):
    """Form for creating/editing document tags."""

    class Meta:
        model = DocumentTag
        fields = ["name", "description", "category"]


# ---------------------------------------------------------------------------
# Retention Category Form
# ---------------------------------------------------------------------------


class RetentionCategoryForm(forms.ModelForm):
    """Form for creating/editing retention categories."""

    class Meta:
        model = RetentionCategory
        fields = [
            "code",
            "name",
            "description",
            "retention_period_days",
            "retention_trigger",
            "disposal_action",
            "supports_legal_hold",
            "requires_review",
            "requires_approval",
        ]


# ---------------------------------------------------------------------------
# Document Hold Form
# ---------------------------------------------------------------------------


class DocumentHoldForm(forms.ModelForm):
    """Form for applying a hold to a document."""

    class Meta:
        model = DocumentHold
        fields = ["hold_type", "reason", "review_date", "restricted_notes"]
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 3}),
            "restricted_notes": forms.Textarea(attrs={"rows": 3}),
            "review_date": forms.DateInput(attrs={"type": "date"}),
        }


# ---------------------------------------------------------------------------
# Document Disposal Request Form
# ---------------------------------------------------------------------------


class DocumentDisposalRequestForm(forms.ModelForm):
    """Form for requesting document disposal."""

    class Meta:
        model = DocumentDisposalRequest
        fields = ["disposal_reason"]
        widgets = {
            "disposal_reason": forms.Textarea(attrs={"rows": 3}),
        }


# ---------------------------------------------------------------------------
# Document Relationship Form
# ---------------------------------------------------------------------------


class DocumentRelationshipForm(forms.ModelForm):
    """Form for creating document relationships."""

    class Meta:
        model = DocumentRelationship
        fields = ["target_document", "relationship_type", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }


# ---------------------------------------------------------------------------
# Bulk Tag Assignment Form
# ---------------------------------------------------------------------------


class BulkTagAssignmentForm(forms.Form):
    """Form for bulk assigning tags to documents."""

    documents = forms.ModelMultipleChoiceField(
        queryset=Document.objects.all(),
        label=_("Documents"),
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=DocumentTag.objects.filter(is_active=True),
        label=_("Tags to Add"),
    )
