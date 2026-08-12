"""Permission-aware, service-backed beneficiary management views."""

from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import Any, ClassVar

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from apps.rbac.authorization import user_has_permission
from apps.rbac.mixins import PermissionRequiredMixin

from .constants import (
    BeneficiaryStatus,
    ConsentStatus,
    DocumentStatus,
    FollowUpStatus,
    PlanStatus,
    ReferenceDataKind,
    ReferralStatus,
    TransferStatus,
)
from .exports import beneficiary_register_csv_response
from .forms import (
    AssessmentForm,
    AttendanceForm,
    BeneficiaryArchiveForm,
    BeneficiaryForm,
    BeneficiaryStatusTransitionForm,
    BeneficiaryUpdateForm,
    CaseNoteForm,
    CommunicationForm,
    ConsentForm,
    ConsentWithdrawForm,
    DocumentForm,
    DuplicateReviewForm,
    EmptyConfirmationForm,
    EnrollmentForm,
    EnrollmentStatusForm,
    ExitForm,
    FeedbackForm,
    FeedbackResponseForm,
    FollowUpCompleteForm,
    FollowUpForm,
    GroupForm,
    GroupMemberForm,
    GuardianForm,
    HouseholdForm,
    HouseholdMemberForm,
    OutcomeForm,
    ParticipationForm,
    ReferralForm,
    ReferralStatusForm,
    SafeguardingForm,
    SafeguardingStatusForm,
    ServiceDeliveryCompleteForm,
    ServiceDeliveryForm,
    SupportPlanForm,
    TransferCompleteForm,
    TransferForm,
)
from .models import (
    Beneficiary,
    BeneficiaryAssessment,
    BeneficiaryDocument,
    BeneficiaryEnrollment,
    BeneficiaryGroup,
    BeneficiaryHousehold,
    BeneficiaryReferenceData,
    ConsentRecord,
    DuplicateReviewRecord,
    FeedbackRecord,
    FollowUpVisit,
    GroupMembership,
    GuardianRecord,
    HouseholdMember,
    Referral,
    SafeguardingRecord,
    ServiceDeliveryRecord,
    SupportPlan,
    TransferRecord,
)
from .permissions import (
    BENEFICIARIES_ANALYTICS,
    BENEFICIARIES_APPROVE,
    BENEFICIARIES_ARCHIVE,
    BENEFICIARIES_CREATE,
    BENEFICIARIES_EXPORT,
    BENEFICIARIES_MANAGE,
    BENEFICIARIES_MANAGE_ASSESSMENTS,
    BENEFICIARIES_MANAGE_ATTENDANCE,
    BENEFICIARIES_MANAGE_CASE_NOTES,
    BENEFICIARIES_MANAGE_CONSENT,
    BENEFICIARIES_MANAGE_DOCUMENTS,
    BENEFICIARIES_MANAGE_DUPLICATES,
    BENEFICIARIES_MANAGE_ENROLLMENTS,
    BENEFICIARIES_MANAGE_EXITS,
    BENEFICIARIES_MANAGE_FEEDBACK,
    BENEFICIARIES_MANAGE_FOLLOW_UPS,
    BENEFICIARIES_MANAGE_GROUPS,
    BENEFICIARIES_MANAGE_GUARDIANS,
    BENEFICIARIES_MANAGE_HOUSEHOLDS,
    BENEFICIARIES_MANAGE_OUTCOMES,
    BENEFICIARIES_MANAGE_PARTICIPATION,
    BENEFICIARIES_MANAGE_REFERRALS,
    BENEFICIARIES_MANAGE_SAFEGUARDING,
    BENEFICIARIES_MANAGE_SERVICES,
    BENEFICIARIES_MANAGE_SUPPORT_PLANS,
    BENEFICIARIES_MANAGE_TRANSFERS,
    BENEFICIARIES_RESTORE,
    BENEFICIARIES_SUBMIT,
    BENEFICIARIES_UPDATE,
    BENEFICIARIES_VIEW,
    BENEFICIARIES_VIEW_CONFIDENTIAL,
)
from .report_exports import (
    beneficiary_profile_docx_response,
    beneficiary_register_docx_response,
    beneficiary_register_pdf_response,
    beneficiary_register_xlsx_response,
)
from .selectors import (
    user_can_access_beneficiary,
    visible_beneficiaries,
    visible_beneficiary_documents,
)
from .services import (
    AssessmentService,
    AttendanceService,
    BeneficiaryService,
    CaseNoteService,
    CommunicationService,
    ConsentService,
    DocumentService,
    DuplicateService,
    EnrollmentService,
    ExitService,
    FeedbackService,
    FollowUpService,
    GroupService,
    GuardianService,
    HouseholdService,
    OutcomeService,
    ParticipationService,
    ReferralService,
    SafeguardingService,
    ServiceDeliveryService,
    SupportPlanService,
    TransferService,
)

logger = logging.getLogger(__name__)


def _can(user, *permission_codes: str) -> bool:
    return bool(
        user_has_permission(user, BENEFICIARIES_MANAGE)
        or any(user_has_permission(user, code) for code in permission_codes)
    )


def _can_view_confidential(user) -> bool:
    return bool(
        getattr(user, "is_superuser", False)
        or _can(user, BENEFICIARIES_VIEW_CONFIDENTIAL)
    )


def _apply_service_errors(form, exc: ValidationError) -> None:
    if hasattr(exc, "message_dict"):
        for field_name, field_messages in exc.message_dict.items():
            target = field_name if field_name in form.fields else None
            for message in field_messages:
                form.add_error(target, message)
        return
    for message in exc.messages:
        form.add_error(None, message)


def _scoped_beneficiary(user, pk, *, include_archived: bool = False) -> Beneficiary:
    return get_object_or_404(
        visible_beneficiaries(user, include_archived=include_archived), pk=pk
    )


def _scoped_related(model, user, pk, relation: str = "beneficiary"):
    return get_object_or_404(
        model.objects.filter(
            **{f"{relation}__in": visible_beneficiaries(user, include_archived=True)}
        ),
        pk=pk,
    )


def _candidate_beneficiaries(user):
    """Possible duplicate candidates exclude the reviewed record itself."""
    return visible_beneficiaries(user, include_archived=True)


class BeneficiaryPermissionMixin(PermissionRequiredMixin):
    """Allow any listed operation permission, with module-manager override."""

    any_permission = True

    def test_func(self) -> bool:
        required = self.permission_required
        permissions = (required,) if isinstance(required, str) else tuple(required)
        return _can(self.request.user, *permissions)


