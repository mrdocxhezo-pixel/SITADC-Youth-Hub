"""Forms for Review and Approval module (Phase 21)."""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import CommentType, EscalationTrigger, ReviewDecisionType, ReviewerRole


class ReviewCreateForm(forms.Form):
    """Form for creating a new review."""

    report = forms.UUIDField(widget=forms.HiddenInput())
    primary_reviewer = forms.UUIDField(required=False, widget=forms.HiddenInput())
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    checklist = forms.UUIDField(required=False, widget=forms.HiddenInput())
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
    )


class ReviewAssignForm(forms.Form):
    """Form for assigning a reviewer."""

    reviewer = forms.UUIDField(widget=forms.HiddenInput())
    role = forms.ChoiceField(
        choices=ReviewerRole.choices,
        initial=ReviewerRole.PRIMARY,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
    )


class ReviewCommentForm(forms.Form):
    """Form for adding a review comment."""

    body = forms.CharField(
        label=_("Comment"),
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
    )
    comment_type = forms.ChoiceField(
        choices=CommentType.choices,
        initial=CommentType.GENERAL,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    is_internal = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class ReviewDecisionForm(forms.Form):
    """Form for making a review decision."""

    decision = forms.ChoiceField(
        choices=ReviewDecisionType.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    reason = forms.CharField(
        label=_("Decision reason"),
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
    )
    conditions = forms.CharField(
        required=False,
        label=_("Conditions (if applicable)"),
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
    )
    signature_data = forms.CharField(
        required=False,
        label=_("Digital signature"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Type your name to sign",
            }
        ),
    )


class ReviewEscalationForm(forms.Form):
    """Form for escalating a review."""

    trigger = forms.ChoiceField(
        choices=EscalationTrigger.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    reason = forms.CharField(
        label=_("Escalation reason"),
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
    )
    escalated_to = forms.UUIDField(required=False, widget=forms.HiddenInput())


class ReviewDelegationForm(forms.Form):
    """Form for delegating a review."""

    delegated_to = forms.UUIDField(widget=forms.HiddenInput())
    reason = forms.CharField(
        label=_("Delegation reason"),
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
    )
    expires_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"}
        ),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
    )


class ChecklistResponseForm(forms.Form):
    """Form for responding to a checklist item."""

    response_id = forms.UUIDField(widget=forms.HiddenInput())
    is_completed = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    score = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
    )


class ReviewFilterForm(forms.Form):
    """Form for filtering reviews."""

    status = forms.ChoiceField(
        choices=[
            ("", _("All Statuses")),
            ("PENDING_ASSIGNMENT", _("Pending Assignment")),
            ("ASSIGNED", _("Assigned")),
            ("ACCEPTED", _("Accepted")),
            ("UNDER_REVIEW", _("Under Review")),
            ("AWAITING_CLARIFICATION", _("Awaiting Clarification")),
            ("RETURNED_FOR_CORRECTION", _("Returned for Correction")),
            ("RESUBMITTED", _("Resubmitted")),
            ("APPROVED", _("Approved")),
            ("CONDITIONALLY_APPROVED", _("Conditionally Approved")),
            ("REJECTED", _("Rejected")),
            ("ESCALATED", _("Escalated")),
            ("DELEGATED", _("Delegated")),
            ("CLOSED", _("Closed")),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search reviews...",
            }
        ),
    )
