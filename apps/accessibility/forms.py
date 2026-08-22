"""Forms for the Accessibility Review module."""

from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from .constants import (
    AccessibilityCategory,
    AuditType,
    ComplianceStatus,
    FontSizeOption,
    NotificationTimingOption,
    SeverityLevel,
    WCAGLevel,
    WCAGPrinciple,
)
from .models import (
    AccessibilityApproval,
    AccessibilityAudit,
    AccessibilityComplianceRecord,
    AccessibilityConfiguration,
    AccessibilityException,
    AccessibilityFinding,
    AccessibilityIssue,
    AccessibilityPolicy,
    AccessibilityPreference,
    AccessibilityRecommendation,
    AccessibilityStandardRecord,
    WCAGCriterion,
)


class AccessibilityFormMixin:
    """Apply Bootstrap 5 styling and accessible form attributes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            widget = field.widget
            if isinstance(field, forms.DateField):
                field.widget = forms.DateInput(attrs=widget.attrs, format="%Y-%m-%d")
                field.widget.attrs["type"] = "date"
                field.input_formats = ["%Y-%m-%d"]
                widget = field.widget
            if isinstance(field, forms.DateTimeField):
                field.widget = forms.DateTimeInput(attrs=widget.attrs, format="%Y-%m-%dT%H:%M")
                field.widget.attrs["type"] = "datetime-local"
                field.input_formats = ["%Y-%m-%dT%H:%M"]
                widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select | forms.SelectMultiple):
                widget.attrs.setdefault("class", "form-select")
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", "form-control")
                widget.attrs.setdefault("rows", 3)
            else:
                widget.attrs.setdefault("class", "form-control")


class AccessibilityStandardForm(AccessibilityFormMixin, forms.ModelForm):
    class Meta:
        model = AccessibilityStandardRecord
        fields = [
            "name",
            "code",
            "standard_type",
            "version",
            "target_level",
            "description",
            "reference_url",
            "effective_date",
            "review_date",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "effective_date": forms.DateInput(attrs={"type": "date"}),
            "review_date": forms.DateInput(attrs={"type": "date"}),
        }


class AccessibilityPolicyForm(AccessibilityFormMixin, forms.ModelForm):
    class Meta:
        model = AccessibilityPolicy
        fields = [
            "title",
            "standard",
            "category",
            "description",
            "requirements",
            "scope",
            "exceptions",
            "version",
            "approved_by",
            "approved_date",
            "effective_date",
            "review_date",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "requirements": forms.Textarea(attrs={"rows": 4, "placeholder": "One requirement per line or JSON array"}),
            "scope": forms.Textarea(attrs={"rows": 2}),
            "exceptions": forms.Textarea(attrs={"rows": 2}),
            "approved_date": forms.DateInput(attrs={"type": "date"}),
            "effective_date": forms.DateInput(attrs={"type": "date"}),
            "review_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"] = forms.ChoiceField(
            choices=AccessibilityCategory.choices, label=_("Category")
        )


class AccessibilityConfigurationForm(AccessibilityFormMixin, forms.ModelForm):
    class Meta:
        model = AccessibilityConfiguration
        fields = [
            "default_standard",
            "target_wcag_level",
            "enable_high_contrast",
            "enable_font_scaling",
            "enable_reduced_motion",
            "enable_focus_indicators",
            "enable_skip_links",
            "auto_scan_enabled",
            "scan_schedule_cron",
            "scan_modules",
            "notify_on_critical",
            "notify_on_regression",
            "notification_recipients",
            "report_retention_days",
            "include_in_dashboard",
        ]
        widgets = {
            "scan_schedule_cron": forms.TextInput(attrs={"placeholder": "0 2 * * *"}),
            "scan_modules": forms.Textarea(attrs={"rows": 3, "placeholder": '["reports", "dashboard", "documents"]'}),
            "report_retention_days": forms.NumberInput(attrs={"min": 30, "max": 3650}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_wcag_level"] = forms.ChoiceField(
            choices=WCAGLevel.choices, label=_("Target WCAG Level")
        )


class AccessibilityPreferenceForm(AccessibilityFormMixin, forms.ModelForm):
    class Meta:
        model = AccessibilityPreference
        fields = [
            "font_size",
            "custom_font_size_px",
            "colour_theme",
            "high_contrast",
            "reduced_motion",
            "enhanced_focus",
            "keyboard_navigation_enhanced",
            "screen_reader_optimized",
            "notification_timing",
            "preferred_language",
            "reading_line_height",
            "reading_letter_spacing",
            "reading_word_spacing",
            "sync_across_devices",
        ]
        widgets = {
            "custom_font_size_px": forms.NumberInput(attrs={"min": 12, "max": 32}),
            "reading_line_height": forms.NumberInput(attrs={"step": "0.1", "min": "1.0", "max": "3.0"}),
            "reading_letter_spacing": forms.NumberInput(attrs={"step": "0.05", "min": "0", "max": "1"}),
            "reading_word_spacing": forms.NumberInput(attrs={"step": "0.05", "min": "0", "max": "1"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["font_size"] = forms.ChoiceField(
            choices=FontSizeOption.choices, label=_("Font Size")
        )
        self.fields["colour_theme"] = forms.ChoiceField(
            choices=[
                ("SYSTEM", _("System Default")),
                ("LIGHT", _("Light")),
                ("DARK", _("Dark")),
                ("HIGH_CONTRAST_LIGHT", _("High Contrast Light")),
                ("HIGH_CONTRAST_DARK", _("High Contrast Dark")),
                ("SEPIA", _("Sepia")),
                ("CUSTOM", _("Custom")),
            ],
            label=_("Colour Theme"),
        )
        self.fields["notification_timing"] = forms.ChoiceField(
            choices=NotificationTimingOption.choices, label=_("Notification Timing")
        )


class WCAGCriterionForm(AccessibilityFormMixin, forms.ModelForm):
    class Meta:
        model = WCAGCriterion
        fields = [
            "standard",
            "guideline_number",
            "criterion_number",
            "title",
            "description",
            "principle",
            "level",
            "category",
            "understanding_url",
            "techniques_url",
            "how_to_meet_url",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["principle"] = forms.ChoiceField(choices=WCAGPrinciple.choices, label=_("Principle"))
        self.fields["level"] = forms.ChoiceField(choices=WCAGLevel.choices, label=_("Level"))
        self.fields["category"] = forms.ChoiceField(choices=AccessibilityCategory.choices, label=_("Category"))


class AccessibilityAuditForm(AccessibilityFormMixin, forms.ModelForm):
    class Meta:
        model = AccessibilityAudit
        fields = [
            "name",
            "audit_type",
            "scope",
            "module",
            "component",
            "page_url",
            "standard",
            "target_level",
            "auditor",
            "started_at",
            "completed_at",
            "summary",
            "recommendations",
            "report_file",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "recommendations": forms.Textarea(attrs={"rows": 3}),
            "started_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "completed_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["audit_type"] = forms.ChoiceField(choices=AuditType.choices, label=_("Audit Type"))
        self.fields["scope"] = forms.ChoiceField(
            choices=[
                ("MODULE", _("Module")),
                ("COMPONENT", _("Component")),
                ("PAGE", _("Page")),
                ("WORKFLOW", _("Workflow")),
                ("FULL_SITE", _("Full Site")),
            ],
            label=_("Scope"),
        )
        self.fields["target_level"] = forms.ChoiceField(choices=WCAGLevel.choices, label=_("Target Level"))


class AccessibilityFindingForm(AccessibilityFormMixin, forms.ModelForm):
    class Meta:
        model = AccessibilityFinding
        fields = [
            "audit",
            "criterion",
            "component",
            "page_url",
            "description",
            "severity",
            "status",
            "compliance_status",
            "code_snippet",
            "recommended_fix",
            "wcag_technique_ref",
            "assigned_to",
            "due_date",
            "resolution_notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "code_snippet": forms.Textarea(attrs={"rows": 4, "class": "form-control font-monospace"}),
            "recommended_fix": forms.Textarea(attrs={"rows": 3}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["severity"] = forms.ChoiceField(choices=SeverityLevel.choices, label=_("Severity"))
        self.fields["status"] = forms.ChoiceField(
            choices=[
                ("OPEN", _("Open")),
                ("IN_PROGRESS", _("In Progress")),
                ("NEEDS_REVIEW", _("Needs Review")),
                ("VERIFIED", _("Verified Fixed")),
                ("WONT_FIX", _("Won't Fix")),
                ("FALSE_POSITIVE", _("False Positive")),
                ("DEFERRED", _("Deferred")),
            ],
            label=_("Status"),
        )
        self.fields["compliance_status"] = forms.ChoiceField(
            choices=ComplianceStatus.choices, label=_("Compliance Status")
        )


class AccessibilityIssueForm(AccessibilityFormMixin, forms.ModelForm):
    class Meta:
        model = AccessibilityIssue
        fields = [
            "title",
            "source",
            "module",
            "component",
            "page_url",
            "description",
            "steps_to_reproduce",
            "expected_behavior",
            "actual_behavior",
            "severity",
            "criterion",
            "status",
            "assigned_to",
            "due_date",
            "resolution_notes",
            "is_regression",
            "regression_from",
            "tags",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "steps_to_reproduce": forms.Textarea(attrs={"rows": 3}),
            "expected_behavior": forms.Textarea(attrs={"rows": 2}),
            "actual_behavior": forms.Textarea(attrs={"rows": 2}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "tags": forms.Textarea(attrs={"rows": 2, "placeholder": '["form", "keyboard", "contrast"]'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source"] = forms.ChoiceField(
            choices=[
                ("USER_REPORT", _("User Report")),
                ("AUTOMATED_SCAN", _("Automated Scan")),
                ("MANUAL_TESTING", _("Manual Testing")),
                ("REGRESSION", _("Regression")),
                ("EXTERNAL_AUDIT", _("External Audit")),
            ],
            label=_("Source"),
        )
        self.fields["severity"] = forms.ChoiceField(choices=SeverityLevel.choices, label=_("Severity"))
        self.fields["status"] = forms.ChoiceField(
            choices=[
                ("OPEN", _("Open")),
                ("IN_PROGRESS", _("In Progress")),
                ("NEEDS_REVIEW", _("Needs Review")),
                ("VERIFIED", _("Verified Fixed")),
                ("WONT_FIX", _("Won't Fix")),
                ("FALSE_POSITIVE", _("False Positive")),
                ("DEFERRED", _("Deferred")),
            ],
            label=_("Status"),
        )


class AccessibilityRecommendationForm(AccessibilityFormMixin, forms.ModelForm):
    class Meta:
        model = AccessibilityRecommendation
        fields = [
            "title",
            "description",
            "rationale",
            "priority",
            "related_criteria",
            "affected_modules",
            "estimated_effort",
            "implementation_notes",
            "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "rationale": forms.Textarea(attrs={"rows": 2}),
            "implementation_notes": forms.Textarea(attrs={"rows": 3}),
            "affected_modules": forms.Textarea(attrs={"rows": 2, "placeholder": '["reports", "dashboard"]'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["priority"] = forms.ChoiceField(
            choices=[
                ("IMMEDIATE", _("Immediate")),
                ("HIGH", _("High")),
                ("MEDIUM", _("Medium")),
                ("LOW", _("Low")),
                ("FUTURE", _("Future Enhancement")),
            ],
            label=_("Priority"),
        )
        self.fields["status"] = forms.ChoiceField(
            choices=[
                ("OPEN", _("Open")),
                ("IN_PROGRESS", _("In Progress")),
                ("NEEDS_REVIEW", _("Needs Review")),
                ("VERIFIED", _("Verified Fixed")),
                ("WONT_FIX", _("Won't Fix")),
                ("FALSE_POSITIVE", _("False Positive")),
                ("DEFERRED", _("Deferred")),
            ],
            label=_("Status"),
        )


class AccessibilityComplianceRecordForm(AccessibilityFormMixin, forms.ModelForm):
    class Meta:
        model = AccessibilityComplianceRecord
        fields = [
            "module",
            "component",
            "page_url",
            "standard",
            "target_level",
            "compliance_status",
            "last_audit",
            "last_tested",
            "next_review_due",
            "open_findings",
            "critical_findings",
            "notes",
            "exception_granted",
            "exception_reason",
            "exception_expires",
            "exception_approved_by",
        ]
        widgets = {
            "last_tested": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "next_review_due": forms.DateInput(attrs={"type": "date"}),
            "exception_expires": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_level"] = forms.ChoiceField(choices=WCAGLevel.choices, label=_("Target Level"))
        self.fields["compliance_status"] = forms.ChoiceField(choices=ComplianceStatus.choices, label=_("Compliance Status"))


class AccessibilityExceptionForm(AccessibilityFormMixin, forms.ModelForm):
    class Meta:
        model = AccessibilityException
        fields = [
            "module",
            "component",
            "criterion",
            "reason",
            "justification",
            "alternative_provided",
            "approved_by",
            "approved_date",
            "expires_on",
            "is_active",
            "review_notes",
        ]
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 3}),
            "justification": forms.Textarea(attrs={"rows": 3}),
            "alternative_provided": forms.Textarea(attrs={"rows": 2}),
            "approved_date": forms.DateInput(attrs={"type": "date"}),
            "expires_on": forms.DateInput(attrs={"type": "date"}),
        }


class AccessibilityApprovalForm(AccessibilityFormMixin, forms.ModelForm):
    class Meta:
        model = AccessibilityApproval
        fields = [
            "approval_type",
            "reference_number",
            "title",
            "description",
            "requested_by",
            "approved_by",
            "status",
            "decision_notes",
            "conditions",
            "expires_on",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "decision_notes": forms.Textarea(attrs={"rows": 2}),
            "conditions": forms.Textarea(attrs={"rows": 2}),
            "expires_on": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["approval_type"] = forms.ChoiceField(
            choices=[
                ("AUDIT_REPORT", _("Audit Report")),
                ("POLICY", _("Policy")),
                ("EXCEPTION", _("Exception")),
                ("RELEASE", _("Release Sign-off")),
                ("CONFIGURATION", _("Configuration Change")),
            ],
            label=_("Approval Type"),
        )
        self.fields["status"] = forms.ChoiceField(
            choices=[
                ("PENDING", _("Pending")),
                ("APPROVED", _("Approved")),
                ("REJECTED", _("Rejected")),
                ("REVISION_REQUESTED", _("Revision Requested")),
            ],
            label=_("Status"),
        )
