"""
Views for the membership management module.
"""

from __future__ import annotations

import csv
from typing import Any, ClassVar

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from django.views.generic.base import ContextMixin

from apps.rbac.mixins import PermissionRequiredMixin

from .constants import ApplicationStatus
from .forms import (
    CommitteeAssignmentForm,
    MemberLeaveForm,
    MemberParticipationForm,
    MemberProfileForm,
    MemberRecognitionForm,
    MembershipApplicationForm,
    MembershipExitForm,
    MembershipPaymentForm,
    MembershipTransferForm,
    MembershipUpgradeForm,
)
from .models import (
    MemberCommitteeAssignment,
    MemberLeave,
    MemberParticipation,
    MemberProfile,
    MemberRecognition,
    MembershipApplication,
    MembershipCard,
    MembershipExit,
    MembershipPayment,
    MembershipRenewal,
    MembershipTransfer,
    MembershipUpgrade,
)
from .permissions import (
    MEMBERSHIP_APPROVE,
    MEMBERSHIP_ASSIGN,
    MEMBERSHIP_CREATE,
    MEMBERSHIP_EXPORT,
    MEMBERSHIP_ISSUE_CARD,
    MEMBERSHIP_MANAGE_EXIT,
    MEMBERSHIP_MANAGE_LEAVE,
    MEMBERSHIP_MANAGE_PARTICIPATION,
    MEMBERSHIP_RECORD_PAYMENT,
    MEMBERSHIP_RENEW,
    MEMBERSHIP_REVIEW,
    MEMBERSHIP_TRANSFER,
    MEMBERSHIP_UPDATE,
    MEMBERSHIP_VERIFY_PAYMENT,
    MEMBERSHIP_VIEW,
)
from .services import (
    MemberCommitteeService,
    MemberLeaveService,
    MemberParticipationService,
    MemberRecognitionService,
    MembershipAnalyticsService,
    MembershipApplicationService,
    MembershipCardService,
    MembershipExitService,
    MembershipPaymentService,
    MembershipRenewalService,
    MembershipStatusService,
    MembershipTransferService,
    MembershipUpgradeService,
)
from .utils import generate_member_qr_base64


class MembershipDashboardView(PermissionRequiredMixin, TemplateView):
    template_name = "memberships/dashboard.html"
    permission_required = MEMBERSHIP_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = MembershipAnalyticsService(user=self.request.user)
        context.update(service.dashboard_summary())
        context["fee_summary"] = service.fee_collection_summary()
        return context


class MembershipDirectoryView(PermissionRequiredMixin, ListView):
    model = MemberProfile
    template_name = "memberships/directory.html"
    context_object_name = "members"
    paginate_by = 25
    permission_required = MEMBERSHIP_VIEW

    def get_queryset(self):
        qs = MemberProfile.objects.filter(is_deleted=False).select_related(
            "user", "status", "category", "membership_type", "level"
        )
        search_query = self.request.GET.get("q", "").strip()
        status_filter = self.request.GET.get("status", "").strip()
        category_filter = self.request.GET.get("category", "").strip()

        if search_query:
            qs = qs.filter(
                Q(user__first_name__icontains=search_query)
                | Q(user__last_name__icontains=search_query)
                | Q(membership_id__icontains=search_query)
                | Q(phone_primary__icontains=search_query)
                | Q(district__icontains=search_query)
            )
        if status_filter:
            qs = qs.filter(status__code=status_filter)
        if category_filter:
            qs = qs.filter(category__code=category_filter)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_codes"] = (
            MemberProfile.objects.exclude(status__isnull=True)
            .values_list("status__code", "status__name")
            .distinct()
            .order_by("status__name")
        )
        context["category_codes"] = (
            MemberProfile.objects.exclude(category__isnull=True)
            .values_list("category__code", "category__name")
            .distinct()
            .order_by("category__name")
        )
        return context


