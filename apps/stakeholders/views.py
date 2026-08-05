"""Permission-aware, service-backed stakeholder management views."""

from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path
from typing import Any, ClassVar

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models
from django.db.models import Count, Q, Sum
from django.http import FileResponse, Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from apps.rbac.authorization import user_has_permission
from apps.rbac.mixins import PermissionRequiredMixin

from .constants import (
    ActionStatus,
    AgreementStatus,
    CommitmentStatus,
    ContributionStatus,
    EngagementStatus,
    ReferenceDataKind,
    ReviewStatus,
    RiskStatus,
    StakeholderStatus,
)
from .exports import stakeholder_register_csv_response
from .forms import (
    ActionStatusForm,
    AgreementRenewalDecisionForm,
    AgreementRenewalRequestForm,
    AgreementTransitionForm,
    AgreementVersionForm,
    CommitmentProgressForm,
    EngagementCompletionForm,
    NoteVersionForm,
    StakeholderActionForm,
    StakeholderAgreementForm,
    StakeholderArchiveForm,
    StakeholderAssessmentForm,
    StakeholderCommitmentForm,
    StakeholderCommunicationForm,
    StakeholderConflictForm,
    StakeholderContactForm,
    StakeholderContributionForm,
    StakeholderDocumentForm,
    StakeholderDueDiligenceForm,
    StakeholderEngagementForm,
    StakeholderEngagementPlanForm,
    StakeholderForm,
    StakeholderNoteForm,
    StakeholderPerformanceForm,
    StakeholderRiskForm,
    StakeholderStatusTransitionForm,
)
from .models import (
    Stakeholder,
    StakeholderActionItem,
    StakeholderAgreement,
    StakeholderAgreementRenewal,
    StakeholderAgreementVersion,
    StakeholderAssessment,
    StakeholderCommitment,
    StakeholderContact,
    StakeholderContribution,
    StakeholderDocument,
    StakeholderEngagement,
    StakeholderNote,
    StakeholderPerformanceReview,
    StakeholderReferenceData,
    StakeholderRisk,
)
from .permissions import (
    PARTNERS_ANALYTICS,
    PARTNERS_APPROVE_AGREEMENTS,
    PARTNERS_ARCHIVE,
    PARTNERS_ASSESS,
    PARTNERS_CREATE,
    PARTNERS_EXPORT,
    PARTNERS_MANAGE,
    PARTNERS_MANAGE_ACTIONS,
    PARTNERS_MANAGE_AGREEMENTS,
    PARTNERS_MANAGE_COMMITMENTS,
    PARTNERS_MANAGE_COMMUNICATIONS,
    PARTNERS_MANAGE_CONTACTS,
    PARTNERS_MANAGE_CONTRIBUTIONS,
    PARTNERS_MANAGE_DOCUMENTS,
    PARTNERS_MANAGE_DUE_DILIGENCE,
    PARTNERS_MANAGE_ENGAGEMENTS,
    PARTNERS_MANAGE_NOTES,
    PARTNERS_MANAGE_PERFORMANCE,
    PARTNERS_MANAGE_RISK,
    PARTNERS_RESTORE,
    PARTNERS_REVIEW_AGREEMENTS,
    PARTNERS_UPDATE,
    PARTNERS_VIEW,
    PARTNERS_VIEW_CONFIDENTIAL,
    PARTNERS_VIEW_DIRECTORY,
    PARTNERS_VIEW_DUE_DILIGENCE,
    PARTNERS_VIEW_FINANCIAL,
    PARTNERS_VIEW_PRIVATE_CONTACTS,
    PARTNERS_VIEW_PROFILE,
)
from .selectors import (
    visible_stakeholder_contacts,
    visible_stakeholder_documents,
    visible_stakeholders,
)
from .services import (
    StakeholderActionService,
    StakeholderAgreementService,
    StakeholderAssessmentService,
    StakeholderCommitmentService,
    StakeholderCommunicationService,
    StakeholderContactService,
    StakeholderContributionService,
    StakeholderDocumentService,
    StakeholderDueDiligenceService,
    StakeholderEngagementService,
    StakeholderNoteService,
    StakeholderPerformanceService,
    StakeholderRiskService,
    StakeholderService,
)

logger = logging.getLogger(__name__)


def _can(user, *permission_codes: str) -> bool:
    return bool(
        user_has_permission(user, PARTNERS_MANAGE)
        or any(user_has_permission(user, code) for code in permission_codes)
    )


def _can_view_financial(user) -> bool:
    return _can(
        user,
        PARTNERS_VIEW_FINANCIAL,
        PARTNERS_MANAGE_CONTRIBUTIONS,
        PARTNERS_MANAGE_COMMITMENTS,
        PARTNERS_MANAGE_AGREEMENTS,
    )


def _can_view_risk(user) -> bool:
    return _can(user, PARTNERS_VIEW_CONFIDENTIAL, PARTNERS_MANAGE_RISK)


def _can_view_notes(user) -> bool:
    return _can(user, PARTNERS_VIEW_CONFIDENTIAL, PARTNERS_MANAGE_NOTES)


def _apply_service_errors(form, exc: ValidationError) -> None:
    if hasattr(exc, "message_dict"):
        for field_name, field_messages in exc.message_dict.items():
            target = field_name if field_name in form.fields else None
            for message in field_messages:
                form.add_error(target, message)
        return
    for message in exc.messages:
        form.add_error(None, message)


def _scoped_stakeholder(user, pk, *, include_archived: bool = False) -> Stakeholder:
    return get_object_or_404(
        visible_stakeholders(user, include_archived=include_archived), pk=pk
    )


def _scoped_related(model, user, pk, relation: str = "stakeholder"):
    return get_object_or_404(
        model.objects.filter(
            **{f"{relation}__in": visible_stakeholders(user, include_archived=True)}
        ),
        pk=pk,
    )


class StakeholderPermissionMixin(PermissionRequiredMixin):
    """Allow any listed operation permission, with module-manager override."""

    any_permission = True

    def test_func(self) -> bool:
        required = self.permission_required
        permissions = (required,) if isinstance(required, str) else tuple(required)
        return _can(self.request.user, *permissions)