class BeneficiaryDashboardView(BeneficiaryPermissionMixin, TemplateView):
    template_name = "beneficiaries/dashboard.html"
    permission_required = BENEFICIARIES_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        beneficiaries = visible_beneficiaries(user)
        today = timezone.localdate()
        metrics = beneficiaries.aggregate(
            total=Count("id"),
            identified=Count("id", filter=Q(status=BeneficiaryStatus.IDENTIFIED)),
            registered=Count("id", filter=Q(status=BeneficiaryStatus.REGISTERED)),
            verified=Count("id", filter=Q(status=BeneficiaryStatus.VERIFIED)),
            eligible=Count("id", filter=Q(status=BeneficiaryStatus.ELIGIBLE)),
            enrolled=Count("id", filter=Q(status=BeneficiaryStatus.ENROLLED)),
            active=Count("id", filter=Q(status=BeneficiaryStatus.ACTIVE)),
            suspended=Count("id", filter=Q(status=BeneficiaryStatus.SUSPENDED)),
            graduated=Count("id", filter=Q(status=BeneficiaryStatus.GRADUATED)),
            exited=Count("id", filter=Q(status=BeneficiaryStatus.EXITED)),
            minors=Count("id", filter=Q(is_minor=True)),
            consent_granted=Count("id", filter=Q(consent_status=ConsentStatus.GRANTED)),
            safeguarding_concerns=Count("id", filter=Q(safeguarding_concerns=True)),
        )
        status_summary = list(
            beneficiaries.values("status")
            .annotate(total=Count("id"))
            .order_by("status")
        )
        context.update(
            {
                "metrics": metrics,
                "status_summary": status_summary,
                "recent_beneficiaries": beneficiaries.order_by("-created_at")[:6],
                "due_follow_ups": FollowUpVisit.objects.filter(
                    beneficiary__in=beneficiaries,
                    status=FollowUpStatus.PLANNED,
                    scheduled_on__lte=today,
                ).count(),
                "open_referrals": Referral.objects.filter(
                    beneficiary__in=beneficiaries,
                    status__in=[ReferralStatus.OPEN, ReferralStatus.ACCEPTED],
                ).count(),
                "can_create": _can(user, BENEFICIARIES_CREATE),
                "has_granular_analytics": _can(user, BENEFICIARIES_ANALYTICS),
            }
        )
        if _can(user, BENEFICIARIES_ANALYTICS):
            context["category_summary"] = list(
                BeneficiaryReferenceData.objects.filter(
                    kind=ReferenceDataKind.CATEGORY,
                    category_beneficiaries__in=beneficiaries,
                )
                .values("name")
                .annotate(total=Count("category_beneficiaries", distinct=True))
                .order_by("name")
            )
            context["region_summary"] = list(
                beneficiaries.exclude(province_or_region="")
                .values("province_or_region")
                .annotate(total=Count("id"))
                .order_by("province_or_region")
            )
        if _can_view_confidential(user):
            context["open_safeguarding"] = SafeguardingRecord.objects.filter(
                beneficiary__in=beneficiaries,
                status__in=["OPEN", "INVESTIGATING", "UNDER_REVIEW"],
            ).count()
            context["pending_duplicates"] = DuplicateReviewRecord.objects.filter(
                beneficiary__in=beneficiaries,
                review_status__in=["PENDING", "CONFIRMED_DUPLICATE"],
            ).count()
        return context


class BeneficiaryDirectoryView(BeneficiaryPermissionMixin, ListView):
    model = Beneficiary
    template_name = "beneficiaries/directory.html"
    context_object_name = "beneficiaries"
    paginate_by = 24
    permission_required = BENEFICIARIES_VIEW

    SORTS: ClassVar[dict[str, tuple[str, ...]]] = {
        "name": ("last_name", "first_name"),
        "name_desc": ("-last_name", "-first_name"),
        "reference": ("reference_number",),
        "status": ("status", "last_name"),
        "region": ("province_or_region", "last_name"),
        "recent": ("-created_at",),
    }

    def get_queryset(self):
        queryset = visible_beneficiaries(self.request.user).prefetch_related(
            "vulnerabilities", "needs"
        )
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(reference_number__icontains=search)
                | Q(first_name__icontains=search)
                | Q(middle_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone_primary__icontains=search)
            )
        status = self.request.GET.get("status", "")
        if status in BeneficiaryStatus.values:
            queryset = queryset.filter(status=status)
        region = self.request.GET.get("region", "").strip()
        if region:
            queryset = queryset.filter(province_or_region__icontains=region)
        category = self.request.GET.get("category", "").strip()
        if category:
            queryset = queryset.filter(category__code=category)
        is_minor = self.request.GET.get("minor", "")
        if is_minor in {"0", "1"}:
            queryset = queryset.filter(is_minor=is_minor == "1")
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
                "status_choices": BeneficiaryStatus.choices,
                "categories": BeneficiaryReferenceData.objects.filter(
                    kind=ReferenceDataKind.CATEGORY, active=True
                ),
                "sort_choices": (
                    ("name", "Name A-Z"),
                    ("name_desc", "Name Z-A"),
                    ("reference", "Reference"),
                    ("status", "Status"),
                    ("region", "Region"),
                    ("recent", "Recently added"),
                ),
                "query_without_page": query.urlencode(),
                "can_create": _can(self.request.user, BENEFICIARIES_CREATE),
                "can_view_confidential": _can_view_confidential(self.request.user),
            }
        )
        return context


class BeneficiaryCreateView(BeneficiaryPermissionMixin, FormView):
    form_class = BeneficiaryForm
    template_name = "beneficiaries/beneficiary_form.html"
    permission_required = BENEFICIARIES_CREATE

    def form_valid(self, form):
        try:
            beneficiary = BeneficiaryService(user=self.request.user).create(
                **form.cleaned_data
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Beneficiary {beneficiary.reference_number} registered successfully.",
        )
        return redirect("beneficiaries:profile", pk=beneficiary.pk)