class MemberDetailView(PermissionRequiredMixin, DetailView):
    model = MemberProfile
    template_name = "memberships/profile_detail.html"
    context_object_name = "member"
    permission_required = MEMBERSHIP_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.object
        context["card"] = getattr(member, "membership_card", None)
        context["renewals"] = member.renewals.all()[:5]
        context["payments"] = member.payments.all()[:5]
        context["committee_assignments"] = member.committee_assignments.all()
        context["participation_records"] = member.participation_records.all()[:5]
        context["recognitions"] = member.recognitions.all()[:5]
        context["leaves"] = member.leaves.all()[:5]
        context["documents"] = member.documents.all()[:5]
        context["status_history"] = member.status_history.all()[:10]
        context["qr_code"] = generate_member_qr_base64(
            member.membership_id or str(member.id)
        )
        return context


class MembershipFormViewMixin(ContextMixin):
    """Mixin providing a shared form template and a configurable page title."""

    template_name: ClassVar[str | None] = "memberships/form.html"
    page_title: ClassVar[str] = "Membership Form"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        return context


class MemberCreateView(MembershipFormViewMixin, PermissionRequiredMixin, CreateView):
    model = MemberProfile
    form_class = MemberProfileForm
    permission_required = MEMBERSHIP_CREATE
    page_title = "New Member Profile"
    success_url = reverse_lazy("memberships:directory")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Member profile updated. Registration via applications is recommended.",
        )
        return super().form_valid(form)


class MemberUpdateView(MembershipFormViewMixin, PermissionRequiredMixin, UpdateView):
    model = MemberProfile
    form_class = MemberProfileForm
    permission_required = MEMBERSHIP_UPDATE
    page_title = "Edit Member Profile"

    def get_success_url(self):
        messages.success(self.request, "Member profile updated successfully.")
        return reverse_lazy("memberships:detail", kwargs={"pk": self.object.pk})


class MemberStatusActionView(PermissionRequiredMixin, View):
    permission_required = MEMBERSHIP_UPDATE

    def post(self, request, pk):
        member = get_object_or_404(MemberProfile, pk=pk)
        action = request.POST.get("action")
        reason = request.POST.get("reason", "")
        service = MembershipStatusService(user=request.user)

        if action == "activate":
            service.activate(member, reason=reason)
            messages.success(request, "Membership activated.")
        elif action == "deactivate":
            service.deactivate(member, reason=reason)
            messages.success(request, "Membership deactivated.")
        elif action == "suspend":
            from datetime import date as _date

            service.suspend(member, reason=reason, effective_date=_date.today())
            messages.success(request, "Membership suspended.")
        elif action == "archive":
            service.archive(member, reason=reason)
            messages.success(request, "Membership archived.")
        elif action == "restore":
            service.restore(member, reason=reason)
            messages.success(request, "Membership restored.")
        return redirect("memberships:detail", pk=member.pk)


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------


class ApplicationListView(PermissionRequiredMixin, ListView):
    model = MembershipApplication
    template_name = "memberships/application_list.html"
    context_object_name = "applications"
    paginate_by = 25
    permission_required = MEMBERSHIP_VIEW

    def get_queryset(self):
        qs = MembershipApplication.objects.select_related("applicant", "category")
        status_filter = self.request.GET.get("status", "").strip()
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = ApplicationStatus.choices
        return context


class ApplicationCreateView(MembershipFormViewMixin, CreateView):
    """Public self-service application form."""

    model = MembershipApplication
    form_class = MembershipApplicationForm
    page_title = "Apply for Membership"
    success_url = reverse_lazy("memberships:application_success")

    def form_valid(self, form):
        service = MembershipApplicationService(user=self.request.user)
        data = form.cleaned_data
        application = service.submit_application(
            applicant=self.request.user,
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            category=data.get("category"),
            membership_type=data.get("membership_type"),
            level=data.get("level"),
            phone=data.get("phone", ""),
            gender=data.get("gender", ""),
            date_of_birth=data.get("date_of_birth"),
            nationality=data.get("nationality", ""),
            national_id=data.get("national_id", ""),
            occupation=data.get("occupation", ""),
            education_level=data.get("education_level", ""),
            province=data.get("province", ""),
            district=data.get("district", ""),
            community=data.get("community", ""),
            skills=data.get("skills", ""),
            interests=data.get("interests", ""),
            referral_source=data.get("referral_source", ""),
            declaration_agreed=data.get("declaration_agreed", False),
            responsibilities_acknowledged=data.get(
                "responsibilities_acknowledged", False
            ),
        )
        messages.success(
            self.request,
            f"Application {application.reference_number} submitted successfully.",
        )
        return redirect("memberships:application_detail", pk=application.pk)


