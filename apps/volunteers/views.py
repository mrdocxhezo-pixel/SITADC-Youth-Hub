"""Permission-aware views for volunteer management."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q, Sum
from django.http import FileResponse, Http404, HttpRequest, HttpResponseBadRequest
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

from apps.rbac.authorization import user_has_permission
from apps.rbac.mixins import PermissionRequiredMixin

from .constants import (
    ApplicationStatus,
    AttendanceStatus,
    VolunteerAuditAction,
    VolunteerStatus,
)
from .exports import (
    export_volunteer_csv,
    export_volunteer_docx,
    export_volunteer_pdf,
    export_volunteer_xlsx,
)
from .forms import (
    VolunteerActivityLogForm,
    VolunteerApplicationForm,
    VolunteerAssignmentForm,
    VolunteerAttendanceForm,
    VolunteerCategoryForm,
    VolunteerCommunicationForm,
    VolunteerDisciplinaryDecisionForm,
    VolunteerDisciplinaryRecordForm,
    VolunteerDocumentReviewForm,
    VolunteerDocumentUploadForm,
    VolunteerExitForm,
    VolunteerInterviewForm,
    VolunteerLeaveForm,
    VolunteerOnboardingForm,
    VolunteerPerformanceForm,
    VolunteerProfileForm,
    VolunteerRecognitionForm,
    VolunteerRecruitmentForm,
    VolunteerRegistrationForm,
    VolunteerScreeningForm,
    VolunteerTrainingForm,
)
from .models import (
    VolunteerActivityLog,
    VolunteerApplication,
    VolunteerAssignment,
    VolunteerAttendance,
    VolunteerCategory,
    VolunteerCommunication,
    VolunteerDisciplinaryRecord,
    VolunteerDocument,
    VolunteerExit,
    VolunteerLeave,
    VolunteerPerformance,
    VolunteerProfile,
    VolunteerRecognition,
    VolunteerRecruitment,
    VolunteerTraining,
)
from .permissions import (
    VOLUNTEERS_ASSIGN,
    VOLUNTEERS_CONFIGURE,
    VOLUNTEERS_CREATE,
    VOLUNTEERS_EXPORT,
    VOLUNTEERS_MANAGE,
    VOLUNTEERS_MANAGE_ACTIVITY,
    VOLUNTEERS_MANAGE_ATTENDANCE,
    VOLUNTEERS_MANAGE_COMMUNICATIONS,
    VOLUNTEERS_MANAGE_DISCIPLINARY,
    VOLUNTEERS_MANAGE_DOCUMENTS,
    VOLUNTEERS_MANAGE_EXIT,
    VOLUNTEERS_MANAGE_LEAVE,
    VOLUNTEERS_MANAGE_PERFORMANCE,
    VOLUNTEERS_MANAGE_TRAINING,
    VOLUNTEERS_UPDATE,
    VOLUNTEERS_VIEW,
    VOLUNTEERS_VIEW_CONFIDENTIAL,
    user_can_view_confidential,
)
from .selectors import can_view_confidential_volunteer_data, visible_volunteer_profiles
from .services import (
    VolunteerActivityService,
    VolunteerApplicationWorkflowService,
    VolunteerAssignmentService,
    VolunteerAttendanceService,
    VolunteerCommunicationService,
    VolunteerDisciplinaryService,
    VolunteerDocumentService,
    VolunteerExitService,
    VolunteerLeaveService,
    VolunteerPerformanceService,
    VolunteerProfileService,
    VolunteerRecognitionService,
    VolunteerRecruitmentService,
    VolunteerTrainingService,
    record_volunteer_audit,
)
from .utils import generate_qr_code_base64


class ManageOverridePermissionMixin(PermissionRequiredMixin):
    """Accept the operation-specific permission or the module manage permission."""

    any_permission = True

    def get_permission_codes(self) -> tuple[str, ...]:
        required = self.permission_required
        if isinstance(required, str):
            return (required, VOLUNTEERS_MANAGE)
        return (*required, VOLUNTEERS_MANAGE)

    def test_func(self) -> bool:
        self.permission_required = self.get_permission_codes()
        return super().test_func()


class ScopedVolunteerMixin:
    request: HttpRequest

    def get_queryset(self):
        return visible_volunteer_profiles(self.request.user)


def _limit_profile_fields(form, user) -> None:
    if "profile" in form.fields:
        form.fields["profile"].queryset = visible_volunteer_profiles(user)
    if "supervisor" in form.fields:
        form.fields["supervisor"].queryset = visible_volunteer_profiles(user)


def _form_error_message(exc: ValidationError) -> str:
    if hasattr(exc, "message_dict"):
        return " ".join(
            str(message)
            for field_messages in exc.message_dict.values()
            for message in field_messages
        )
    return " ".join(str(message) for message in exc.messages)


class VolunteerDashboardView(ManageOverridePermissionMixin, TemplateView):
    template_name = "volunteers/dashboard.html"
    permission_required = VOLUNTEERS_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profiles = visible_volunteer_profiles(self.request.user)
        metrics = profiles.aggregate(
            total=Count("id"),
            active=Count(
                "id",
                filter=Q(status__in=[VolunteerStatus.ACTIVE, VolunteerStatus.ASSIGNED]),
            ),
            assigned=Count("id", filter=Q(status=VolunteerStatus.ASSIGNED)),
            on_leave=Count("id", filter=Q(status=VolunteerStatus.ON_LEAVE)),
        )
        attendance = VolunteerAttendance.objects.filter(profile__in=profiles)
        context.update(
            {
                "total_volunteers": metrics["total"],
                "active_volunteers": metrics["active"],
                "assigned_volunteers": metrics["assigned"],
                "on_leave": metrics["on_leave"],
                "pending_apps": (
                    VolunteerApplication.objects.filter(
                        status=ApplicationStatus.SUBMITTED
                    ).count()
                    if self.request.user.is_superuser
                    or user_has_permission(
                        self.request.user,
                        VOLUNTEERS_MANAGE,
                    )
                    else 0
                ),
                "total_hours": attendance.filter(
                    status=AttendanceStatus.PRESENT
                ).aggregate(total=Sum("hours_served"))["total"]
                or 0,
                "category_counts": profiles.values("category__name", "category__code")
                .annotate(count=Count("id"))
                .order_by("-count"),
                "region_counts": profiles.values("region")
                .annotate(count=Count("id"))
                .order_by("-count"),
                "recent_volunteers": profiles.order_by("-created_at")[:5],
                "recent_assignments": VolunteerAssignment.objects.filter(
                    profile__in=profiles, is_active=True
                )
                .select_related("profile__user")
                .order_by("-created_at")[:5],
            }
        )
        return context


class VolunteerDirectoryView(ManageOverridePermissionMixin, ListView):
    model = VolunteerProfile
    template_name = "volunteers/directory.html"
    context_object_name = "volunteers"
    paginate_by = 25
    permission_required = VOLUNTEERS_VIEW

    def get_queryset(self):
        queryset = visible_volunteer_profiles(self.request.user)
        search_query = self.request.GET.get("q", "").strip()
        status_filter = self.request.GET.get("status", "").strip()
        category_filter = self.request.GET.get("category", "").strip()
        region_filter = self.request.GET.get("region", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query)
                | Q(user__last_name__icontains=search_query)
                | Q(reference_number__icontains=search_query)
                | Q(membership_number__icontains=search_query)
            )
            if can_view_confidential_volunteer_data(self.request.user):
                queryset = queryset | visible_volunteer_profiles(
                    self.request.user
                ).filter(
                    Q(email__icontains=search_query)
                    | Q(phone_number__icontains=search_query)
                )
        if status_filter in VolunteerStatus.values:
            queryset = queryset.filter(status=status_filter)
        if category_filter:
            queryset = queryset.filter(category__code=category_filter)
        if region_filter:
            queryset = queryset.filter(
                Q(region__icontains=region_filter)
                | Q(province_location__name__icontains=region_filter)
            )
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = VolunteerStatus.choices
        context["category_choices"] = list(
            VolunteerCategory.objects.filter(is_active=True).values_list("code", "name")
        )
        context["categories"] = VolunteerCategory.objects.filter(is_active=True)
        context["can_view_confidential"] = can_view_confidential_volunteer_data(
            self.request.user
        )
        return context


class VolunteerDetailView(
    ScopedVolunteerMixin,
    ManageOverridePermissionMixin,
    DetailView,
):
    model = VolunteerProfile
    template_name = "volunteers/profile_detail.html"
    context_object_name = "profile"
    permission_required = VOLUNTEERS_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.object
        context.update(
            {
                "assignments": profile.assignments.filter(
                    is_deleted=False
                ).select_related("team", "supervisor__user"),
                "attendance_logs": profile.attendance_records.order_by("-date")[:10],
                "trainings": profile.trainings.all(),
                "reviews": profile.performance_reviews.all(),
                "recognitions": profile.recognitions.all(),
                "leaves": profile.leaves.all(),
                "qr_code": generate_qr_code_base64(
                    f"VOLUNTEER:{profile.reference_number}"
                ),
                "can_view_confidential": can_view_confidential_volunteer_data(
                    self.request.user
                ),
                "id_card_issued": (
                    hasattr(profile, "onboarding") and profile.onboarding.id_card_issued
                ),
            }
        )
        return context


class VolunteerCreateView(ManageOverridePermissionMixin, CreateView):
    model = VolunteerProfile
    form_class = VolunteerRegistrationForm
    template_name = "volunteers/profile_form.html"
    permission_required = VOLUNTEERS_CREATE

    def form_valid(self, form):
        cleaned_data = form.cleaned_data.copy()
        user_account = cleaned_data.pop("user_account")
        try:
            profile = VolunteerProfileService(user=self.request.user).create_profile(
                user_account=user_account,
                **cleaned_data,
            )
        except ValidationError as exc:
            form.add_error(None, _form_error_message(exc))
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Volunteer profile {profile.reference_number} created successfully.",
        )
        return redirect("volunteers:detail", pk=profile.pk)


class VolunteerUpdateView(
    ScopedVolunteerMixin,
    ManageOverridePermissionMixin,
    UpdateView,
):
    model = VolunteerProfile
    form_class = VolunteerProfileForm
    template_name = "volunteers/profile_form.html"
    permission_required = VOLUNTEERS_UPDATE

    def form_valid(self, form):
        try:
            profile = VolunteerProfileService(user=self.request.user).update_profile(
                self.object,
                **form.cleaned_data,
            )
        except ValidationError as exc:
            form.add_error(None, _form_error_message(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Volunteer profile updated successfully.")
        return redirect("volunteers:detail", pk=profile.pk)


class VolunteerRecruitmentListView(ManageOverridePermissionMixin, ListView):
    model = VolunteerRecruitment
    template_name = "volunteers/recruitment_list.html"
    context_object_name = "campaigns"
    paginate_by = 25
    permission_required = VOLUNTEERS_VIEW

    def get_queryset(self):
        return VolunteerRecruitment.objects.select_related("supervisor__user")


class VolunteerRecruitmentCreateView(ManageOverridePermissionMixin, CreateView):
    form_class = VolunteerRecruitmentForm
    template_name = "volunteers/workflow_form.html"
    permission_required = VOLUNTEERS_CREATE

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        _limit_profile_fields(form, self.request.user)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create recruitment campaign"
        return context

    def form_valid(self, form):
        data = form.cleaned_data.copy()
        title = data.pop("title")
        deadline = data.pop("application_deadline")
        try:
            VolunteerRecruitmentService(user=self.request.user).create_campaign(
                title=title,
                deadline=deadline,
                **data,
            )
        except ValidationError as exc:
            form.add_error(None, _form_error_message(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Recruitment campaign created.")
        return redirect("volunteers:recruitment_list")


class VolunteerApplicationCreateView(CreateView):
    model = VolunteerApplication
    form_class = VolunteerApplicationForm
    template_name = "volunteers/application_form.html"

    def form_valid(self, form):
        data = form.cleaned_data.copy()
        applicant_name = data.pop("applicant_name")
        email = data.pop("email")
        phone = data.pop("phone_number")
        actor = self.request.user if self.request.user.is_authenticated else None
        try:
            application = VolunteerRecruitmentService(user=actor).submit_application(
                applicant_name=applicant_name,
                email=email,
                phone=phone,
                **data,
            )
        except ValidationError as exc:
            form.add_error(None, _form_error_message(exc))
            return self.form_invalid(form)
        self.request.session["volunteer_application_receipt"] = (
            application.reference_number
        )
        return redirect("volunteers:application_success")


class VolunteerApplicationSuccessView(TemplateView):
    template_name = "volunteers/application_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reference_number"] = self.request.session.pop(
            "volunteer_application_receipt", None
        )
        return context


class VolunteerApplicationDetailView(ManageOverridePermissionMixin, DetailView):
    model = VolunteerApplication
    template_name = "volunteers/application_detail.html"
    context_object_name = "application"
    permission_required = VOLUNTEERS_VIEW


class VolunteerApplicationReviewView(ManageOverridePermissionMixin, View):
    permission_required = VOLUNTEERS_UPDATE

    def post(self, request, pk):
        application = get_object_or_404(VolunteerApplication, pk=pk)
        action = request.POST.get("action", "")
        status_by_action = {
            "start-screening": ApplicationStatus.UNDER_SCREENING,
            "return": ApplicationStatus.RETURNED,
            "approve": ApplicationStatus.APPROVED,
            "reject": ApplicationStatus.REJECTED,
            "withdraw": ApplicationStatus.WITHDRAWN,
        }
        if action not in status_by_action:
            return HttpResponseBadRequest("Invalid application action.")
        try:
            VolunteerApplicationWorkflowService(user=request.user).review_application(
                application,
                status_by_action[action],
                notes=request.POST.get("notes", ""),
            )
        except ValidationError as exc:
            messages.error(request, _form_error_message(exc))
        else:
            messages.success(request, "Application status updated.")
        return redirect("volunteers:application_detail", pk=pk)


class VolunteerScreeningView(ManageOverridePermissionMixin, CreateView):
    form_class = VolunteerScreeningForm
    template_name = "volunteers/workflow_form.html"
    permission_required = VOLUNTEERS_UPDATE

    def dispatch(self, request, *args, **kwargs):
        self.application = get_object_or_404(
            VolunteerApplication, pk=kwargs["application_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Screen {self.application.reference_number}"
        return context

    def form_valid(self, form):
        try:
            VolunteerApplicationWorkflowService(
                user=self.request.user
            ).complete_screening(self.application, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, _form_error_message(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Screening completed.")
        return redirect("volunteers:application_detail", pk=self.application.pk)


class VolunteerInterviewView(ManageOverridePermissionMixin, CreateView):
    form_class = VolunteerInterviewForm
    template_name = "volunteers/workflow_form.html"
    permission_required = VOLUNTEERS_UPDATE

    def dispatch(self, request, *args, **kwargs):
        self.application = get_object_or_404(
            VolunteerApplication, pk=kwargs["application_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Interview {self.application.reference_number}"
        return context

    def form_valid(self, form):
        try:
            VolunteerApplicationWorkflowService(
                user=self.request.user
            ).complete_interview(self.application, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, _form_error_message(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Interview recorded.")
        return redirect("volunteers:application_detail", pk=self.application.pk)


class VolunteerOnboardingView(
    ScopedVolunteerMixin,
    ManageOverridePermissionMixin,
    CreateView,
):
    form_class = VolunteerOnboardingForm
    template_name = "volunteers/workflow_form.html"
    permission_required = VOLUNTEERS_UPDATE

    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(
            visible_volunteer_profiles(request.user), pk=kwargs["profile_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Complete onboarding for {self.profile.reference_number}"
        return context

    def form_valid(self, form):
        try:
            VolunteerApplicationWorkflowService(
                user=self.request.user
            ).complete_onboarding(self.profile, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, _form_error_message(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Volunteer onboarding completed.")
        return redirect("volunteers:detail", pk=self.profile.pk)


class ScopedRelatedListMixin:
    request: HttpRequest
    model: Any
    paginate_by: int | None = 25
    profile_relation = "profile"

    def get_queryset(self):
        lookup = {
            f"{self.profile_relation}__in": visible_volunteer_profiles(
                self.request.user
            )
        }
        return self.model.objects.filter(**lookup).select_related("profile__user")


class ServiceCreateView(ManageOverridePermissionMixin, CreateView):
    success_message = "Record created successfully."

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        _limit_profile_fields(form, self.request.user)
        return form

    def perform_service(self, cleaned_data):
        raise NotImplementedError

    def form_valid(self, form):
        try:
            self.perform_service(form.cleaned_data.copy())
        except ValidationError as exc:
            form.add_error(None, _form_error_message(exc))
            return self.form_invalid(form)
        messages.success(self.request, self.success_message)
        return redirect(str(self.success_url))


class VolunteerAssignmentListView(
    ScopedRelatedListMixin, ManageOverridePermissionMixin, ListView
):
    model = VolunteerAssignment
    template_name = "volunteers/assignment_list.html"
    context_object_name = "assignments"
    permission_required = VOLUNTEERS_VIEW


class VolunteerAssignmentCreateView(ServiceCreateView):
    form_class = VolunteerAssignmentForm
    template_name = "volunteers/assignment_form.html"
    permission_required = VOLUNTEERS_ASSIGN
    success_url = reverse_lazy("volunteers:assignment_list")
    success_message = "Volunteer deployed successfully."

    def perform_service(self, cleaned_data):
        VolunteerAssignmentService(user=self.request.user).create_assignment(
            **cleaned_data
        )


class VolunteerAttendanceListView(
    ScopedRelatedListMixin, ManageOverridePermissionMixin, ListView
):
    model = VolunteerAttendance
    template_name = "volunteers/attendance_list.html"
    context_object_name = "attendance_logs"
    paginate_by = 30
    permission_required = VOLUNTEERS_VIEW


class VolunteerAttendanceCreateView(ServiceCreateView):
    form_class = VolunteerAttendanceForm
    template_name = "volunteers/attendance_form.html"
    permission_required = VOLUNTEERS_MANAGE_ATTENDANCE
    success_url = reverse_lazy("volunteers:attendance_list")

    def perform_service(self, cleaned_data):
        cleaned_data["hours"] = cleaned_data.pop("hours_served")
        VolunteerAttendanceService(user=self.request.user).log_attendance(
            **cleaned_data
        )


class VolunteerTrainingListView(
    ScopedRelatedListMixin, ManageOverridePermissionMixin, ListView
):
    model = VolunteerTraining
    template_name = "volunteers/training_list.html"
    context_object_name = "trainings"
    permission_required = VOLUNTEERS_VIEW


class VolunteerTrainingCreateView(ServiceCreateView):
    form_class = VolunteerTrainingForm
    template_name = "volunteers/training_form.html"
    permission_required = VOLUNTEERS_MANAGE_TRAINING
    success_url = reverse_lazy("volunteers:training_list")

    def perform_service(self, cleaned_data):
        VolunteerTrainingService(user=self.request.user).record_training(**cleaned_data)


class VolunteerPerformanceListView(
    ScopedRelatedListMixin, ManageOverridePermissionMixin, ListView
):
    model = VolunteerPerformance
    template_name = "volunteers/performance_list.html"
    context_object_name = "reviews"
    permission_required = VOLUNTEERS_VIEW


class VolunteerPerformanceCreateView(ServiceCreateView):
    form_class = VolunteerPerformanceForm
    template_name = "volunteers/performance_form.html"
    permission_required = VOLUNTEERS_MANAGE_PERFORMANCE
    success_url = reverse_lazy("volunteers:performance_list")

    def perform_service(self, cleaned_data):
        cleaned_data["score"] = cleaned_data.pop("overall_score")
        VolunteerPerformanceService(user=self.request.user).record_review(
            **cleaned_data
        )


class VolunteerRecognitionListView(
    ScopedRelatedListMixin, ManageOverridePermissionMixin, ListView
):
    model = VolunteerRecognition
    template_name = "volunteers/recognition_list.html"
    context_object_name = "recognitions"
    permission_required = VOLUNTEERS_VIEW


class VolunteerRecognitionCreateView(ServiceCreateView):
    form_class = VolunteerRecognitionForm
    template_name = "volunteers/recognition_form.html"
    permission_required = VOLUNTEERS_CREATE
    success_url = reverse_lazy("volunteers:recognition_list")

    def perform_service(self, cleaned_data):
        VolunteerRecognitionService(user=self.request.user).award_recognition(
            **cleaned_data
        )


class VolunteerLeaveListView(
    ScopedRelatedListMixin, ManageOverridePermissionMixin, ListView
):
    model = VolunteerLeave
    template_name = "volunteers/leave_list.html"
    context_object_name = "leaves"
    permission_required = VOLUNTEERS_VIEW


class VolunteerLeaveCreateView(ServiceCreateView):
    form_class = VolunteerLeaveForm
    template_name = "volunteers/leave_form.html"
    permission_required = VOLUNTEERS_VIEW
    success_url = reverse_lazy("volunteers:leave_list")

    def perform_service(self, cleaned_data):
        VolunteerLeaveService(user=self.request.user).apply_leave(**cleaned_data)


class VolunteerLeaveApproveView(ManageOverridePermissionMixin, View):
    permission_required = VOLUNTEERS_MANAGE_LEAVE

    def post(self, request, pk):
        leave = get_object_or_404(
            VolunteerLeave.objects.filter(
                profile__in=visible_volunteer_profiles(request.user)
            ),
            pk=pk,
        )
        action = request.POST.get("action")
        if action not in {"approve", "reject"}:
            return HttpResponseBadRequest("Invalid leave action.")
        try:
            VolunteerLeaveService(user=request.user).approve_leave(
                leave,
                approve=action == "approve",
                notes=request.POST.get("notes", ""),
            )
        except ValidationError as exc:
            messages.error(request, _form_error_message(exc))
        else:
            messages.success(request, "Leave request updated.")
        return redirect("volunteers:leave_list")


class VolunteerExitListView(
    ScopedRelatedListMixin, ManageOverridePermissionMixin, ListView
):
    model = VolunteerExit
    template_name = "volunteers/exit_list.html"
    context_object_name = "exits"
    permission_required = VOLUNTEERS_VIEW


class VolunteerExitCreateView(ServiceCreateView):
    form_class = VolunteerExitForm
    template_name = "volunteers/exit_form.html"
    permission_required = VOLUNTEERS_MANAGE_EXIT
    success_url = reverse_lazy("volunteers:exit_list")

    def perform_service(self, cleaned_data):
        VolunteerExitService(user=self.request.user).initiate_exit(**cleaned_data)


class VolunteerIdCardView(
    ScopedVolunteerMixin,
    ManageOverridePermissionMixin,
    DetailView,
):
    model = VolunteerProfile
    template_name = "volunteers/id_card.html"
    context_object_name = "profile"
    permission_required = VOLUNTEERS_VIEW

    def get_object(self, queryset=None):
        profile = super().get_object(queryset)
        if not hasattr(profile, "onboarding") or not profile.onboarding.id_card_issued:
            raise Http404("Volunteer ID card has not been issued.")
        return profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["qr_code"] = generate_qr_code_base64(
            f"VOLUNTEER:{self.object.reference_number}"
        )
        return context


class VolunteerApplicationCVDownloadView(ManageOverridePermissionMixin, View):
    permission_required = (VOLUNTEERS_VIEW_CONFIDENTIAL, VOLUNTEERS_MANAGE)

    def get(self, request, pk):
        if not user_can_view_confidential(request.user):
            raise PermissionDenied
        application = get_object_or_404(VolunteerApplication, pk=pk)
        if not application.cv_file:
            raise Http404("No CV is attached.")
        record_volunteer_audit(
            "VolunteerApplication",
            application.pk,
            VolunteerAuditAction.DOCUMENT_DOWNLOADED,
            request.user,
            notes="Application CV downloaded.",
        )
        response = FileResponse(
            application.cv_file.open("rb"),
            as_attachment=True,
            filename=Path(application.cv_file.name).name,
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response


class VolunteerReportView(ManageOverridePermissionMixin, TemplateView):
    template_name = "volunteers/reports.html"
    permission_required = VOLUNTEERS_EXPORT

    def get(self, request, *args, **kwargs):
        export_format = request.GET.get("export")
        if export_format not in {"csv", "xlsx", "docx", "pdf"}:
            return super().get(request, *args, **kwargs)
        profiles = visible_volunteer_profiles(request.user).order_by("reference_number")
        include_confidential = can_view_confidential_volunteer_data(request.user)
        if export_format == "csv":
            response = export_volunteer_csv(profiles, include_confidential)
        elif export_format == "xlsx":
            response = export_volunteer_xlsx(profiles, include_confidential)
        elif export_format == "docx":
            response = export_volunteer_docx(profiles, include_confidential)
        else:
            response = export_volunteer_pdf(profiles, include_confidential)
        row_count = len(list(profiles))
        record_volunteer_audit(
            "VolunteerRegister",
            export_format,
            VolunteerAuditAction.EXPORTED,
            request.user,
            to_data={
                "row_count": row_count,
                "included_confidential": include_confidential,
                "format": export_format,
            },
            notes=f"Volunteer register exported as {export_format.upper()}.",
        )
        return response


class VolunteerActivityLogListView(
    ScopedRelatedListMixin, ManageOverridePermissionMixin, ListView
):
    model = VolunteerActivityLog
    template_name = "volunteers/activity_log_list.html"
    context_object_name = "activity_logs"
    paginate_by = 30
    permission_required = VOLUNTEERS_VIEW


class VolunteerActivityLogCreateView(ServiceCreateView):
    form_class = VolunteerActivityLogForm
    template_name = "volunteers/activity_log_form.html"
    permission_required = VOLUNTEERS_MANAGE_ACTIVITY
    success_url = reverse_lazy("volunteers:activity_log_list")
    success_message = "Volunteer activity logged successfully."

    def perform_service(self, cleaned_data):
        VolunteerActivityService(user=self.request.user).log_activity(**cleaned_data)


class VolunteerDisciplinaryListView(
    ScopedRelatedListMixin, ManageOverridePermissionMixin, ListView
):
    model = VolunteerDisciplinaryRecord
    template_name = "volunteers/disciplinary_list.html"
    context_object_name = "disciplinary_records"
    paginate_by = 30
    permission_required = VOLUNTEERS_VIEW


class VolunteerDisciplinaryCreateView(ServiceCreateView):
    form_class = VolunteerDisciplinaryRecordForm
    template_name = "volunteers/disciplinary_form.html"
    permission_required = VOLUNTEERS_MANAGE_DISCIPLINARY
    success_url = reverse_lazy("volunteers:disciplinary_list")
    success_message = "Disciplinary record opened successfully."

    def perform_service(self, cleaned_data):
        VolunteerDisciplinaryService(user=self.request.user).open_disciplinary(
            **cleaned_data
        )


class VolunteerDisciplinaryDetailView(ManageOverridePermissionMixin, DetailView):
    model = VolunteerDisciplinaryRecord
    template_name = "volunteers/disciplinary_detail.html"
    context_object_name = "disciplinary_record"
    permission_required = VOLUNTEERS_VIEW

    def get_queryset(self):
        return VolunteerDisciplinaryRecord.objects.filter(
            profile__in=visible_volunteer_profiles(self.request.user)
        ).select_related("profile__user", "decided_by")


class VolunteerDisciplinaryDecisionView(ManageOverridePermissionMixin, UpdateView):
    model = VolunteerDisciplinaryRecord
    form_class = VolunteerDisciplinaryDecisionForm
    template_name = "volunteers/disciplinary_decision_form.html"
    permission_required = VOLUNTEERS_MANAGE_DISCIPLINARY
    context_object_name = "disciplinary_record"

    def get_queryset(self):
        return VolunteerDisciplinaryRecord.objects.filter(
            profile__in=visible_volunteer_profiles(self.request.user)
        )

    def form_valid(self, form):
        try:
            VolunteerDisciplinaryService(user=self.request.user).decide_disciplinary(
                self.object, **form.cleaned_data
            )
        except ValidationError as exc:
            form.add_error(None, _form_error_message(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Disciplinary decision recorded.")
        return redirect("volunteers:disciplinary_detail", pk=self.object.pk)

    def get_success_url(self):
        return reverse_lazy(
            "volunteers:disciplinary_detail", kwargs={"pk": self.object.pk}
        )


class VolunteerCommunicationListView(
    ScopedRelatedListMixin, ManageOverridePermissionMixin, ListView
):
    model = VolunteerCommunication
    template_name = "volunteers/communication_list.html"
    context_object_name = "communications"
    paginate_by = 30
    permission_required = VOLUNTEERS_VIEW


class VolunteerCommunicationCreateView(ServiceCreateView):
    form_class = VolunteerCommunicationForm
    template_name = "volunteers/communication_form.html"
    permission_required = VOLUNTEERS_MANAGE_COMMUNICATIONS
    success_url = reverse_lazy("volunteers:communication_list")
    success_message = "Communication recorded successfully."

    def perform_service(self, cleaned_data):
        VolunteerCommunicationService(user=self.request.user).record_communication(
            **cleaned_data
        )


class VolunteerDocumentListView(
    ScopedRelatedListMixin, ManageOverridePermissionMixin, ListView
):
    model = VolunteerDocument
    template_name = "volunteers/document_list.html"
    context_object_name = "documents"
    paginate_by = 30
    permission_required = VOLUNTEERS_VIEW
    profile_relation = "profile"


class VolunteerDocumentUploadView(ServiceCreateView):
    form_class = VolunteerDocumentUploadForm
    template_name = "volunteers/document_form.html"
    permission_required = VOLUNTEERS_MANAGE_DOCUMENTS
    success_url = reverse_lazy("volunteers:document_list")
    success_message = "Document uploaded successfully."

    def perform_service(self, cleaned_data):
        VolunteerDocumentService(user=self.request.user).upload_document(**cleaned_data)


class VolunteerDocumentReviewView(ManageOverridePermissionMixin, UpdateView):
    model = VolunteerDocument
    form_class = VolunteerDocumentReviewForm
    template_name = "volunteers/document_review_form.html"
    permission_required = VOLUNTEERS_MANAGE_DOCUMENTS
    context_object_name = "document"

    def get_queryset(self):
        return VolunteerDocument.objects.filter(
            profile__in=visible_volunteer_profiles(self.request.user)
        )

    def form_valid(self, form):
        action = self.request.POST.get("action", "approve")
        try:
            service = VolunteerDocumentService(user=self.request.user)
            if action == "reject":
                service.reject_document(self.object, notes=form.cleaned_data["notes"])
            else:
                service.approve_document(self.object, notes=form.cleaned_data["notes"])
        except ValidationError as exc:
            form.add_error(None, _form_error_message(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Document review recorded.")
        return redirect("volunteers:document_list")


class VolunteerDocumentArchiveView(ManageOverridePermissionMixin, View):
    permission_required = VOLUNTEERS_MANAGE_DOCUMENTS

    def post(self, request, pk):
        document = get_object_or_404(
            VolunteerDocument.objects.filter(
                profile__in=visible_volunteer_profiles(request.user)
            ),
            pk=pk,
        )
        try:
            VolunteerDocumentService(user=request.user).archive_document(document)
        except ValidationError as exc:
            messages.error(request, _form_error_message(exc))
        else:
            messages.success(request, "Document archived.")
        return redirect("volunteers:document_list")


class VolunteerDocumentDownloadView(ManageOverridePermissionMixin, View):
    permission_required = (VOLUNTEERS_VIEW_CONFIDENTIAL, VOLUNTEERS_MANAGE)

    def get(self, request, pk):
        document = get_object_or_404(
            VolunteerDocument.objects.filter(
                profile__in=visible_volunteer_profiles(request.user)
            ),
            pk=pk,
        )
        if document.is_confidential and not user_can_view_confidential(request.user):
            raise PermissionDenied
        record_volunteer_audit(
            "VolunteerDocument",
            document.pk,
            VolunteerAuditAction.DOCUMENT_DOWNLOADED,
            request.user,
            notes=f"Volunteer document '{document.title}' downloaded.",
        )
        response = FileResponse(
            document.file.open("rb"),
            as_attachment=True,
            filename=Path(document.file.name).name,
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response


class VolunteerCategoryListView(ManageOverridePermissionMixin, ListView):
    model = VolunteerCategory
    template_name = "volunteers/category_list.html"
    context_object_name = "categories"
    permission_required = VOLUNTEERS_CONFIGURE


class VolunteerCategoryCreateView(ServiceCreateView):
    form_class = VolunteerCategoryForm
    template_name = "volunteers/category_form.html"
    permission_required = VOLUNTEERS_CONFIGURE
    success_url = reverse_lazy("volunteers:category_list")
    success_message = "Volunteer category created successfully."

    def perform_service(self, cleaned_data):
        VolunteerCategory.objects.create(**cleaned_data)


class VolunteerCategoryUpdateView(ManageOverridePermissionMixin, UpdateView):
    model = VolunteerCategory
    form_class = VolunteerCategoryForm
    template_name = "volunteers/category_form.html"
    permission_required = VOLUNTEERS_CONFIGURE
    context_object_name = "category"
    success_url = reverse_lazy("volunteers:category_list")