class BeneficiaryUpdateView(BeneficiaryPermissionMixin, FormView):
    form_class = BeneficiaryUpdateForm
    template_name = "beneficiaries/beneficiary_form.html"
    permission_required = BENEFICIARIES_UPDATE

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = _scoped_beneficiary(self.request.user, self.kwargs["pk"])
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
            beneficiary = BeneficiaryService(user=self.request.user).update(
                self.get_object(), **form.cleaned_data
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Beneficiary profile updated successfully.")
        return redirect("beneficiaries:profile", pk=beneficiary.pk)


class BeneficiaryProfileView(BeneficiaryPermissionMixin, DetailView):
    model = Beneficiary
    template_name = "beneficiaries/profile.html"
    context_object_name = "beneficiary"
    permission_required = BENEFICIARIES_VIEW

    def get_queryset(self):
        return visible_beneficiaries(self.request.user).prefetch_related(
            "vulnerabilities",
            "inclusion_barriers",
            "disabilities",
            "skills",
            "interests",
            "needs",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        beneficiary = self.object
        user = self.request.user
        can_confidential = _can_view_confidential(user)
        can_documents = _can(user, BENEFICIARIES_MANAGE_DOCUMENTS)
        context.update(
            {
                "status_history": beneficiary.status_history.select_related(
                    "changed_by"
                )[:8],
                "guardians": beneficiary.guardians.all()[:6],
                "enrollments": beneficiary.enrollments.all()[:6],
                "participations": beneficiary.participations.all()[:6],
                "attendance_records": beneficiary.attendance_records.all()[:6],
                "services_received": beneficiary.services_received.all()[:6],
                "referrals": beneficiary.referrals.all()[:6],
                "case_notes": beneficiary.case_notes.all()[:6],
                "follow_ups": beneficiary.follow_ups.all()[:6],
                "assessments": beneficiary.assessments.all()[:6],
                "support_plans": beneficiary.support_plans.all()[:6],
                "outcomes": beneficiary.outcomes.all()[:6],
                "exits": beneficiary.exit_records.all()[:6],
                "transfers": beneficiary.transfers.all()[:6],
                "communications": beneficiary.communications.all()[:6],
                "feedback_records": beneficiary.feedback_records.all()[:6],
                "household_memberships": (
                    beneficiary.household_memberships.select_related("household")
                ),
                "group_memberships": beneficiary.group_memberships.select_related(
                    "group"
                ),
                "consent_records": beneficiary.consent_records.all()[:6],
                "can_update": _can(user, BENEFICIARIES_UPDATE),
                "can_archive": _can(user, BENEFICIARIES_ARCHIVE),
                "can_documents": can_documents,
                "can_view_confidential": can_confidential,
            }
        )
        if can_documents:
            context["documents"] = visible_beneficiary_documents(user, beneficiary)[:6]
        if can_confidential:
            context["safeguarding_records"] = beneficiary.safeguarding_records.all()[:6]
            context["duplicate_reviews"] = beneficiary.duplicate_reviews.all()[:6]
        return context


class BeneficiaryStatusView(BeneficiaryPermissionMixin, FormView):
    form_class = BeneficiaryStatusTransitionForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_UPDATE

    def get_beneficiary(self):
        if not hasattr(self, "beneficiary"):
            self.beneficiary = _scoped_beneficiary(self.request.user, self.kwargs["pk"])
        return self.beneficiary

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["beneficiary"] = self.get_beneficiary()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Change beneficiary status",
                "beneficiary": self.get_beneficiary(),
                "cancel_url": reverse(
                    "beneficiaries:profile", kwargs={"pk": self.get_beneficiary().pk}
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            BeneficiaryService(user=self.request.user).change_status(
                self.get_beneficiary(),
                form.cleaned_data["new_status"],
                form.cleaned_data["reason"],
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Beneficiary status updated.")
        return redirect("beneficiaries:profile", pk=self.get_beneficiary().pk)


class BeneficiaryArchiveView(BeneficiaryPermissionMixin, FormView):
    form_class = BeneficiaryArchiveForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_ARCHIVE

    def get_beneficiary(self):
        return _scoped_beneficiary(self.request.user, self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Archive beneficiary",
                "beneficiary": self.get_beneficiary(),
                "cancel_url": reverse(
                    "beneficiaries:profile", kwargs={"pk": self.get_beneficiary().pk}
                ),
            }
        )
        return context

    def form_valid(self, form):
        BeneficiaryService(user=self.request.user).archive(
            self.get_beneficiary(), form.cleaned_data["reason"]
        )
        messages.success(self.request, "Beneficiary archived.")
        return redirect("beneficiaries:directory")


class BeneficiaryRestoreView(BeneficiaryPermissionMixin, FormView):
    form_class = BeneficiaryArchiveForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_RESTORE

    def get_beneficiary(self):
        return _scoped_beneficiary(
            self.request.user, self.kwargs["pk"], include_archived=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Restore beneficiary",
                "beneficiary": self.get_beneficiary(),
                "cancel_url": reverse("beneficiaries:directory"),
            }
        )
        return context

    def form_valid(self, form):
        beneficiary = BeneficiaryService(user=self.request.user).restore(
            self.get_beneficiary(), form.cleaned_data["reason"]
        )
        messages.success(self.request, "Beneficiary restored as registered.")
        return redirect("beneficiaries:profile", pk=beneficiary.pk)


class HouseholdListView(BeneficiaryPermissionMixin, ListView):
    model = BeneficiaryHousehold
    template_name = "beneficiaries/households.html"
    context_object_name = "households"
    paginate_by = 24
    permission_required = BENEFICIARIES_VIEW

    def get_queryset(self):
        queryset = BeneficiaryHousehold.objects.select_related("household_type", "head")
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(reference_number__icontains=search)
                | Q(household_name__icontains=search)
            )
        status = self.request.GET.get("status", "")
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-formed_on")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop("page", None)
        context.update(
            {
                "status_choices": BeneficiaryHousehold._meta.get_field(
                    "status"
                ).choices,
                "query_without_page": query.urlencode(),
                "can_create": _can(self.request.user, BENEFICIARIES_MANAGE_HOUSEHOLDS),
                "household_form": (
                    HouseholdForm(prefix="household")
                    if _can(self.request.user, BENEFICIARIES_MANAGE_HOUSEHOLDS)
                    else None
                ),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        if not _can(request.user, BENEFICIARIES_MANAGE_HOUSEHOLDS):
            raise PermissionDenied
        form = HouseholdForm(request.POST, prefix="household")
        if form.is_valid():
            try:
                HouseholdService(user=request.user).create(**form.cleaned_data)
            except ValidationError as exc:
                _apply_service_errors(form, exc)
            else:
                messages.success(request, "Household created successfully.")
                return redirect("beneficiaries:households")
        context = self.get_context_data()
        context["household_form"] = form
        return self.render_to_response(context)


class HouseholdDetailView(BeneficiaryPermissionMixin, TemplateView):
    template_name = "beneficiaries/household_detail.html"
    permission_required = BENEFICIARIES_VIEW

    def get_household(self):
        if not hasattr(self, "household"):
            self.household = get_object_or_404(
                BeneficiaryHousehold.objects.select_related("household_type", "head"),
                pk=self.kwargs["pk"],
            )
        return self.household

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        household = self.get_household()
        can_write = _can(self.request.user, BENEFICIARIES_MANAGE_HOUSEHOLDS)
        context.update(
            {
                "household": household,
                "memberships": household.memberships.select_related(
                    "beneficiary", "relationship_to_head"
                ),
                "can_write": can_write,
                "member_form": kwargs.get("member_form")
                or (
                    HouseholdMemberForm(
                        beneficiaries=visible_beneficiaries(self.request.user)
                    )
                    if can_write
                    else None
                ),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        if not _can(request.user, BENEFICIARIES_MANAGE_HOUSEHOLDS):
            raise PermissionDenied
        form = HouseholdMemberForm(
            request.POST,
            beneficiaries=visible_beneficiaries(request.user),
        )
        if form.is_valid():
            try:
                HouseholdService(user=request.user).add_member(
                    self.get_household(),
                    form.cleaned_data["beneficiary"],
                    **form.cleaned_data,
                )
            except ValidationError as exc:
                _apply_service_errors(form, exc)
            else:
                messages.success(request, "Household member added.")
                return redirect(
                    "beneficiaries:household_detail", pk=self.get_household().pk
                )
        return self.render_to_response(self.get_context_data(member_form=form))


class GroupListView(BeneficiaryPermissionMixin, ListView):
    model = BeneficiaryGroup
    template_name = "beneficiaries/groups.html"
    context_object_name = "groups"
    paginate_by = 24
    permission_required = BENEFICIARIES_VIEW

    def get_queryset(self):
        queryset = BeneficiaryGroup.objects.select_related("group_type", "group_leader")
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(reference_number__icontains=search) | Q(group_name__icontains=search)
            )
        status = self.request.GET.get("status", "")
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-formation_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop("page", None)
        context.update(
            {
                "status_choices": BeneficiaryGroup._meta.get_field("status").choices,
                "query_without_page": query.urlencode(),
                "can_create": _can(self.request.user, BENEFICIARIES_MANAGE_GROUPS),
                "group_form": (
                    GroupForm(
                        beneficiaries=visible_beneficiaries(self.request.user),
                        prefix="group",
                    )
                    if _can(self.request.user, BENEFICIARIES_MANAGE_GROUPS)
                    else None
                ),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        if not _can(request.user, BENEFICIARIES_MANAGE_GROUPS):
            raise PermissionDenied
        form = GroupForm(
            request.POST,
            beneficiaries=visible_beneficiaries(request.user),
            prefix="group",
        )
        if form.is_valid():
            try:
                GroupService(user=request.user).create(**form.cleaned_data)
            except ValidationError as exc:
                _apply_service_errors(form, exc)
            else:
                messages.success(request, "Group created successfully.")
                return redirect("beneficiaries:groups")
        context = self.get_context_data()
        context["group_form"] = form
        return self.render_to_response(context)


class GroupDetailView(BeneficiaryPermissionMixin, TemplateView):
    template_name = "beneficiaries/group_detail.html"
    permission_required = BENEFICIARIES_VIEW

    def get_group(self):
        if not hasattr(self, "group"):
            self.group = get_object_or_404(
                BeneficiaryGroup.objects.select_related("group_type", "group_leader"),
                pk=self.kwargs["pk"],
            )
        return self.group

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_group()
        can_write = _can(self.request.user, BENEFICIARIES_MANAGE_GROUPS)
        context.update(
            {
                "group": group,
                "memberships": group.memberships.select_related("beneficiary"),
                "can_write": can_write,
                "member_form": kwargs.get("member_form")
                or (
                    GroupMemberForm(
                        beneficiaries=visible_beneficiaries(self.request.user)
                    )
                    if can_write
                    else None
                ),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        if not _can(request.user, BENEFICIARIES_MANAGE_GROUPS):
            raise PermissionDenied
        form = GroupMemberForm(
            request.POST, beneficiaries=visible_beneficiaries(request.user)
        )
        if form.is_valid():
            try:
                GroupService(user=request.user).add_member(
                    self.get_group(),
                    form.cleaned_data["beneficiary"],
                    **form.cleaned_data,
                )
            except ValidationError as exc:
                _apply_service_errors(form, exc)
            else:
                messages.success(request, "Group member added.")
                return redirect("beneficiaries:group_detail", pk=self.get_group().pk)
        return self.render_to_response(self.get_context_data(member_form=form))


class BeneficiaryRelatedView(BeneficiaryPermissionMixin, TemplateView):
    """Render and create one scoped related-record collection."""

    template_name = "beneficiaries/related_records.html"
    permission_required: str | tuple[str, ...] = BENEFICIARIES_VIEW
    write_permission = ""
    form_class: ClassVar[type[forms.BaseForm] | None] = None
    route_name = ""
    title = "Related records"
    description = ""
    columns: tuple[str, ...] = ()

    def get_beneficiary(self):
        if not hasattr(self, "beneficiary"):
            self.beneficiary = _scoped_beneficiary(
                self.request.user, self.kwargs["pk"], include_archived=True
            )
        return self.beneficiary

    def can_write(self):
        return bool(
            self.write_permission and _can(self.request.user, self.write_permission)
        )

    def get_form_kwargs(self):
        kwargs = {}
        if self.form_class is not None:
            parameters = inspect.signature(self.form_class.__init__).parameters
            if "beneficiary" in parameters:
                kwargs["beneficiary"] = self.get_beneficiary()
        return kwargs

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
                "beneficiary": self.get_beneficiary(),
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
                return redirect(self.route_name, pk=self.get_beneficiary().pk)
        return self.render_to_response(self.get_context_data(form=form))


class GuardiansView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_GUARDIANS
    form_class = GuardianForm
    route_name = "beneficiaries:guardians"
    title = "Guardians"
    description = "Guardians and care-givers for the beneficiary."
    columns = ("Name", "Relationship", "Contact", "Validity", "Status")

    def get_rows(self):
        rows = []
        for guardian in self.get_beneficiary().guardians.all():
            actions = []
            if self.can_write() and guardian.is_active and not guardian.is_primary:
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:guardian_primary",
                            kwargs={"guardian_pk": guardian.pk},
                        ),
                        "label": "Set primary",
                        "style": "outline-primary",
                    }
                )
            if self.can_write() and guardian.is_active:
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:guardian_deactivate",
                            kwargs={"guardian_pk": guardian.pk},
                        ),
                        "label": "Deactivate",
                        "style": "outline-danger",
                    }
                )
            rows.append(
                {
                    "cells": [
                        guardian.full_name,
                        guardian.get_relationship_display(),
                        guardian.email or guardian.phone_primary,
                        f"{guardian.valid_from} to {guardian.valid_to or 'current'}",
                        (
                            "Primary"
                            if guardian.is_primary
                            else ("Active" if guardian.is_active else "Inactive")
                        ),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        GuardianService(user=self.request.user).create(
            self.get_beneficiary(), **cleaned_data
        )


class EnrollmentsView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_ENROLLMENTS
    form_class = EnrollmentForm
    route_name = "beneficiaries:enrollments"
    title = "Enrollments"
    description = "Program, project, and intervention enrollments."
    columns = ("Reference", "Activity", "Enrollment date", "Source", "Status")

    def get_rows(self):
        rows = []
        for item in self.get_beneficiary().enrollments.select_related(
            "enrollment_type", "source"
        ):
            actions = []
            if self.can_write() and item.status not in {
                "COMPLETED",
                "WITHDRAWN",
            }:
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:enrollment_status",
                            kwargs={"enrollment_pk": item.pk},
                        ),
                        "label": "Change status",
                        "style": "outline-primary",
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.reference_number,
                        item.activity_title,
                        item.enrollment_date,
                        item.enrollment_type.name if item.enrollment_type else "N/A",
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        EnrollmentService(user=self.request.user).create(
            self.get_beneficiary(), **cleaned_data
        )


class ParticipationView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_PARTICIPATION
    form_class = ParticipationForm
    route_name = "beneficiaries:participation"
    title = "Participation"
    description = "Activity participation records and observed outcomes."
    columns = ("Reference", "Activity", "Date", "Location", "Status")

    def get_rows(self):
        return [
            {
                "cells": [
                    item.reference_number,
                    item.activity_title,
                    item.activity_date,
                    item.location or "N/A",
                    item.get_status_display(),
                ]
            }
            for item in self.get_beneficiary().participations.all()
        ]

    def perform_service(self, cleaned_data):
        ParticipationService(user=self.request.user).record(
            self.get_beneficiary(), **cleaned_data
        )


class AttendanceView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_ATTENDANCE
    form_class = AttendanceForm
    route_name = "beneficiaries:attendance"
    title = "Attendance"
    description = "Session attendance records for the beneficiary."
    columns = ("Session", "Date", "Status", "Absence reason")

    def get_rows(self):
        return [
            {
                "cells": [
                    item.session_title,
                    item.session_date,
                    item.get_status_display(),
                    item.reason or "N/A",
                ]
            }
            for item in self.get_beneficiary().attendance_records.all()
        ]

    def perform_service(self, cleaned_data):
        AttendanceService(user=self.request.user).record(
            self.get_beneficiary(), **cleaned_data
        )


class ServicesView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_SERVICES
    form_class = ServiceDeliveryForm
    route_name = "beneficiaries:services"
    title = "Services delivered"
    description = "Services delivered to the beneficiary with outcomes."
    columns = ("Reference", "Service", "Date", "Provider", "Status")

    def get_rows(self):
        rows = []
        for item in self.get_beneficiary().services_received.select_related(
            "service_type"
        ):
            actions = []
            if self.can_write() and item.status == "PLANNED":
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:service_deliver",
                            kwargs={"service_pk": item.pk},
                        ),
                        "label": "Mark delivered",
                        "style": "outline-success",
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.reference_number,
                        item.service_name,
                        item.service_date,
                        item.provider or "N/A",
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        ServiceDeliveryService(user=self.request.user).create(
            self.get_beneficiary(), **cleaned_data
        )


class ReferralsView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_REFERRALS
    form_class = ReferralForm
    route_name = "beneficiaries:referrals"
    title = "Referrals"
    description = "Internal and external referrals on behalf of the beneficiary."
    columns = ("Reference", "To", "Date", "Priority", "Status")

    def get_rows(self):
        rows = []
        for item in self.get_beneficiary().referrals.all():
            actions = []
            if self.can_write() and item.status not in {"CLOSED", "CANCELLED"}:
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:referral_status",
                            kwargs={"referral_pk": item.pk},
                        ),
                        "label": "Update status",
                        "style": "outline-primary",
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.reference_number,
                        item.referred_to,
                        item.referral_date,
                        item.get_priority_display(),
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        ReferralService(user=self.request.user).create(
            self.get_beneficiary(), **cleaned_data
        )


class CaseNotesView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_CASE_NOTES
    form_class = CaseNoteForm
    route_name = "beneficiaries:case_notes"
    title = "Case notes"
    description = "Structured case-management notes with confidentiality control."
    columns = ("Reference", "Title", "Date", "Confidential")

    def get_rows(self):
        return [
            {
                "cells": [
                    item.reference_number,
                    item.title,
                    item.occurred_on,
                    "Yes" if item.is_confidential else "No",
                ]
            }
            for item in self.get_beneficiary().case_notes.all()
        ]

    def perform_service(self, cleaned_data):
        title = cleaned_data.pop("title")
        content = cleaned_data.pop("content")
        CaseNoteService(user=self.request.user).create(
            self.get_beneficiary(), title, content, **cleaned_data
        )


class FollowUpsView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_FOLLOW_UPS
    form_class = FollowUpForm
    route_name = "beneficiaries:follow_ups"
    title = "Follow-up visits"
    description = "Scheduled and completed follow-up visits and contacts."
    columns = ("Purpose", "Scheduled", "Assigned to", "Status")

    def get_rows(self):
        rows = []
        for item in self.get_beneficiary().follow_ups.select_related(
            "purpose", "assigned_to"
        ):
            actions = []
            if self.can_write() and item.status == FollowUpStatus.PLANNED:
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:follow_up_complete",
                            kwargs={"follow_up_pk": item.pk},
                        ),
                        "label": "Complete",
                        "style": "outline-success",
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.purpose.name if item.purpose else "N/A",
                        item.scheduled_on,
                        item.assigned_to or "Unassigned",
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        FollowUpService(user=self.request.user).create(
            self.get_beneficiary(), **cleaned_data
        )


class AssessmentsView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_ASSESSMENTS
    form_class = AssessmentForm
    route_name = "beneficiaries:assessments"
    title = "Assessments"
    description = "Needs, eligibility, and progress assessments."
    columns = ("Reference", "Date", "Type", "Status")

    def get_rows(self):
        rows = []
        for item in self.get_beneficiary().assessments.select_related(
            "assessment_type"
        ):
            actions = []
            if _can(self.request.user, BENEFICIARIES_SUBMIT) and item.status == "DRAFT":
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:assessment_submit",
                            kwargs={"assessment_pk": item.pk},
                        ),
                        "label": "Submit",
                        "style": "outline-primary",
                    }
                )
            if (
                _can(self.request.user, BENEFICIARIES_APPROVE)
                and item.status == "SUBMITTED"
            ):
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:assessment_approve",
                            kwargs={"assessment_pk": item.pk},
                        ),
                        "label": "Approve",
                        "style": "outline-success",
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.reference_number,
                        item.assessment_date,
                        item.assessment_type.name if item.assessment_type else "N/A",
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        AssessmentService(user=self.request.user).create(
            self.get_beneficiary(), **cleaned_data
        )