class ApplicationDetailView(PermissionRequiredMixin, DetailView):
    model = MembershipApplication
    template_name = "memberships/application_detail.html"
    context_object_name = "application"
    permission_required = MEMBERSHIP_VIEW


class ApplicationSuccessView(TemplateView):
    template_name = "memberships/application_success.html"


class ApplicationReviewView(PermissionRequiredMixin, View):
    permission_required = MEMBERSHIP_REVIEW

    def post(self, request, pk):
        application = get_object_or_404(MembershipApplication, pk=pk)
        action = request.POST.get("action")
        notes = request.POST.get("notes", "")
        service = MembershipApplicationService(user=request.user)

        if action == "review":
            service.start_review(application)
            messages.success(request, "Application moved into review.")
        elif action == "approve":
            service.approve_application(application, decision_notes=notes)
            messages.success(request, "Application approved and member registered.")
        elif action == "return":
            service.return_application(application, decision_notes=notes)
            messages.success(request, "Application returned for correction.")
        elif action == "reject":
            service.reject_application(application, decision_notes=notes)
            messages.success(request, "Application rejected.")
        return redirect("memberships:application_detail", pk=application.pk)


# ---------------------------------------------------------------------------
# Renewals, Upgrades, Transfers
# ---------------------------------------------------------------------------


class RenewalListView(PermissionRequiredMixin, ListView):
    model = MembershipRenewal
    template_name = "memberships/renewal_list.html"
    context_object_name = "renewals"
    permission_required = MEMBERSHIP_VIEW


class RenewalApproveView(PermissionRequiredMixin, View):
    permission_required = MEMBERSHIP_RENEW

    def post(self, request, pk):
        renewal = get_object_or_404(MembershipRenewal, pk=pk)
        approve = request.POST.get("action") == "approve"
        service = MembershipRenewalService(user=request.user)
        service.approve_renewal(renewal, approve=approve)
        messages.success(request, f"Renewal {'approved' if approve else 'rejected'}.")
        return redirect("memberships:renewal_list")


class TransferListView(PermissionRequiredMixin, ListView):
    model = MembershipTransfer
    template_name = "memberships/transfer_list.html"
    context_object_name = "transfers"
    permission_required = MEMBERSHIP_VIEW


class TransferCreateView(MembershipFormViewMixin, PermissionRequiredMixin, CreateView):
    model = MembershipTransfer
    form_class = MembershipTransferForm
    permission_required = MEMBERSHIP_TRANSFER
    page_title = "Request Membership Transfer"

    def form_valid(self, form):
        service = MembershipTransferService(user=self.request.user)
        service.request_transfer(**form.cleaned_data)
        messages.success(self.request, "Transfer request recorded.")
        return redirect("memberships:transfer_list")


class TransferApproveView(PermissionRequiredMixin, View):
    permission_required = MEMBERSHIP_TRANSFER

    def post(self, request, pk):
        transfer = get_object_or_404(MembershipTransfer, pk=pk)
        approve = request.POST.get("action") == "approve"
        service = MembershipTransferService(user=request.user)
        service.approve_transfer(transfer, approve=approve)
        messages.success(request, f"Transfer {'approved' if approve else 'rejected'}.")
        return redirect("memberships:transfer_list")


class UpgradeCreateView(MembershipFormViewMixin, PermissionRequiredMixin, CreateView):
    model = MembershipUpgrade
    form_class = MembershipUpgradeForm
    permission_required = MEMBERSHIP_TRANSFER
    page_title = "Request Membership Upgrade"

    def form_valid(self, form):
        service = MembershipUpgradeService(user=self.request.user)
        service.request_upgrade(**form.cleaned_data)
        messages.success(self.request, "Upgrade request recorded.")
        return redirect("memberships:directory")


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------


class PaymentListView(PermissionRequiredMixin, ListView):
    model = MembershipPayment
    template_name = "memberships/payment_list.html"
    context_object_name = "payments"
    permission_required = MEMBERSHIP_VIEW