class StakeholderDashboardView(StakeholderPermissionMixin, TemplateView):
    template_name = "stakeholders/dashboard.html"
    permission_required = (PARTNERS_VIEW, PARTNERS_VIEW_DIRECTORY)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stakeholders = visible_stakeholders(self.request.user)
        today = timezone.localdate()
        metrics = stakeholders.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(status=StakeholderStatus.ACTIVE)),
            prospects=Count(
                "id",
                filter=Q(
                    status__in=[
                        StakeholderStatus.PROSPECT,
                        StakeholderStatus.IDENTIFIED,
                        StakeholderStatus.UNDER_ASSESSMENT,
                    ]
                ),
            ),
        )
        status_summary = list(
            stakeholders.values("status").annotate(total=Count("id")).order_by("status")
        )
        context.update(
            {
                "metrics": metrics,
                "status_summary": status_summary,
                "recent_stakeholders": stakeholders.order_by("-created_at")[:6],
                "expiring_agreements": StakeholderAgreement.objects.filter(
                    stakeholder__in=stakeholders,
                    status=AgreementStatus.ACTIVE,
                    expiry_date__gte=today,
                    expiry_date__lte=today + timedelta(days=60),
                ).count(),
                "overdue_actions": StakeholderActionItem.objects.filter(
                    stakeholder__in=stakeholders,
                    due_date__lt=today,
                    status__in=[
                        ActionStatus.OPEN,
                        ActionStatus.IN_PROGRESS,
                        ActionStatus.BLOCKED,
                        ActionStatus.OVERDUE,
                    ],
                ).count(),
                "can_create": _can(self.request.user, PARTNERS_CREATE),
                "has_granular_analytics": _can(self.request.user, PARTNERS_ANALYTICS),
            }
        )
        if _can(self.request.user, PARTNERS_ANALYTICS):
            context["category_summary"] = list(
                StakeholderReferenceData.objects.filter(
                    kind=ReferenceDataKind.CATEGORY,
                    category_stakeholders__in=stakeholders,
                )
                .values("name")
                .annotate(total=Count("category_stakeholders", distinct=True))
                .order_by("name")
            )
            context["region_summary"] = list(
                stakeholders.exclude(province_or_region="")
                .values("province_or_region")
                .annotate(total=Count("id"))
                .order_by("province_or_region")
            )
        if _can_view_financial(self.request.user):
            context["verified_contribution_total"] = (
                StakeholderContribution.objects.filter(
                    stakeholder__in=stakeholders,
                    status=ContributionStatus.VERIFIED,
                    amount__isnull=False,
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )
        if _can_view_risk(self.request.user):
            context["open_risks"] = StakeholderRisk.objects.filter(
                stakeholder__in=stakeholders,
                status__in=[RiskStatus.OPEN, RiskStatus.MONITORING],
            ).count()
        return context


class StakeholderDirectoryView(StakeholderPermissionMixin, ListView):
    model = Stakeholder
    template_name = "stakeholders/directory.html"
    context_object_name = "stakeholders"
    paginate_by = 24
    permission_required = (PARTNERS_VIEW, PARTNERS_VIEW_DIRECTORY)
    directory_title = "Stakeholder directory"
    directory_description = "Permission-scoped organizational relationship records."
    specialized_filter = Q()
    route_name = "stakeholders:directory"

    SORTS: ClassVar[dict[str, tuple[str, ...]]] = {
        "name": ("legal_name",),
        "name_desc": ("-legal_name",),
        "reference": ("reference_number",),
        "status": ("status", "legal_name"),
        "region": ("province_or_region", "legal_name"),
        "recent": ("-created_at",),
    }

    def get_queryset(self):
        queryset = (
            visible_stakeholders(self.request.user)
            .filter(self.specialized_filter)
            .prefetch_related("categories", "sectors")
        )
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(reference_number__icontains=search)
                | Q(legal_name__icontains=search)
                | Q(trading_name__icontains=search)
                | Q(display_name__icontains=search)
                | Q(acronym__icontains=search)
            )
        status = self.request.GET.get("status", "")
        if status in StakeholderStatus.values:
            queryset = queryset.filter(status=status)
        entity_type = self.request.GET.get("entity_type", "")
        if entity_type in dict(
            Stakeholder._meta.get_field("entity_type").choices or ()
        ):
            queryset = queryset.filter(entity_type=entity_type)
        category = self.request.GET.get("category", "").strip()
        if category:
            queryset = queryset.filter(categories__code=category)
        relationship_type = self.request.GET.get("relationship_type", "").strip()
        if relationship_type:
            queryset = queryset.filter(relationship_type__code=relationship_type)
        region = self.request.GET.get("region", "").strip()
        if region:
            queryset = queryset.filter(province_or_region__icontains=region)
        ordering = self.SORTS.get(
            self.request.GET.get("sort", "name"), self.SORTS["name"]
        )
        return queryset.distinct().order_by(*ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop("page", None)
        context.update(
            {
                "directory_title": self.directory_title,
                "directory_description": self.directory_description,
                "route_name": self.route_name,
                "status_choices": StakeholderStatus.choices,
                "entity_type_choices": Stakeholder._meta.get_field(
                    "entity_type"
                ).choices,
                "categories": StakeholderReferenceData.objects.filter(
                    kind=ReferenceDataKind.CATEGORY, active=True
                ),
                "relationship_types": StakeholderReferenceData.objects.filter(
                    kind=ReferenceDataKind.TYPE, active=True
                ),
                "sort_choices": (
                    ("name", "Name A-Z"),
                    ("name_desc", "Name Z-A"),
                    ("reference", "Reference"),
                    ("status", "Status"),
                    ("region", "Region"),
                    ("recent", "Recently added"),
                ),
                "display_mode": (
                    "cards" if self.request.GET.get("view") == "cards" else "table"
                ),
                "query_without_page": query.urlencode(),
                "can_create": _can(self.request.user, PARTNERS_CREATE),
            }
        )
        return context


class PartnerDirectoryView(StakeholderDirectoryView):
    directory_title = "Partner directory"
    directory_description = "Strategic, technical, funding, and delivery partners."
    route_name = "stakeholders:partners"
    specialized_filter = Q(relationship_type__isnull=False) | Q(
        categories__code="development-partner"
    )


class DonorDirectoryView(StakeholderDirectoryView):
    directory_title = "Donor directory"
    directory_description = "Stakeholders classified as donors or funding partners."
    route_name = "stakeholders:donors"
    specialized_filter = Q(categories__code="donor") | Q(
        relationship_type__code="funding"
    )


class SponsorDirectoryView(StakeholderDirectoryView):
    directory_title = "Sponsor directory"
    directory_description = (
        "Organizations and individuals with sponsorship relationships."
    )
    route_name = "stakeholders:sponsors"
    specialized_filter = Q(categories__code="sponsor")


class GovernmentDirectoryView(StakeholderDirectoryView):
    directory_title = "Government directory"
    directory_description = (
        "Government institutions and government relationship partners."
    )
    route_name = "stakeholders:government"
    specialized_filter = Q(categories__code="government") | Q(
        relationship_type__code="government"
    )


class CommunityDirectoryView(StakeholderDirectoryView):
    directory_title = "Community directory"
    directory_description = "Community-based, faith-based, and community partners."
    route_name = "stakeholders:community"
    specialized_filter = (
        Q(categories__code__in=["cbo", "fbo"])
        | Q(relationship_type__code="community")
        | Q(classification__code="community")
    )


class StakeholderCreateView(StakeholderPermissionMixin, FormView):
    form_class = StakeholderForm
    template_name = "stakeholders/stakeholder_form.html"
    permission_required = PARTNERS_CREATE

    def form_valid(self, form):
        try:
            stakeholder = StakeholderService(user=self.request.user).create(
                **form.cleaned_data
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Stakeholder {stakeholder.reference_number} created successfully.",
        )
        return redirect("stakeholders:profile", pk=stakeholder.pk)


class StakeholderUpdateView(StakeholderPermissionMixin, FormView):
    form_class = StakeholderForm
    template_name = "stakeholders/stakeholder_form.html"
    permission_required = PARTNERS_UPDATE

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = _scoped_stakeholder(self.request.user, self.kwargs["pk"])
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def form_valid(self, form):
        try:
            stakeholder = StakeholderService(user=self.request.user).update(
                self.get_object(), **form.cleaned_data
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Stakeholder profile updated successfully.")
        return redirect("stakeholders:profile", pk=stakeholder.pk)


class StakeholderProfileView(StakeholderPermissionMixin, DetailView):
    model = Stakeholder
    template_name = "stakeholders/profile.html"
    context_object_name = "stakeholder"
    permission_required = (PARTNERS_VIEW_PROFILE, PARTNERS_VIEW)

    def get_queryset(self):
        return visible_stakeholders(self.request.user).prefetch_related(
            "categories", "sectors", "focus_areas", "sdgs"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stakeholder = self.object
        user = self.request.user
        can_contacts = _can(
            user, PARTNERS_VIEW_PRIVATE_CONTACTS, PARTNERS_MANAGE_CONTACTS
        )
        can_financial = _can_view_financial(user)
        can_due_diligence = _can(
            user, PARTNERS_VIEW_DUE_DILIGENCE, PARTNERS_MANAGE_DUE_DILIGENCE
        )
        can_risk = _can_view_risk(user)
        can_notes = _can_view_notes(user)
        can_documents = _can(user, PARTNERS_MANAGE_DOCUMENTS)
        agreements = StakeholderAgreement.objects.filter(stakeholder=stakeholder)
        if not can_financial:
            agreements = agreements.defer("financial_value", "in_kind_value")
        context.update(
            {
                "status_history": stakeholder.status_history.select_related(
                    "changed_by"
                )[:8],
                "recent_engagements": stakeholder.engagements.select_related(
                    "responsible_officer"
                )[:6],
                "engagement_plans": stakeholder.engagement_plans.select_related(
                    "engagement_level", "responsible_officer"
                )[:5],
                "assessments": stakeholder.assessments.all()[:5],
                "agreements": agreements[:5],
                "action_items": stakeholder.action_items.select_related("assigned_to")[
                    :6
                ],
                "performance_reviews": stakeholder.performance_reviews.all()[:5],
                "can_update": _can(user, PARTNERS_UPDATE),
                "can_archive": _can(user, PARTNERS_ARCHIVE),
                "can_contacts": can_contacts,
                "can_financial": can_financial,
                "can_due_diligence": can_due_diligence,
                "can_risk": can_risk,
                "can_notes": can_notes,
                "can_documents": can_documents,
            }
        )
        if can_contacts:
            context["contacts"] = visible_stakeholder_contacts(user, stakeholder)[:5]
        if can_financial:
            context["contributions"] = stakeholder.contributions.select_related(
                "contribution_type"
            )[:5]
            context["commitments"] = stakeholder.commitments.all()[:5]
        if can_due_diligence:
            context["due_diligence_reviews"] = stakeholder.due_diligence_reviews.all()[
                :5
            ]
        if can_risk:
            context["risks"] = stakeholder.risks.select_related("category")[:5]
            context["conflicts"] = stakeholder.conflicts_of_interest.all()[:5]
        if can_notes:
            context["notes"] = stakeholder.stakeholder_notes.all()[:5]
        if can_documents:
            context["documents"] = visible_stakeholder_documents(user, stakeholder)[:5]
        return context


class StakeholderStatusView(StakeholderPermissionMixin, FormView):
    form_class = StakeholderStatusTransitionForm
    template_name = "stakeholders/workflow_form.html"
    permission_required = PARTNERS_UPDATE

    def get_stakeholder(self):
        if not hasattr(self, "stakeholder"):
            self.stakeholder = _scoped_stakeholder(self.request.user, self.kwargs["pk"])
        return self.stakeholder

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["stakeholder"] = self.get_stakeholder()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Change stakeholder status",
                "stakeholder": self.get_stakeholder(),
                "cancel_url": reverse(
                    "stakeholders:profile", kwargs={"pk": self.get_stakeholder().pk}
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            StakeholderService(user=self.request.user).change_status(
                self.get_stakeholder(),
                form.cleaned_data["new_status"],
                form.cleaned_data["reason"],
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Stakeholder status updated.")
        return redirect("stakeholders:profile", pk=self.get_stakeholder().pk)


class StakeholderArchiveView(StakeholderPermissionMixin, FormView):
    form_class = StakeholderArchiveForm
    template_name = "stakeholders/workflow_form.html"
    permission_required = PARTNERS_ARCHIVE

    def get_stakeholder(self):
        return _scoped_stakeholder(self.request.user, self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Archive stakeholder",
                "stakeholder": self.get_stakeholder(),
                "cancel_url": reverse(
                    "stakeholders:profile", kwargs={"pk": self.get_stakeholder().pk}
                ),
            }
        )
        return context

    def form_valid(self, form):
        StakeholderService(user=self.request.user).archive(
            self.get_stakeholder(), form.cleaned_data["reason"]
        )
        messages.success(self.request, "Stakeholder archived.")
        return redirect("stakeholders:directory")


class StakeholderRestoreView(StakeholderPermissionMixin, FormView):
    form_class = StakeholderArchiveForm
    template_name = "stakeholders/workflow_form.html"
    permission_required = PARTNERS_RESTORE

    def get_stakeholder(self):
        return _scoped_stakeholder(
            self.request.user, self.kwargs["pk"], include_archived=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Restore stakeholder",
                "stakeholder": self.get_stakeholder(),
                "cancel_url": reverse("stakeholders:directory"),
            }
        )
        return context

    def form_valid(self, form):
        stakeholder = StakeholderService(user=self.request.user).restore(
            self.get_stakeholder(), form.cleaned_data["reason"]
        )
        messages.success(self.request, "Stakeholder restored as inactive.")
        return redirect("stakeholders:profile", pk=stakeholder.pk)


class MappingMatrixView(StakeholderPermissionMixin, ListView):
    model = StakeholderAssessment
    template_name = "stakeholders/mapping_matrix.html"
    context_object_name = "assessments"
    paginate_by = 30
    permission_required = (PARTNERS_VIEW_PROFILE, PARTNERS_VIEW, PARTNERS_ASSESS)

    def get_queryset(self):
        queryset = StakeholderAssessment.objects.filter(
            stakeholder__in=visible_stakeholders(self.request.user)
        ).select_related("stakeholder", "assessed_by")
        classification = self.request.GET.get("classification", "")
        valid = dict(
            StakeholderAssessment._meta.get_field("classification").choices or ()
        )
        if classification in valid:
            queryset = queryset.filter(classification=classification)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop("page", None)
        context.update(
            {
                "classification_choices": StakeholderAssessment._meta.get_field(
                    "classification"
                ).choices,
                "classification_summary": list(
                    self.get_queryset()
                    .values("classification")
                    .annotate(total=Count("id"))
                    .order_by("classification")
                ),
                "query_without_page": query.urlencode(),
            }
        )
        return context


class StakeholderRelatedView(StakeholderPermissionMixin, TemplateView):
    """Render and create one scoped related-record collection."""

    template_name = "stakeholders/related_records.html"
    permission_required: str | tuple[str, ...] = (
        PARTNERS_VIEW_PROFILE,
        PARTNERS_VIEW,
    )
    write_permission = ""
    form_class: ClassVar[type[forms.BaseForm] | None] = None
    route_name = ""
    title = "Related records"
    description = ""
    columns: tuple[str, ...] = ()

    def get_stakeholder(self):
        if not hasattr(self, "stakeholder"):
            self.stakeholder = _scoped_stakeholder(
                self.request.user, self.kwargs["pk"], include_archived=True
            )
        return self.stakeholder

    def can_write(self):
        return bool(
            self.write_permission and _can(self.request.user, self.write_permission)
        )

    def get_form_kwargs(self):
        return {}

    def get_form(self, data=None, files=None):
        if not self.can_write() or self.form_class is None:
            return None
        return self.form_class(data, files, **self.get_form_kwargs())

    def get_rows(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def perform_service(self, cleaned_data: dict):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "stakeholder": self.get_stakeholder(),
                "title": self.title,
                "description": self.description,
                "columns": self.columns,
                "rows": self.get_rows(),
                "form": kwargs.get("form") or self.get_form(),
                "can_write": self.can_write(),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        if not self.can_write():
            raise PermissionDenied
        form = self.get_form(request.POST, request.FILES)
        if form is None:
            raise PermissionDenied
        if form.is_valid():
            try:
                self.perform_service(form.cleaned_data.copy())
            except ValidationError as exc:
                _apply_service_errors(form, exc)
            else:
                messages.success(request, "Record created successfully.")
                return redirect(self.route_name, pk=self.get_stakeholder().pk)
        return self.render_to_response(self.get_context_data(form=form))


class StakeholderContactsView(StakeholderRelatedView):
    permission_required = (PARTNERS_VIEW_PRIVATE_CONTACTS, PARTNERS_MANAGE_CONTACTS)
    write_permission = PARTNERS_MANAGE_CONTACTS
    form_class = StakeholderContactForm
    route_name = "stakeholders:contacts"
    title = "Private contacts"
    description = "Authorized contact-person records and communication preferences."
    columns = ("Name", "Contact", "Role", "Validity", "Status")

    def get_rows(self):
        rows = []
        for contact in visible_stakeholder_contacts(
            self.request.user, self.get_stakeholder()
        ):
            actions = []
            if self.can_write() and contact.is_active and not contact.is_primary:
                actions.append(
                    {
                        "url": reverse(
                            "stakeholders:contact_primary",
                            kwargs={"contact_pk": contact.pk},
                        ),
                        "label": "Set primary",
                        "style": "outline-primary",
                    }
                )
            if self.can_write() and contact.is_active:
                actions.append(
                    {
                        "url": reverse(
                            "stakeholders:contact_deactivate",
                            kwargs={"contact_pk": contact.pk},
                        ),
                        "label": "Deactivate",
                        "style": "outline-danger",
                    }
                )
            rows.append(
                {
                    "cells": [
                        contact.full_name,
                        contact.email
                        or contact.phone_primary
                        or contact.phone_secondary,
                        contact.designation or contact.title or contact.department,
                        f"{contact.valid_from} to {contact.valid_to or 'current'}",
                        (
                            "Primary"
                            if contact.is_primary
                            else ("Active" if contact.is_active else "Inactive")
                        ),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        StakeholderContactService(user=self.request.user).create(
            self.get_stakeholder(), **cleaned_data
        )


class StakeholderAssessmentsView(StakeholderRelatedView):
    write_permission = PARTNERS_ASSESS
    form_class = StakeholderAssessmentForm
    route_name = "stakeholders:assessments"
    title = "Assessments"
    description = "Power-interest mapping and complete relationship score evidence."
    columns = ("Reference", "Date", "Influence", "Interest", "Matrix", "Complete")

    def get_rows(self):
        return [
            {
                "cells": [
                    item.reference_number,
                    item.assessment_date,
                    (
                        item.influence_score
                        if item.influence_score is not None
                        else "Missing"
                    ),
                    (
                        item.interest_score
                        if item.interest_score is not None
                        else "Missing"
                    ),
                    item.get_classification_display(),
                    f"{item.completeness_percentage}%",
                ]
            }
            for item in self.get_stakeholder().assessments.all()
        ]

    def perform_service(self, cleaned_data):
        StakeholderAssessmentService(user=self.request.user).record(
            self.get_stakeholder(), **cleaned_data
        )


class StakeholderEngagementPlansView(StakeholderRelatedView):
    write_permission = PARTNERS_MANAGE_ENGAGEMENTS
    form_class = StakeholderEngagementPlanForm
    route_name = "stakeholders:engagement_plans"
    title = "Engagement plans"
    description = (
        "Time-bound strategies, outcomes, review points, and accountable officers."
    )
    columns = ("Plan", "Level", "Period", "Responsible officer", "Status")

    def get_rows(self):
        queryset = self.get_stakeholder().engagement_plans.select_related(
            "engagement_level", "responsible_officer"
        )
        return [
            {
                "cells": [
                    plan.title,
                    plan.engagement_level.name,
                    f"{plan.start_date} to {plan.end_date or 'open'}",
                    plan.responsible_officer or "Unassigned",
                    plan.get_status_display(),
                ]
            }
            for plan in queryset
        ]

    def perform_service(self, cleaned_data):
        StakeholderEngagementService(user=self.request.user).create_plan(
            self.get_stakeholder(), **cleaned_data
        )


class StakeholderEngagementsView(StakeholderRelatedView):
    write_permission = PARTNERS_MANAGE_ENGAGEMENTS
    form_class = StakeholderEngagementForm
    route_name = "stakeholders:engagements"
    title = "Engagements"
    description = "Meetings, consultations, visits, events, and their outcomes."
    columns = ("Reference", "Engagement", "Scheduled", "Officer", "Status")

    def get_form_kwargs(self):
        return {"stakeholder": self.get_stakeholder()}

    def get_rows(self):
        queryset = self.get_stakeholder().engagements.select_related(
            "responsible_officer"
        )
        rows = []
        for engagement in queryset:
            actions = []
            if self.can_write() and engagement.status == EngagementStatus.PLANNED:
                actions.append(
                    {
                        "url": reverse(
                            "stakeholders:engagement_complete",
                            kwargs={"engagement_pk": engagement.pk},
                        ),
                        "label": "Complete",
                        "style": "outline-success",
                        "link": True,
                    }
                )
            rows.append(
                {
                    "cells": [
                        engagement.reference_number,
                        engagement.title,
                        engagement.scheduled_at,
                        engagement.responsible_officer or "Unassigned",
                        engagement.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        StakeholderEngagementService(user=self.request.user).record(
            self.get_stakeholder(), **cleaned_data
        )


class StakeholderCommunicationsView(StakeholderRelatedView):
    write_permission = PARTNERS_MANAGE_COMMUNICATIONS
    form_class = StakeholderCommunicationForm
    route_name = "stakeholders:communications"
    title = "Communications"
    description = "Inbound, outbound, and internal relationship communication history."
    columns = ("Occurred", "Subject", "Channel", "Direction", "Follow-up")

    def get_form_kwargs(self):
        return {
            "stakeholder": self.get_stakeholder(),
            "can_view_private_contacts": _can(
                self.request.user,
                PARTNERS_VIEW_PRIVATE_CONTACTS,
                PARTNERS_MANAGE_CONTACTS,
            ),
        }

    def get_rows(self):
        return [
            {
                "cells": [
                    item.occurred_at,
                    item.subject,
                    item.get_channel_display(),
                    item.get_direction_display(),
                    (
                        item.follow_up_due_date
                        if item.requires_follow_up
                        else "Not required"
                    ),
                ]
            }
            for item in self.get_stakeholder().communications.all()
        ]

    def perform_service(self, cleaned_data):
        StakeholderCommunicationService(user=self.request.user).record(
            self.get_stakeholder(), **cleaned_data
        )


class StakeholderCommitmentsView(StakeholderRelatedView):
    write_permission = PARTNERS_MANAGE_COMMITMENTS
    form_class = StakeholderCommitmentForm
    route_name = "stakeholders:commitments"
    title = "Commitments"
    description = "Dated obligations, owners, progress, and completion evidence."
    columns = ("Reference", "Commitment", "Responsible party", "Due", "Progress")

    def get_rows(self):
        can_financial = _can_view_financial(self.request.user)
        queryset = self.get_stakeholder().commitments.all()
        if not can_financial:
            queryset = queryset.defer(
                "expected_value", "actual_value", "in_kind_details"
            )
        rows = []
        for item in queryset:
            actions = []
            if self.can_write() and item.status not in {
                CommitmentStatus.COMPLETED,
                CommitmentStatus.CANCELLED,
            }:
                actions.append(
                    {
                        "url": reverse(
                            "stakeholders:commitment_progress",
                            kwargs={"commitment_pk": item.pk},
                        ),
                        "label": "Update progress",
                        "style": "outline-primary",
                        "link": True,
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.reference_number,
                        item.title,
                        item.responsible_party,
                        item.due_date,
                        f"{item.progress_percentage}% - {item.get_status_display()}",
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        StakeholderCommitmentService(user=self.request.user).create(
            self.get_stakeholder(), **cleaned_data
        )


class StakeholderContributionsView(StakeholderRelatedView):
    permission_required = (PARTNERS_VIEW_FINANCIAL, PARTNERS_MANAGE_CONTRIBUTIONS)
    write_permission = PARTNERS_MANAGE_CONTRIBUTIONS
    form_class = StakeholderContributionForm
    route_name = "stakeholders:contributions"
    title = "Contributions"
    description = (
        "Restricted financial, in-kind, technical, and advisory support records."
    )
    columns = ("Reference", "Date", "Type", "Value", "Status")

    def get_rows(self):
        rows = []
        queryset = self.get_stakeholder().contributions.select_related(
            "contribution_type"
        )
        for item in queryset:
            actions = []
            if self.can_write() and item.status in {
                ContributionStatus.PLEDGED,
                ContributionStatus.RECEIVED,
            }:
                actions.append(
                    {
                        "url": reverse(
                            "stakeholders:contribution_verify",
                            kwargs={"contribution_pk": item.pk},
                        ),
                        "label": "Verify",
                        "style": "outline-success",
                    }
                )
            value = item.amount if item.amount is not None else item.estimated_value
            if value is None:
                value = f"{item.quantity or 0} {item.unit}".strip()
            else:
                value = f"{item.currency} {value}"
            rows.append(
                {
                    "cells": [
                        item.reference_number,
                        item.contribution_date,
                        item.contribution_type.name,
                        value,
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        StakeholderContributionService(user=self.request.user).record(
            self.get_stakeholder(), **cleaned_data
        )


class StakeholderAgreementsView(StakeholderRelatedView):
    template_name = "stakeholders/agreements.html"
    write_permission = PARTNERS_MANAGE_AGREEMENTS
    form_class = StakeholderAgreementForm
    route_name = "stakeholders:agreements"
    title = "Agreements"
    description = (
        "Formal agreements, immutable versions, review, approval, and renewal."
    )

    def get_rows(self):
        can_financial = _can_view_financial(self.request.user)
        queryset = self.get_stakeholder().agreements.select_related("agreement_type")
        if not can_financial:
            queryset = queryset.defer("financial_value", "in_kind_value")
        rows = []
        for agreement in queryset:
            actions = []
            if _can(
                self.request.user,
                PARTNERS_MANAGE_AGREEMENTS,
                PARTNERS_REVIEW_AGREEMENTS,
                PARTNERS_APPROVE_AGREEMENTS,
            ):
                actions.append(
                    {
                        "url": reverse(
                            "stakeholders:agreement_transition",
                            kwargs={"agreement_pk": agreement.pk},
                        ),
                        "label": "Transition",
                    }
                )
            if self.can_write() and agreement.status in {
                AgreementStatus.DRAFT,
                AgreementStatus.UNDER_REVIEW,
            }:
                actions.append(
                    {
                        "url": reverse(
                            "stakeholders:agreement_version_add",
                            kwargs={"agreement_pk": agreement.pk},
                        ),
                        "label": "Add version",
                    }
                )
            if self.can_write() and agreement.status in {
                AgreementStatus.ACTIVE,
                AgreementStatus.EXPIRED,
            }:
                actions.append(
                    {
                        "url": reverse(
                            "stakeholders:renewal_request",
                            kwargs={"agreement_pk": agreement.pk},
                        ),
                        "label": "Request renewal",
                    }
                )
            versions = [
                {
                    "number": version.version_number,
                    "download_url": (
                        reverse(
                            "stakeholders:agreement_version_download",
                            kwargs={"version_pk": version.pk},
                        )
                        if version.file
                        and _can(
                            self.request.user,
                            PARTNERS_MANAGE_AGREEMENTS,
                            PARTNERS_MANAGE_DOCUMENTS,
                        )
                        else ""
                    ),
                }
                for version in agreement.versions.all()
            ]
            rows.append(
                {
                    "agreement": agreement,
                    "actions": actions,
                    "versions": versions,
                    "financial_value": (
                        f"{agreement.currency} {agreement.financial_value}"
                        if can_financial and agreement.financial_value is not None
                        else None
                    ),
                }
            )
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        renewals = StakeholderAgreementRenewal.objects.filter(
            agreement__stakeholder=self.get_stakeholder()
        ).select_related("agreement", "decided_by")
        context.update(
            {
                "agreement_rows": context.pop("rows"),
                "renewals": renewals,
                "can_decide_renewal": self.can_write(),
                "can_view_financial": _can_view_financial(self.request.user),
            }
        )
        return context

    def perform_service(self, cleaned_data):
        StakeholderAgreementService(user=self.request.user).create(
            self.get_stakeholder(), **cleaned_data
        )


class StakeholderDueDiligenceView(StakeholderRelatedView):
    permission_required = (
        PARTNERS_VIEW_DUE_DILIGENCE,
        PARTNERS_MANAGE_DUE_DILIGENCE,
    )
    write_permission = PARTNERS_MANAGE_DUE_DILIGENCE
    form_class = StakeholderDueDiligenceForm
    route_name = "stakeholders:due_diligence"
    title = "Due diligence"
    description = "Restricted legal, financial, safeguarding, and compliance reviews."
    columns = ("Reference", "Review date", "Expiry", "Status", "Recommendation")

    def get_form_kwargs(self):
        return {"reviewer": self.request.user}

    def get_rows(self):
        return [
            {
                "cells": [
                    item.reference_number,
                    item.review_date,
                    item.expiry_date or "No expiry",
                    item.get_status_display(),
                    item.recommendation,
                ]
            }
            for item in self.get_stakeholder().due_diligence_reviews.all()
        ]

    def perform_service(self, cleaned_data):
        StakeholderDueDiligenceService(user=self.request.user).record(
            self.get_stakeholder(), **cleaned_data
        )


class StakeholderRiskView(StakeholderRelatedView):
    template_name = "stakeholders/risk_records.html"
    permission_required = (PARTNERS_VIEW_CONFIDENTIAL, PARTNERS_MANAGE_RISK)
    write_permission = PARTNERS_MANAGE_RISK
    route_name = "stakeholders:risks"
    title = "Conflict and risk"
    description = "Restricted declarations, scoring, mitigation, and review dates."

    def get_rows(self):
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "risks": self.get_stakeholder().risks.select_related(
                    "category", "responsible_officer"
                ),
                "conflicts": (
                    self.get_stakeholder().conflicts_of_interest.select_related(
                        "declared_by", "reviewed_by"
                    )
                ),
                "risk_form": kwargs.get("risk_form")
                or (StakeholderRiskForm(prefix="risk") if self.can_write() else None),
                "conflict_form": kwargs.get("conflict_form")
                or (
                    StakeholderConflictForm(prefix="conflict")
                    if self.can_write()
                    else None
                ),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        if not self.can_write():
            raise PermissionDenied
        record_type = request.POST.get("record_type")
        risk_form = StakeholderRiskForm(prefix="risk")
        conflict_form = StakeholderConflictForm(prefix="conflict")
        if record_type == "risk":
            risk_form = StakeholderRiskForm(request.POST, prefix="risk")
            if risk_form.is_valid():
                try:
                    StakeholderRiskService(user=request.user).record_risk(
                        self.get_stakeholder(), **risk_form.cleaned_data
                    )
                except ValidationError as exc:
                    _apply_service_errors(risk_form, exc)
                else:
                    messages.success(request, "Risk recorded.")
                    return redirect(self.route_name, pk=self.get_stakeholder().pk)
        elif record_type == "conflict":
            conflict_form = StakeholderConflictForm(request.POST, prefix="conflict")
            if conflict_form.is_valid():
                try:
                    StakeholderRiskService(user=request.user).declare_conflict(
                        self.get_stakeholder(), **conflict_form.cleaned_data
                    )
                except ValidationError as exc:
                    _apply_service_errors(conflict_form, exc)
                else:
                    messages.success(request, "Conflict declaration recorded.")
                    return redirect(self.route_name, pk=self.get_stakeholder().pk)
        else:
            return HttpResponseBadRequest("Invalid risk record type.")
        return self.render_to_response(
            self.get_context_data(risk_form=risk_form, conflict_form=conflict_form)
        )


class StakeholderPerformanceView(StakeholderRelatedView):
    write_permission = PARTNERS_MANAGE_PERFORMANCE
    form_class = StakeholderPerformanceForm
    route_name = "stakeholders:performance"
    title = "Performance reviews"
    description = "Weighted scorecards using the currently active dimensions."
    columns = ("Reference", "Period", "Date", "Score", "Completeness", "Status")

    def get_rows(self):
        rows = []
        for review in self.get_stakeholder().performance_reviews.all():
            actions = []
            if self.can_write() and review.status == ReviewStatus.DRAFT:
                actions.append(
                    {
                        "url": reverse(
                            "stakeholders:performance_finalize",
                            kwargs={"review_pk": review.pk},
                        ),
                        "label": "Finalize",
                        "style": "outline-success",
                    }
                )
            rows.append(
                {
                    "cells": [
                        review.reference_number,
                        review.review_period,
                        review.review_date,
                        (
                            review.weighted_score
                            if review.weighted_score is not None
                            else "Missing"
                        ),
                        f"{review.completeness_percentage}%",
                        review.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        form = self._active_form
        review_period = cleaned_data.pop("review_period")
        StakeholderPerformanceService(user=self.request.user).record_review(
            self.get_stakeholder(),
            review_period=review_period,
            scores=form.scores,
            **cleaned_data,
        )

    def post(self, request, *args, **kwargs):
        if not self.can_write():
            raise PermissionDenied
        form = self.get_form(request.POST, request.FILES)
        self._active_form = form
        if form is not None and form.is_valid():
            try:
                self.perform_service(form.cleaned_data.copy())
            except ValidationError as exc:
                _apply_service_errors(form, exc)
            else:
                messages.success(request, "Performance review recorded.")
                return redirect(self.route_name, pk=self.get_stakeholder().pk)
        return self.render_to_response(self.get_context_data(form=form))


class StakeholderActionsView(StakeholderRelatedView):
    write_permission = PARTNERS_MANAGE_ACTIONS
    form_class = StakeholderActionForm
    route_name = "stakeholders:actions"
    title = "Action items"
    description = "Assigned follow-up work, priorities, due dates, and progress."
    columns = ("Action", "Assigned to", "Due", "Priority", "Status")

    def get_form_kwargs(self):
        return {"stakeholder": self.get_stakeholder()}

    def get_rows(self):
        rows = []
        for item in self.get_stakeholder().action_items.select_related("assigned_to"):
            actions = []
            if self.can_write() and item.status not in {
                ActionStatus.COMPLETED,
                ActionStatus.CANCELLED,
            }:
                actions.append(
                    {
                        "url": reverse(
                            "stakeholders:action_status",
                            kwargs={"action_pk": item.pk},
                        ),
                        "label": "Update",
                        "style": "outline-primary",
                        "link": True,
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.title,
                        item.assigned_to or "Unassigned",
                        item.due_date,
                        item.get_priority_display(),
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        StakeholderActionService(user=self.request.user).create(
            self.get_stakeholder(), **cleaned_data
        )


class StakeholderNotesView(StakeholderRelatedView):
    permission_required = (PARTNERS_VIEW_CONFIDENTIAL, PARTNERS_MANAGE_NOTES)
    write_permission = PARTNERS_MANAGE_NOTES
    form_class = StakeholderNoteForm
    route_name = "stakeholders:notes"
    title = "Internal notes"
    description = "Restricted, versioned internal relationship notes."
    columns = ("Title", "Category", "Owner", "Version", "Status")

    def get_rows(self):
        rows = []
        queryset = self.get_stakeholder().stakeholder_notes.select_related("owner")
        for note in queryset:
            actions = []
            if self.can_write() and note.status == "DRAFT":
                actions.extend(
                    [
                        {
                            "url": reverse(
                                "stakeholders:note_version_add",
                                kwargs={"note_pk": note.pk},
                            ),
                            "label": "Add version",
                            "style": "outline-primary",
                            "link": True,
                        },
                        {
                            "url": reverse(
                                "stakeholders:note_finalize",
                                kwargs={"note_pk": note.pk},
                            ),
                            "label": "Finalize",
                            "style": "outline-success",
                        },
                    ]
                )
            latest = note.versions.filter(
                version_number=note.current_version_number
            ).first()
            rows.append(
                {
                    "cells": [
                        note.title,
                        note.category,
                        note.owner or "Unassigned",
                        note.current_version_number,
                        note.get_status_display(),
                    ],
                    "details": latest.content if latest else "No content version.",
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        content = cleaned_data.pop("content")
        title = cleaned_data.pop("title")
        StakeholderNoteService(user=self.request.user).create(
            self.get_stakeholder(), title=title, content=content, **cleaned_data
        )


class StakeholderDocumentsView(StakeholderRelatedView):
    permission_required = PARTNERS_MANAGE_DOCUMENTS
    write_permission = PARTNERS_MANAGE_DOCUMENTS
    form_class = StakeholderDocumentForm
    route_name = "stakeholders:documents"
    title = "Protected documents"
    description = (
        "Private, versioned files delivered only through authorized downloads."
    )
    columns = ("Document", "Type", "Version", "Status", "File size")

    def get_rows(self):
        rows = []
        for document in visible_stakeholder_documents(
            self.request.user, self.get_stakeholder()
        ):
            actions = [
                {
                    "url": reverse(
                        "stakeholders:document_download",
                        kwargs={"document_pk": document.pk},
                    ),
                    "label": "Download",
                    "style": "outline-primary",
                    "link": True,
                }
            ]
            if self.can_write() and document.status != "ARCHIVED":
                actions.append(
                    {
                        "url": reverse(
                            "stakeholders:document_archive",
                            kwargs={"document_pk": document.pk},
                        ),
                        "label": "Archive",
                        "style": "outline-danger",
                    }
                )
            rows.append(
                {
                    "cells": [
                        document.title,
                        document.document_type,
                        document.version_number,
                        document.get_status_display(),
                        f"{document.file_size} bytes",
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        file = cleaned_data.pop("file")
        document_key = cleaned_data.pop("document_key")
        title = cleaned_data.pop("title")
        document_type = cleaned_data.pop("document_type")
        StakeholderDocumentService(user=self.request.user).add_version(
            self.get_stakeholder(),
            document_key=document_key,
            title=title,
            document_type=document_type,
            file=file,
            **cleaned_data,
        )


class ScopedWorkflowFormView(StakeholderPermissionMixin, FormView):
    template_name = "stakeholders/workflow_form.html"
    model: ClassVar[type[models.Model] | None] = None
    object_kwarg = "pk"
    relation = "stakeholder"
    title = "Update record"
    success_route = "stakeholders:profile"

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = _scoped_related(
                self.model,
                self.request.user,
                self.kwargs[self.object_kwarg],
                self.relation,
            )
        return self.object

    def get_stakeholder(self):
        obj = self.get_object()
        if self.relation == "stakeholder":
            return obj.stakeholder
        if self.relation == "agreement__stakeholder":
            return obj.agreement.stakeholder
        raise RuntimeError("Unsupported stakeholder relation.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.title,
                "stakeholder": self.get_stakeholder(),
                "record": self.get_object(),
                "cancel_url": reverse(
                    self.success_route, kwargs={"pk": self.get_stakeholder().pk}
                ),
            }
        )
        return context

    def perform_service(self, cleaned_data):
        raise NotImplementedError

    def form_valid(self, form):
        try:
            self.perform_service(form.cleaned_data.copy())
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Workflow action completed.")
        return redirect(self.success_route, pk=self.get_stakeholder().pk)


class EngagementCompleteView(ScopedWorkflowFormView):
    model = StakeholderEngagement
    object_kwarg = "engagement_pk"
    form_class = EngagementCompletionForm
    permission_required = PARTNERS_MANAGE_ENGAGEMENTS
    title = "Complete engagement"
    success_route = "stakeholders:engagements"

    def perform_service(self, cleaned_data):
        StakeholderEngagementService(user=self.request.user).complete(
            self.get_object(), **cleaned_data
        )


class CommitmentProgressView(ScopedWorkflowFormView):
    model = StakeholderCommitment
    object_kwarg = "commitment_pk"
    form_class = CommitmentProgressForm
    permission_required = PARTNERS_MANAGE_COMMITMENTS
    title = "Update commitment progress"
    success_route = "stakeholders:commitments"

    def perform_service(self, cleaned_data):
        StakeholderCommitmentService(user=self.request.user).update_progress(
            self.get_object(), **cleaned_data
        )


class AgreementTransitionView(ScopedWorkflowFormView):
    model = StakeholderAgreement
    object_kwarg = "agreement_pk"
    form_class = AgreementTransitionForm
    permission_required = (
        PARTNERS_MANAGE_AGREEMENTS,
        PARTNERS_REVIEW_AGREEMENTS,
        PARTNERS_APPROVE_AGREEMENTS,
    )
    title = "Review or transition agreement"
    success_route = "stakeholders:agreements"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["agreement"] = self.get_object()
        return kwargs

    def perform_service(self, cleaned_data):
        StakeholderAgreementService(user=self.request.user).transition(
            self.get_object(),
            cleaned_data["new_status"],
            cleaned_data.get("reason", ""),
        )


class AgreementVersionCreateView(ScopedWorkflowFormView):
    model = StakeholderAgreement
    object_kwarg = "agreement_pk"
    form_class = AgreementVersionForm
    permission_required = PARTNERS_MANAGE_AGREEMENTS
    title = "Add agreement version"
    success_route = "stakeholders:agreements"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["agreement"] = self.get_object()
        return kwargs

    def perform_service(self, cleaned_data):
        change_summary = cleaned_data.pop("change_summary")
        StakeholderAgreementService(user=self.request.user).add_version(
            self.get_object(), change_summary=change_summary, **cleaned_data
        )


class AgreementRenewalRequestView(ScopedWorkflowFormView):
    model = StakeholderAgreement
    object_kwarg = "agreement_pk"
    form_class = AgreementRenewalRequestForm
    permission_required = PARTNERS_MANAGE_AGREEMENTS
    title = "Request agreement renewal"
    success_route = "stakeholders:agreements"

    def perform_service(self, cleaned_data):
        StakeholderAgreementService(user=self.request.user).request_renewal(
            self.get_object(), **cleaned_data
        )


class AgreementRenewalDecisionView(ScopedWorkflowFormView):
    model = StakeholderAgreementRenewal
    object_kwarg = "renewal_pk"
    relation = "agreement__stakeholder"
    form_class = AgreementRenewalDecisionForm
    permission_required = PARTNERS_MANAGE_AGREEMENTS
    title = "Decide agreement renewal"
    success_route = "stakeholders:agreements"

    def perform_service(self, cleaned_data):
        StakeholderAgreementService(user=self.request.user).decide_renewal(
            self.get_object(),
            approve=cleaned_data["decision"] == "approve",
            decision_notes=cleaned_data["decision_notes"],
        )


class ActionStatusView(ScopedWorkflowFormView):
    model = StakeholderActionItem
    object_kwarg = "action_pk"
    form_class = ActionStatusForm
    permission_required = PARTNERS_MANAGE_ACTIONS
    title = "Update action status"
    success_route = "stakeholders:actions"

    def perform_service(self, cleaned_data):
        StakeholderActionService(user=self.request.user).change_status(
            self.get_object(), **cleaned_data
        )


class NoteVersionCreateView(ScopedWorkflowFormView):
    model = StakeholderNote
    object_kwarg = "note_pk"
    form_class = NoteVersionForm
    permission_required = PARTNERS_MANAGE_NOTES
    title = "Add note version"
    success_route = "stakeholders:notes"

    def perform_service(self, cleaned_data):
        StakeholderNoteService(user=self.request.user).add_version(
            self.get_object(), **cleaned_data
        )


class ScopedPostActionView(StakeholderPermissionMixin, View):
    model: ClassVar[type[models.Model] | None] = None
    object_kwarg = "pk"
    relation = "stakeholder"
    success_route = "stakeholders:profile"

    def perform_service(self, obj):
        raise NotImplementedError

    def post(self, request, *args, **kwargs):
        obj = _scoped_related(
            self.model,
            request.user,
            kwargs[self.object_kwarg],
            self.relation,
        )
        stakeholder = (
            obj.stakeholder
            if self.relation == "stakeholder"
            else obj.agreement.stakeholder
        )
        try:
            self.perform_service(obj)
        except ValidationError as exc:
            messages.error(request, " ".join(str(message) for message in exc.messages))
        else:
            messages.success(request, "Workflow action completed.")
        return redirect(self.success_route, pk=stakeholder.pk)


class ContactSetPrimaryView(ScopedPostActionView):
    model = StakeholderContact
    object_kwarg = "contact_pk"
    permission_required = PARTNERS_MANAGE_CONTACTS
    success_route = "stakeholders:contacts"

    def perform_service(self, obj):
        StakeholderContactService(user=self.request.user).set_primary(obj)


class ContactDeactivateView(ContactSetPrimaryView):
    def perform_service(self, obj):
        StakeholderContactService(user=self.request.user).deactivate(obj)


class ContributionVerifyView(ScopedPostActionView):
    model = StakeholderContribution
    object_kwarg = "contribution_pk"
    permission_required = PARTNERS_MANAGE_CONTRIBUTIONS
    success_route = "stakeholders:contributions"

    def perform_service(self, obj):
        StakeholderContributionService(user=self.request.user).verify(obj)


class PerformanceFinalizeView(ScopedPostActionView):
    model = StakeholderPerformanceReview
    object_kwarg = "review_pk"
    permission_required = PARTNERS_MANAGE_PERFORMANCE
    success_route = "stakeholders:performance"

    def perform_service(self, obj):
        StakeholderPerformanceService(user=self.request.user).finalize(obj)


class NoteFinalizeView(ScopedPostActionView):
    model = StakeholderNote
    object_kwarg = "note_pk"
    permission_required = PARTNERS_MANAGE_NOTES
    success_route = "stakeholders:notes"

    def perform_service(self, obj):
        StakeholderNoteService(user=self.request.user).finalize(obj)


class DocumentArchiveView(ScopedPostActionView):
    model = StakeholderDocument
    object_kwarg = "document_pk"
    permission_required = PARTNERS_MANAGE_DOCUMENTS
    success_route = "stakeholders:documents"

    def perform_service(self, obj):
        StakeholderDocumentService(user=self.request.user).archive(obj)


class StakeholderDocumentDownloadView(StakeholderPermissionMixin, View):
    permission_required = PARTNERS_MANAGE_DOCUMENTS

    def get(self, request, document_pk):
        document = get_object_or_404(
            visible_stakeholder_documents(request.user), pk=document_pk
        )
        if not document.file:
            raise Http404("The document file is unavailable.")
        try:
            file_handle = document.file.open("rb")
        except OSError as exc:
            raise Http404("The document file is unavailable.") from exc
        logger.info(
            "stakeholder_document_downloaded",
            extra={
                "stakeholder_event": {
                    "action": "document.downloaded",
                    "entity_id": str(document.pk),
                    "stakeholder_id": str(document.stakeholder_id),
                    "actor_id": str(request.user.pk),
                }
            },
        )
        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=Path(document.original_filename or document.file.name).name,
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        response["Pragma"] = "no-cache"
        return response


class AgreementVersionDownloadView(StakeholderPermissionMixin, View):
    permission_required = (PARTNERS_MANAGE_AGREEMENTS, PARTNERS_MANAGE_DOCUMENTS)

    def get(self, request, version_pk):
        version = get_object_or_404(
            StakeholderAgreementVersion.objects.filter(
                agreement__stakeholder__in=visible_stakeholders(
                    request.user, include_archived=True
                )
            ).select_related("agreement__stakeholder"),
            pk=version_pk,
        )
        if not version.file:
            raise Http404("This agreement version has no file.")
        try:
            file_handle = version.file.open("rb")
        except OSError as exc:
            raise Http404("The agreement file is unavailable.") from exc
        logger.info(
            "stakeholder_agreement_version_downloaded",
            extra={
                "stakeholder_event": {
                    "action": "agreement_version.downloaded",
                    "entity_id": str(version.pk),
                    "agreement_id": str(version.agreement_id),
                    "stakeholder_id": str(version.agreement.stakeholder_id),
                    "actor_id": str(request.user.pk),
                }
            },
        )
        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=Path(version.file_name or version.file.name).name,
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        response["Pragma"] = "no-cache"
        return response


class StakeholderReportsView(StakeholderPermissionMixin, TemplateView):
    template_name = "stakeholders/reports.html"
    permission_required = (PARTNERS_VIEW, PARTNERS_ANALYTICS, PARTNERS_EXPORT)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stakeholders = visible_stakeholders(self.request.user)
        context.update(
            {
                "total": stakeholders.count(),
                "status_summary": list(
                    stakeholders.values("status")
                    .annotate(total=Count("id"))
                    .order_by("status")
                ),
                "category_summary": list(
                    StakeholderReferenceData.objects.filter(
                        kind=ReferenceDataKind.CATEGORY,
                        category_stakeholders__in=stakeholders,
                    )
                    .values("name")
                    .annotate(total=Count("category_stakeholders", distinct=True))
                    .order_by("name")
                ),
                "region_summary": list(
                    stakeholders.exclude(province_or_region="")
                    .values("province_or_region")
                    .annotate(total=Count("id"))
                    .order_by("province_or_region")
                ),
                "can_export": _can(self.request.user, PARTNERS_EXPORT),
            }
        )
        if _can_view_financial(self.request.user):
            context["contribution_summary"] = list(
                StakeholderContribution.objects.filter(stakeholder__in=stakeholders)
                .values("status", "currency")
                .annotate(total=Sum("amount"), records=Count("id"))
                .order_by("status", "currency")
            )
        return context


class StakeholderRegisterExportView(StakeholderPermissionMixin, View):
    permission_required = PARTNERS_EXPORT

    def get(self, request):
        return stakeholder_register_csv_response(request.user)