class SupportPlansView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_SUPPORT_PLANS
    form_class = SupportPlanForm
    route_name = "beneficiaries:support_plans"
    title = "Support plans"
    description = "Time-bound plans of interventions derived from assessments."
    columns = ("Reference", "Title", "Period", "Coordinator", "Status")

    def get_rows(self):
        rows = []
        for item in self.get_beneficiary().support_plans.select_related(
            "support_coordinator"
        ):
            actions = []
            if self.can_write() and item.status == PlanStatus.DRAFT:
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:support_plan_activate",
                            kwargs={"plan_pk": item.pk},
                        ),
                        "label": "Activate",
                        "style": "outline-success",
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.reference_number,
                        item.title,
                        f"{item.start_date} to {item.end_date or 'open'}",
                        item.support_coordinator or "Unassigned",
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        SupportPlanService(user=self.request.user).create(
            self.get_beneficiary(), **cleaned_data
        )


class ConsentView(BeneficiaryRelatedView):
    permission_required = (
        BENEFICIARIES_VIEW_CONFIDENTIAL,
        BENEFICIARIES_MANAGE_CONSENT,
    )
    write_permission = BENEFICIARIES_MANAGE_CONSENT
    form_class = ConsentForm
    route_name = "beneficiaries:consent"
    title = "Consent"
    description = "Consent and assent records, versioning, and withdrawal."
    columns = ("Reference", "Type", "Provided by", "Valid to", "Status")

    def get_rows(self):
        rows = []
        for item in self.get_beneficiary().consent_records.all():
            actions = []
            if self.can_write() and item.status == ConsentStatus.GRANTED:
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:consent_withdraw",
                            kwargs={"consent_pk": item.pk},
                        ),
                        "label": "Withdraw",
                        "style": "outline-danger",
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.reference_number,
                        item.get_consent_type_display(),
                        item.provided_by,
                        item.valid_to or "No expiry",
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        ConsentService(user=self.request.user).record(
            self.get_beneficiary(),
            consent_type=cleaned_data.pop("consent_type"),
            provided_by=cleaned_data.pop("provided_by"),
            **cleaned_data,
        )