class PaymentCreateView(MembershipFormViewMixin, PermissionRequiredMixin, CreateView):
    model = MembershipPayment
    form_class = MembershipPaymentForm
    permission_required = MEMBERSHIP_RECORD_PAYMENT
    page_title = "Record Membership Payment"

    def form_valid(self, form):
        data = form.cleaned_data
        service = MembershipPaymentService(user=self.request.user)
        payment = service.record_payment(
            member=data["member"],
            amount=data["amount"],
            payment_method=data["payment_method"],
            payment_date=data.get("payment_date"),
            fee=data.get("fee"),
            currency=data.get("currency", "ZMW"),
            transaction_reference=data.get("transaction_reference", ""),
            period_from=data.get("period_from"),
            period_to=data.get("period_to"),
            receipt_file=data.get("receipt_file"),
        )
        messages.success(self.request, f"Payment {payment.receipt_number} recorded.")
        return redirect("memberships:payment_list")


class PaymentVerifyView(PermissionRequiredMixin, View):
    permission_required = MEMBERSHIP_VERIFY_PAYMENT

    def post(self, request, pk):
        payment = get_object_or_404(MembershipPayment, pk=pk)
        service = MembershipPaymentService(user=request.user)
        service.verify_payment(payment)
        messages.success(request, "Payment verified.")
        return redirect("memberships:payment_list")


class CardListView(PermissionRequiredMixin, ListView):
    model = MembershipCard
    template_name = "memberships/card_list.html"
    context_object_name = "cards"
    permission_required = MEMBERSHIP_VIEW


class CardIssueView(PermissionRequiredMixin, View):
    permission_required = MEMBERSHIP_ISSUE_CARD

    def post(self, request, pk):
        member = get_object_or_404(MemberProfile, pk=pk)
        service = MembershipCardService(user=request.user)
        card = service.issue_card(member)
        messages.success(request, f"Card {card.card_number} issued.")
        return redirect("memberships:detail", pk=member.pk)


class CardRevokeView(PermissionRequiredMixin, View):
    permission_required = MEMBERSHIP_ISSUE_CARD

    def post(self, request, pk):
        card = get_object_or_404(MembershipCard, pk=pk)
        reason = request.POST.get("reason", "")
        service = MembershipCardService(user=request.user)
        service.revoke_card(card, reason=reason)
        messages.success(request, "Card revoked.")
        return redirect("memberships:detail", pk=card.member_id)


# ---------------------------------------------------------------------------
# Participation, Committees, Recognition, Leave
# ---------------------------------------------------------------------------


class ParticipationCreateView(
    MembershipFormViewMixin, PermissionRequiredMixin, CreateView
):
    model = MemberParticipation
    form_class = MemberParticipationForm
    permission_required = MEMBERSHIP_MANAGE_PARTICIPATION
    page_title = "Record Member Participation"

    def form_valid(self, form):
        data = form.cleaned_data
        service = MemberParticipationService(user=self.request.user)
        service.record_participation(**data)
        messages.success(self.request, "Participation recorded.")
        return redirect("memberships:detail", pk=data["member"].pk)


class CommitteeAssignView(MembershipFormViewMixin, PermissionRequiredMixin, CreateView):
    model = MemberCommitteeAssignment
    form_class = CommitteeAssignmentForm
    permission_required = MEMBERSHIP_ASSIGN
    page_title = "Assign Member to Committee"

    def form_valid(self, form):
        data = form.cleaned_data
        service = MemberCommitteeService(user=self.request.user)
        service.assign_member(**data)
        messages.success(self.request, "Committee assignment recorded.")
        return redirect("memberships:detail", pk=data["member"].pk)


class RecognitionCreateView(
    MembershipFormViewMixin, PermissionRequiredMixin, CreateView
):
    model = MemberRecognition
    form_class = MemberRecognitionForm
    permission_required = MEMBERSHIP_APPROVE
    page_title = "Record Member Recognition"

    def form_valid(self, form):
        data = form.cleaned_data
        service = MemberRecognitionService(user=self.request.user)
        service.record_recognition(**data)
        messages.success(self.request, "Recognition recorded.")
        return redirect("memberships:detail", pk=data["member"].pk)


class LeaveListView(PermissionRequiredMixin, ListView):
    model = MemberLeave
    template_name = "memberships/leave_list.html"
    context_object_name = "leaves"
    permission_required = MEMBERSHIP_VIEW