class SafeguardingView(BeneficiaryRelatedView):
    permission_required = (
        BENEFICIARIES_VIEW_CONFIDENTIAL,
        BENEFICIARIES_MANAGE_SAFEGUARDING,
    )
    write_permission = BENEFICIARIES_MANAGE_SAFEGUARDING
    form_class = SafeguardingForm
    route_name = "beneficiaries:safeguarding"
    title = "Safeguarding"
    description = "Restricted safeguarding concerns, actions, and closure."
    columns = ("Reference", "Reported", "Category", "Risk", "Status")

    def get_rows(self):
        rows = []
        for item in self.get_beneficiary().safeguarding_records.select_related(
            "category"
        ):
            actions = []
            if self.can_write() and item.status not in {"RESOLVED", "CLOSED"}:
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:safeguarding_status",
                            kwargs={"record_pk": item.pk},
                        ),
                        "label": "Change status",
                        "style": "outline-primary",
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.reference_number,
                        item.reported_on,
                        item.category.name if item.category else "N/A",
                        item.get_risk_level_display(),
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        SafeguardingService(user=self.request.user).record(
            self.get_beneficiary(), **cleaned_data
        )


class OutcomesView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_OUTCOMES
    form_class = OutcomeForm
    route_name = "beneficiaries:outcomes"
    title = "Outcomes"
    description = "Outcome and result evidence against indicators."
    columns = ("Reference", "Indicator", "Measured", "Value", "Status")

    def get_rows(self):
        return [
            {
                "cells": [
                    item.reference_number,
                    item.indicator_name,
                    item.measurement_date,
                    item.current_value,
                    item.get_status_display(),
                ]
            }
            for item in self.get_beneficiary().outcomes.all()
        ]

    def perform_service(self, cleaned_data):
        OutcomeService(user=self.request.user).record(
            self.get_beneficiary(), **cleaned_data
        )


class ExitsView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_EXITS
    form_class = ExitForm
    route_name = "beneficiaries:exits"
    title = "Exits"
    description = "Exit, graduation, and discontinuation records."
    columns = ("Reference", "Date", "Exit status", "Reason")

    def get_rows(self):
        return [
            {
                "cells": [
                    item.reference_number,
                    item.exit_date,
                    item.get_exit_status_display(),
                    item.reason,
                ]
            }
            for item in self.get_beneficiary().exit_records.all()
        ]

    def perform_service(self, cleaned_data):
        ExitService(user=self.request.user).record(
            self.get_beneficiary(),
            exit_status=cleaned_data.pop("exit_status"),
            reason=cleaned_data.pop("reason"),
            **cleaned_data,
        )


class DocumentsView(BeneficiaryRelatedView):
    permission_required = (BENEFICIARIES_VIEW, BENEFICIARIES_MANAGE_DOCUMENTS)
    write_permission = BENEFICIARIES_MANAGE_DOCUMENTS
    form_class = DocumentForm
    route_name = "beneficiaries:documents"
    title = "Documents"
    description = "Consent-gated, version-tracked beneficiary documents."
    columns = ("Reference", "Title", "Type", "Uploaded", "Status")

    def get_rows(self):
        rows = []
        for item in visible_beneficiary_documents(
            self.request.user, self.get_beneficiary()
        ):
            actions = []
            if item.file:
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:document_download",
                            kwargs={"document_pk": item.pk},
                        ),
                        "label": "Download",
                        "style": "outline-primary",
                        "link": True,
                    }
                )
            if self.can_write() and item.status != DocumentStatus.ARCHIVED:
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:document_archive",
                            kwargs={"document_pk": item.pk},
                        ),
                        "label": "Archive",
                        "style": "outline-danger",
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.reference_number,
                        item.title,
                        item.document_type.name if item.document_type else "N/A",
                        item.uploaded_by or "N/A",
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        title = cleaned_data.pop("title")
        file = cleaned_data.pop("file")
        DocumentService(user=self.request.user).upload(
            self.get_beneficiary(), title=title, file=file, **cleaned_data
        )


class CommunicationsView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_CASE_NOTES
    form_class = CommunicationForm
    route_name = "beneficiaries:communications"
    title = "Communications"
    description = "Retained inbound, outbound, and internal communication history."
    columns = ("Occurred", "Subject", "Channel", "Direction", "Follow-up")

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
            for item in self.get_beneficiary().communications.all()
        ]

    def perform_service(self, cleaned_data):
        CommunicationService(user=self.request.user).record(
            self.get_beneficiary(), **cleaned_data
        )


class FeedbackView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_FEEDBACK
    form_class = FeedbackForm
    route_name = "beneficiaries:feedback"
    title = "Feedback"
    description = "Beneficiary feedback, complaints, and response handling."
    columns = ("Reference", "Date", "Channel", "Complaint", "Status")

    def get_rows(self):
        rows = []
        for item in self.get_beneficiary().feedback_records.all():
            actions = []
            if self.can_write() and item.status == "RECEIVED":
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:feedback_respond",
                            kwargs={"feedback_pk": item.pk},
                        ),
                        "label": "Respond",
                        "style": "outline-primary",
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.reference_number,
                        item.feedback_date,
                        item.get_channel_display(),
                        "Yes" if item.is_complaint else "No",
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        FeedbackService(user=self.request.user).record(
            self.get_beneficiary(), **cleaned_data
        )


class TransfersView(BeneficiaryRelatedView):
    write_permission = BENEFICIARIES_MANAGE_TRANSFERS
    form_class = TransferForm
    route_name = "beneficiaries:transfers"
    title = "Transfers"
    description = "Transfers between programs, projects, or sites."
    columns = ("Reference", "Date", "From", "To", "Status")

    def get_rows(self):
        rows = []
        for item in self.get_beneficiary().transfers.all():
            actions = []
            if self.can_write() and item.status == TransferStatus.PENDING:
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:transfer_complete",
                            kwargs={"transfer_pk": item.pk},
                        ),
                        "label": "Complete",
                        "style": "outline-success",
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.reference_number,
                        item.transfer_date,
                        item.from_program_reference or item.from_site or "N/A",
                        item.to_program_reference or item.to_site or "N/A",
                        item.get_status_display(),
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        TransferService(user=self.request.user).create(
            self.get_beneficiary(), **cleaned_data
        )


class DuplicatesView(BeneficiaryRelatedView):
    permission_required = (BENEFICIARIES_VIEW, BENEFICIARIES_MANAGE_DUPLICATES)
    write_permission = BENEFICIARIES_MANAGE_DUPLICATES
    form_class = DuplicateReviewForm
    route_name = "beneficiaries:duplicates"
    title = "Duplicate review"
    description = "Review and merge possible duplicate beneficiary records."
    columns = ("Candidate", "Match", "Status", "Decision notes")

    def get_form_kwargs(self):
        beneficiary = self.get_beneficiary()
        candidates = _candidate_beneficiaries(self.request.user).exclude(
            pk=beneficiary.pk
        )
        return {"candidates": candidates}

    def get_rows(self):
        rows = []
        beneficiary = self.get_beneficiary()
        for item in beneficiary.duplicate_reviews.select_related(
            "duplicate_candidate", "reviewed_by"
        ):
            actions = []
            if (
                self.can_write()
                and item.review_status == "CONFIRMED_DUPLICATE"
                and not item.merged_into_id
            ):
                actions.append(
                    {
                        "url": reverse(
                            "beneficiaries:duplicate_merge",
                            kwargs={"review_pk": item.pk},
                        ),
                        "label": "Merge",
                        "style": "outline-success",
                    }
                )
            rows.append(
                {
                    "cells": [
                        item.duplicate_candidate.full_name,
                        f"{item.match_score}%",
                        item.get_review_status_display(),
                        item.decision_notes or "N/A",
                    ],
                    "actions": actions,
                }
            )
        return rows

    def perform_service(self, cleaned_data):
        candidate = cleaned_data.pop("candidate")
        DuplicateService(user=self.request.user).review(
            self.get_beneficiary(), candidate, **cleaned_data
        )