class LeaveCreateView(MembershipFormViewMixin, PermissionRequiredMixin, CreateView):
    model = MemberLeave
    form_class = MemberLeaveForm
    permission_required = MEMBERSHIP_MANAGE_LEAVE
    page_title = "Apply for Member Leave"

    def form_valid(self, form):
        data = form.cleaned_data
        service = MemberLeaveService(user=self.request.user)
        service.apply_leave(**data)
        messages.success(self.request, "Leave application submitted.")
        return redirect("memberships:leave_list")


class LeaveApproveView(PermissionRequiredMixin, View):
    permission_required = MEMBERSHIP_MANAGE_LEAVE

    def post(self, request, pk):
        leave = get_object_or_404(MemberLeave, pk=pk)
        approve = request.POST.get("action") == "approve"
        notes = request.POST.get("notes", "")
        service = MemberLeaveService(user=request.user)
        service.approve_leave(leave, approve=approve, notes=notes)
        messages.success(request, f"Leave {'approved' if approve else 'rejected'}.")
        return redirect("memberships:leave_list")


# ---------------------------------------------------------------------------
# Exit & Alumni
# ---------------------------------------------------------------------------


class ExitListView(PermissionRequiredMixin, ListView):
    model = MembershipExit
    template_name = "memberships/exit_list.html"
    context_object_name = "exits"
    permission_required = MEMBERSHIP_VIEW


class ExitCreateView(MembershipFormViewMixin, PermissionRequiredMixin, CreateView):
    model = MembershipExit
    form_class = MembershipExitForm
    permission_required = MEMBERSHIP_MANAGE_EXIT
    page_title = "Initiate Membership Exit"

    def form_valid(self, form):
        data = form.cleaned_data
        service = MembershipExitService(user=self.request.user)
        service.initiate_exit(
            member=data["member"],
            exit_type=data["exit_type"],
            reason=data.get("reason", ""),
            effective_date=data.get("effective_date"),
            transition_to_alumni=data.get("transition_to_alumni", True),
        )
        messages.success(self.request, "Exit process initiated.")
        return redirect("memberships:exit_list")


class ExitCompleteView(PermissionRequiredMixin, View):
    permission_required = MEMBERSHIP_MANAGE_EXIT

    def post(self, request, pk):
        exit_rec = get_object_or_404(MembershipExit, pk=pk)
        service = MembershipExitService(user=request.user)
        service.complete_exit(
            exit_rec,
            exit_interview_notes=request.POST.get("notes", ""),
            assets_returned=request.POST.get("assets_returned") == "on",
            documents_returned=request.POST.get("documents_returned") == "on",
        )
        messages.success(request, "Exit completed.")
        return redirect("memberships:exit_list")


class MemberIdCardView(PermissionRequiredMixin, DetailView):
    model = MemberProfile
    template_name = "memberships/id_card.html"
    context_object_name = "member"
    permission_required = MEMBERSHIP_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card"] = getattr(self.object, "membership_card", None)
        context["qr_code"] = generate_member_qr_base64(
            self.object.membership_id or str(self.object.id)
        )
        return context


class MemberReportsView(PermissionRequiredMixin, TemplateView):
    template_name = "memberships/reports.html"
    permission_required = MEMBERSHIP_EXPORT

    def get(self, request, *args, **kwargs):
        export_type = request.GET.get("export")
        if export_type == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                'attachment; filename="membership_register.csv"'
            )
            writer = csv.writer(response)
            writer.writerow(
                [
                    "Membership ID",
                    "Full Name",
                    "Email",
                    "Phone",
                    "Category",
                    "Type",
                    "Level",
                    "Status",
                    "Province",
                    "District",
                    "Date Joined",
                    "Expiry Date",
                ]
            )
            profiles = MemberProfile.objects.filter(is_deleted=False).select_related(
                "user", "status", "category", "membership_type", "level"
            )
            for p in profiles:
                writer.writerow(
                    [
                        p.membership_id,
                        p.user.full_name,
                        p.email_personal,
                        p.phone_primary,
                        p.category.name if p.category else "",
                        p.membership_type.name if p.membership_type else "",
                        p.level.name if p.level else "",
                        p.status.name if p.status else "",
                        p.province,
                        p.district,
                        p.date_joined,
                        p.expiry_date,
                    ]
                )
            return response
        return super().get(request, *args, **kwargs)