class ReferralStatusView(BeneficiaryPermissionMixin, FormView):
    form_class = ReferralStatusForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_MANAGE_REFERRALS

    def get_referral(self):
        return _scoped_related(Referral, self.request.user, self.kwargs["referral_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        referral = self.get_referral()
        context.update(
            {
                "title": "Update referral status",
                "beneficiary": referral.beneficiary,
                "cancel_url": reverse(
                    "beneficiaries:referrals",
                    kwargs={"pk": referral.beneficiary_id},
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            ReferralService(user=self.request.user).change_status(
                self.get_referral(),
                form.cleaned_data["status"],
                form.cleaned_data.get("response_notes", ""),
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Referral status updated.")
        return redirect(
            "beneficiaries:referrals", pk=self.get_referral().beneficiary_id
        )


class EnrollmentStatusView(BeneficiaryPermissionMixin, FormView):
    form_class = EnrollmentStatusForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_MANAGE_ENROLLMENTS

    def get_enrollment(self):
        return _scoped_related(
            BeneficiaryEnrollment, self.request.user, self.kwargs["enrollment_pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollment = self.get_enrollment()
        context.update(
            {
                "title": "Change enrollment status",
                "beneficiary": enrollment.beneficiary,
                "cancel_url": reverse(
                    "beneficiaries:enrollments",
                    kwargs={"pk": enrollment.beneficiary_id},
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            EnrollmentService(user=self.request.user).change_status(
                self.get_enrollment(),
                form.cleaned_data["status"],
                form.cleaned_data.get("reason", ""),
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Enrollment status updated.")
        return redirect(
            "beneficiaries:enrollments", pk=self.get_enrollment().beneficiary_id
        )


class SafeguardingStatusView(BeneficiaryPermissionMixin, FormView):
    form_class = SafeguardingStatusForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_MANAGE_SAFEGUARDING

    def get_record(self):
        return _scoped_related(
            SafeguardingRecord, self.request.user, self.kwargs["record_pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = self.get_record()
        context.update(
            {
                "title": "Change safeguarding status",
                "beneficiary": record.beneficiary,
                "cancel_url": reverse(
                    "beneficiaries:safeguarding",
                    kwargs={"pk": record.beneficiary_id},
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            SafeguardingService(user=self.request.user).change_status(
                self.get_record(),
                form.cleaned_data["status"],
                form.cleaned_data.get("notes", ""),
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Safeguarding status updated.")
        return redirect(
            "beneficiaries:safeguarding", pk=self.get_record().beneficiary_id
        )


class ConsentWithdrawView(BeneficiaryPermissionMixin, FormView):
    form_class = ConsentWithdrawForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_MANAGE_CONSENT

    def get_consent(self):
        return _scoped_related(
            ConsentRecord, self.request.user, self.kwargs["consent_pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        consent = self.get_consent()
        context.update(
            {
                "title": "Withdraw consent",
                "beneficiary": consent.beneficiary,
                "cancel_url": reverse(
                    "beneficiaries:consent", kwargs={"pk": consent.beneficiary_id}
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            ConsentService(user=self.request.user).withdraw(
                self.get_consent(), form.cleaned_data["reason"]
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Consent withdrawn.")
        return redirect("beneficiaries:consent", pk=self.get_consent().beneficiary_id)


class ServiceDeliverView(BeneficiaryPermissionMixin, FormView):
    form_class = ServiceDeliveryCompleteForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_MANAGE_SERVICES

    def get_service(self):
        return _scoped_related(
            ServiceDeliveryRecord, self.request.user, self.kwargs["service_pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.get_service()
        context.update(
            {
                "title": "Mark service as delivered",
                "beneficiary": service.beneficiary,
                "cancel_url": reverse(
                    "beneficiaries:services", kwargs={"pk": service.beneficiary_id}
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            ServiceDeliveryService(user=self.request.user).mark_delivered(
                self.get_service(), form.cleaned_data.get("outcome_notes", "")
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Service marked as delivered.")
        return redirect("beneficiaries:services", pk=self.get_service().beneficiary_id)


class FollowUpCompleteView(BeneficiaryPermissionMixin, FormView):
    form_class = FollowUpCompleteForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_MANAGE_FOLLOW_UPS

    def get_follow_up(self):
        return _scoped_related(
            FollowUpVisit, self.request.user, self.kwargs["follow_up_pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        follow_up = self.get_follow_up()
        context.update(
            {
                "title": "Complete follow-up visit",
                "beneficiary": follow_up.beneficiary,
                "cancel_url": reverse(
                    "beneficiaries:follow_ups", kwargs={"pk": follow_up.beneficiary_id}
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            FollowUpService(user=self.request.user).complete(
                self.get_follow_up(), **form.cleaned_data
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Follow-up completed.")
        return redirect(
            "beneficiaries:follow_ups", pk=self.get_follow_up().beneficiary_id
        )


class AssessmentSubmitView(BeneficiaryPermissionMixin, FormView):
    form_class = EmptyConfirmationForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_SUBMIT

    def get_assessment(self):
        return _scoped_related(
            BeneficiaryAssessment, self.request.user, self.kwargs["assessment_pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = self.get_assessment()
        context.update(
            {
                "title": "Submit assessment for approval",
                "beneficiary": assessment.beneficiary,
                "cancel_url": reverse(
                    "beneficiaries:assessments",
                    kwargs={"pk": assessment.beneficiary_id},
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            AssessmentService(user=self.request.user).submit(self.get_assessment())
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Assessment submitted.")
        return redirect(
            "beneficiaries:assessments", pk=self.get_assessment().beneficiary_id
        )


class AssessmentApproveView(BeneficiaryPermissionMixin, FormView):
    form_class = EmptyConfirmationForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_APPROVE

    def get_assessment(self):
        return _scoped_related(
            BeneficiaryAssessment, self.request.user, self.kwargs["assessment_pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = self.get_assessment()
        context.update(
            {
                "title": "Approve assessment",
                "beneficiary": assessment.beneficiary,
                "cancel_url": reverse(
                    "beneficiaries:assessments",
                    kwargs={"pk": assessment.beneficiary_id},
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            AssessmentService(user=self.request.user).approve(self.get_assessment())
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Assessment approved.")
        return redirect(
            "beneficiaries:assessments", pk=self.get_assessment().beneficiary_id
        )


class SupportPlanActivateView(BeneficiaryPermissionMixin, FormView):
    form_class = EmptyConfirmationForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_MANAGE_SUPPORT_PLANS

    def get_plan(self):
        return _scoped_related(SupportPlan, self.request.user, self.kwargs["plan_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.get_plan()
        context.update(
            {
                "title": "Activate support plan",
                "beneficiary": plan.beneficiary,
                "cancel_url": reverse(
                    "beneficiaries:support_plans",
                    kwargs={"pk": plan.beneficiary_id},
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            SupportPlanService(user=self.request.user).activate(self.get_plan())
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Support plan activated.")
        return redirect(
            "beneficiaries:support_plans", pk=self.get_plan().beneficiary_id
        )


class TransferCompleteView(BeneficiaryPermissionMixin, FormView):
    form_class = TransferCompleteForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_MANAGE_TRANSFERS

    def get_transfer(self):
        return _scoped_related(
            TransferRecord, self.request.user, self.kwargs["transfer_pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transfer = self.get_transfer()
        context.update(
            {
                "title": "Complete transfer",
                "beneficiary": transfer.beneficiary,
                "cancel_url": reverse(
                    "beneficiaries:transfers", kwargs={"pk": transfer.beneficiary_id}
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            TransferService(user=self.request.user).complete(
                self.get_transfer(), form.cleaned_data.get("handover_notes", "")
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Transfer completed.")
        return redirect(
            "beneficiaries:transfers", pk=self.get_transfer().beneficiary_id
        )


class FeedbackRespondView(BeneficiaryPermissionMixin, FormView):
    form_class = FeedbackResponseForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_MANAGE_FEEDBACK

    def get_feedback(self):
        return _scoped_related(
            FeedbackRecord, self.request.user, self.kwargs["feedback_pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feedback = self.get_feedback()
        context.update(
            {
                "title": "Respond to feedback",
                "beneficiary": feedback.beneficiary,
                "cancel_url": reverse(
                    "beneficiaries:feedback", kwargs={"pk": feedback.beneficiary_id}
                ),
            }
        )
        return context

    def form_valid(self, form):
        try:
            FeedbackService(user=self.request.user).respond(
                self.get_feedback(),
                form.cleaned_data["response"],
                close=form.cleaned_data["close"],
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Feedback response recorded.")
        return redirect("beneficiaries:feedback", pk=self.get_feedback().beneficiary_id)


class DuplicateMergeView(BeneficiaryPermissionMixin, FormView):
    form_class = EmptyConfirmationForm
    template_name = "beneficiaries/workflow_form.html"
    permission_required = BENEFICIARIES_MANAGE_DUPLICATES

    def get_review(self):
        return get_object_or_404(
            DuplicateReviewRecord.objects.filter(
                beneficiary__in=visible_beneficiaries(
                    self.request.user, include_archived=True
                )
            ),
            pk=self.kwargs["review_pk"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review = self.get_review()
        context.update(
            {
                "title": "Merge duplicate records",
                "beneficiary": review.beneficiary,
                "cancel_url": reverse(
                    "beneficiaries:duplicates",
                    kwargs={"pk": review.beneficiary_id},
                ),
            }
        )
        return context

    def form_valid(self, form):
        review = self.get_review()
        try:
            DuplicateService(user=self.request.user).merge(
                review, merged_into=review.beneficiary
            )
        except ValidationError as exc:
            _apply_service_errors(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Duplicate records merged.")
        return redirect("beneficiaries:duplicates", pk=review.beneficiary_id)


class GuardianPrimaryView(BeneficiaryPermissionMixin, View):
    permission_required = BENEFICIARIES_MANAGE_GUARDIANS

    def post(self, request, *args, **kwargs):
        guardian = _scoped_related(GuardianRecord, request.user, kwargs["guardian_pk"])
        GuardianService(user=request.user).set_primary(guardian)
        messages.success(request, "Guardian set as primary.")
        return redirect("beneficiaries:guardians", pk=guardian.beneficiary_id)


class GuardianDeactivateView(BeneficiaryPermissionMixin, View):
    permission_required = BENEFICIARIES_MANAGE_GUARDIANS

    def post(self, request, *args, **kwargs):
        guardian = _scoped_related(GuardianRecord, request.user, kwargs["guardian_pk"])
        GuardianService(user=request.user).deactivate(guardian)
        messages.success(request, "Guardian deactivated.")
        return redirect("beneficiaries:guardians", pk=guardian.beneficiary_id)


class HouseholdMemberRemoveView(BeneficiaryPermissionMixin, View):
    permission_required = BENEFICIARIES_MANAGE_HOUSEHOLDS

    def post(self, request, *args, **kwargs):
        member = _scoped_related(HouseholdMember, request.user, kwargs["member_pk"])
        HouseholdService(user=request.user).remove_member(member)
        messages.success(request, "Household member removed.")
        return redirect("beneficiaries:household_detail", pk=member.household_id)


class GroupMemberRemoveView(BeneficiaryPermissionMixin, View):
    permission_required = BENEFICIARIES_MANAGE_GROUPS

    def post(self, request, *args, **kwargs):
        membership = _scoped_related(
            GroupMembership, request.user, kwargs["membership_pk"]
        )
        GroupService(user=request.user).remove_member(membership)
        messages.success(request, "Group member removed.")
        return redirect("beneficiaries:group_detail", pk=membership.group_id)


class DocumentDownloadView(BeneficiaryPermissionMixin, View):
    permission_required = (BENEFICIARIES_VIEW, BENEFICIARIES_MANAGE_DOCUMENTS)

    def get(self, request, *args, **kwargs):
        document = _scoped_related(
            BeneficiaryDocument, request.user, kwargs["document_pk"]
        )
        if not document.file:
            raise Http404("Document has no file.")
        if not user_can_access_beneficiary(
            request.user, document.beneficiary, include_archived=True
        ):
            raise PermissionDenied
        response = FileResponse(document.file.open("rb"))
        response["Content-Disposition"] = (
            f'attachment; filename="{Path(document.file.name).name}"'
        )
        response["Cache-Control"] = "private, no-store"
        return response


class DocumentArchiveView(BeneficiaryPermissionMixin, View):
    permission_required = BENEFICIARIES_MANAGE_DOCUMENTS

    def post(self, request, *args, **kwargs):
        document = _scoped_related(
            BeneficiaryDocument, request.user, kwargs["document_pk"]
        )
        DocumentService(user=request.user).archive(document)
        messages.success(request, "Document archived.")
        return redirect("beneficiaries:documents", pk=document.beneficiary_id)


class BeneficiaryRegisterExportView(BeneficiaryPermissionMixin, View):
    permission_required = (BENEFICIARIES_VIEW, BENEFICIARIES_EXPORT)

    def get(self, request, *args, **kwargs):
        return beneficiary_register_csv_response(request.user)


class BeneficiaryRegisterXlsxExportView(BeneficiaryPermissionMixin, View):
    permission_required = (BENEFICIARIES_VIEW, BENEFICIARIES_EXPORT)

    def get(self, request, *args, **kwargs):
        return beneficiary_register_xlsx_response(request.user)


class BeneficiaryRegisterDocxExportView(BeneficiaryPermissionMixin, View):
    permission_required = (BENEFICIARIES_VIEW, BENEFICIARIES_EXPORT)

    def get(self, request, *args, **kwargs):
        return beneficiary_register_docx_response(request.user)


class BeneficiaryRegisterPdfExportView(BeneficiaryPermissionMixin, View):
    permission_required = (BENEFICIARIES_VIEW, BENEFICIARIES_EXPORT)

    def get(self, request, *args, **kwargs):
        return beneficiary_register_pdf_response(request.user)


class BeneficiaryProfileDocxExportView(BeneficiaryPermissionMixin, View):
    permission_required = (BENEFICIARIES_VIEW, BENEFICIARIES_EXPORT)

    def get(self, request, *args, **kwargs):
        beneficiary = _scoped_beneficiary(
            request.user, kwargs["pk"], include_archived=True
        )
        return beneficiary_profile_docx_response(request.user, beneficiary)


class BeneficiaryAutocompleteView(BeneficiaryPermissionMixin, View):
    """Lightweight JSON search for beneficiary selection widgets."""

    permission_required = BENEFICIARIES_VIEW

    def get(self, request, *args, **kwargs):
        term = request.GET.get("q", "").strip()
        queryset = visible_beneficiaries(request.user)
        if term:
            queryset = queryset.filter(
                Q(reference_number__icontains=term)
                | Q(first_name__icontains=term)
                | Q(last_name__icontains=term)
            )
        results = [
            {"id": str(item.pk), "text": f"{item.full_name} ({item.reference_number})"}
            for item in queryset[:20]
        ]
        return JsonResponse({"results": results})
