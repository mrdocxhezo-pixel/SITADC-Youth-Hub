"""Views for the Leadership Management module."""

from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.rbac.mixins import PermissionRequiredMixin

from .forms import (
    CoachingRecordForm,
    LeadershipAppointmentForm,
    LeadershipAttendanceForm,
    LeadershipProfileForm,
    MentorshipRecordForm,
    PerformanceReviewForm,
    SuccessionPlanForm,
)
from .models import (
    CoachingRecord,
    LeadershipAppointment,
    LeadershipAttendance,
    LeadershipProfile,
    MentorshipRecord,
    PerformanceReview,
    SuccessionPlan,
)
from .permissions import LEADERSHIP_CREATE, LEADERSHIP_UPDATE, LEADERSHIP_VIEW


class DashboardView(
    PermissionRequiredMixin,
    TemplateView,
):
    """Leadership module dashboard with summary statistics."""

    template_name = "leadership/dashboard.html"
    permission_required = LEADERSHIP_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_leaders"] = LeadershipProfile.objects.filter(
            status="ACTIVE",
        ).count()
        context["pending_appointments"] = LeadershipAppointment.objects.filter(
            status="PENDING_APPROVAL",
        ).count()
        context["recent_appointments"] = LeadershipAppointment.objects.select_related(
            "profile__user",
            "position",
        ).order_by("-created_at")[:5]
        return context


class DirectoryView(
    PermissionRequiredMixin,
    ListView,
):
    """Public-facing leadership directory."""

    model = LeadershipProfile
    template_name = "leadership/directory.html"
    context_object_name = "profiles"
    paginate_by = 12
    permission_required = LEADERSHIP_VIEW

    def get_queryset(self):
        return (
            LeadershipProfile.objects.filter(
                status="ACTIVE",
            )
            .select_related(
                "user",
                "organizational_unit",
                "position",
            )
            .order_by("user__last_name", "user__first_name")
        )


class ProfileDetailView(
    PermissionRequiredMixin,
    DetailView,
):
    """Detailed leadership profile page."""

    model = LeadershipProfile
    template_name = "leadership/profile_detail.html"
    context_object_name = "profile"
    permission_required = LEADERSHIP_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["appointments"] = self.object.appointments.select_related(
            "position",
        ).all()
        context["attendance"] = self.object.attendance_records.order_by(
            "-attendance_date",
        )[:10]
        return context


class ProfileCreateView(
    PermissionRequiredMixin,
    CreateView,
):
    """Create a new leadership profile."""

    model = LeadershipProfile
    form_class = LeadershipProfileForm
    template_name = "leadership/profile_form.html"
    permission_required = LEADERSHIP_CREATE

    def get_success_url(self):
        return reverse_lazy(
            "leadership:profile_detail",
            kwargs={"pk": self.object.pk},
        )


class ProfileUpdateView(
    PermissionRequiredMixin,
    UpdateView,
):
    """Edit an existing leadership profile."""

    model = LeadershipProfile
    form_class = LeadershipProfileForm
    template_name = "leadership/profile_form.html"
    permission_required = LEADERSHIP_UPDATE

    def get_success_url(self):
        return reverse_lazy(
            "leadership:profile_detail",
            kwargs={"pk": self.object.pk},
        )


class AppointmentListView(
    PermissionRequiredMixin,
    ListView,
):
    """List all leadership appointments."""

    model = LeadershipAppointment
    template_name = "leadership/appointment_list.html"
    context_object_name = "appointments"
    paginate_by = 20
    permission_required = LEADERSHIP_VIEW

    def get_queryset(self):
        return LeadershipAppointment.objects.select_related(
            "profile__user",
            "position",
            "organizational_unit",
        ).order_by("-created_at")


class AppointmentDetailView(
    PermissionRequiredMixin,
    DetailView,
):
    """View appointment details."""

    model = LeadershipAppointment
    template_name = "leadership/appointment_detail.html"
    context_object_name = "appointment"
    permission_required = LEADERSHIP_VIEW


class AppointmentCreateView(
    PermissionRequiredMixin,
    CreateView,
):
    """Create a new appointment."""

    model = LeadershipAppointment
    form_class = LeadershipAppointmentForm
    template_name = "leadership/appointment_form.html"
    permission_required = LEADERSHIP_CREATE
    success_url = reverse_lazy(
        "leadership:appointment_list",
    )


class AppointmentUpdateView(
    PermissionRequiredMixin,
    UpdateView,
):
    """Edit an existing appointment."""

    model = LeadershipAppointment
    form_class = LeadershipAppointmentForm
    template_name = "leadership/appointment_form.html"
    permission_required = LEADERSHIP_UPDATE
    success_url = reverse_lazy(
        "leadership:appointment_list",
    )


class ReviewListView(
    PermissionRequiredMixin,
    ListView,
):
    """List performance reviews."""

    model = PerformanceReview
    template_name = "leadership/review_list.html"
    context_object_name = "reviews"
    paginate_by = 20
    permission_required = LEADERSHIP_VIEW

    def get_queryset(self):
        return PerformanceReview.objects.select_related(
            "profile__user",
            "reviewer",
        ).order_by("-created_at")


class ReviewDetailView(
    PermissionRequiredMixin,
    DetailView,
):
    """View performance review details."""

    model = PerformanceReview
    template_name = "leadership/review_detail.html"
    context_object_name = "review"
    permission_required = LEADERSHIP_VIEW


class ReviewCreateView(
    PermissionRequiredMixin,
    CreateView,
):
    """Create a new performance review."""

    model = PerformanceReview
    form_class = PerformanceReviewForm
    template_name = "leadership/review_form.html"
    permission_required = LEADERSHIP_CREATE
    success_url = reverse_lazy("leadership:review_list")


class AttendanceListView(
    PermissionRequiredMixin,
    ListView,
):
    """List attendance records."""

    model = LeadershipAttendance
    template_name = "leadership/attendance_list.html"
    context_object_name = "attendance_records"
    paginate_by = 20
    permission_required = LEADERSHIP_VIEW

    def get_queryset(self):
        return LeadershipAttendance.objects.select_related(
            "profile__user",
        ).order_by("-attendance_date")


class AttendanceCreateView(
    PermissionRequiredMixin,
    CreateView,
):
    """Mark attendance for a leader."""

    model = LeadershipAttendance
    form_class = LeadershipAttendanceForm
    template_name = "leadership/attendance_form.html"
    permission_required = LEADERSHIP_CREATE
    success_url = reverse_lazy(
        "leadership:attendance_list",
    )


class CoachingListView(
    PermissionRequiredMixin,
    ListView,
):
    """List coaching records."""

    model = CoachingRecord
    template_name = "leadership/coaching_list.html"
    context_object_name = "coaching_records"
    paginate_by = 20
    permission_required = LEADERSHIP_VIEW

    def get_queryset(self):
        return CoachingRecord.objects.select_related(
            "leader__user",
            "coach",
        ).order_by("-session_date")


class CoachingCreateView(
    PermissionRequiredMixin,
    CreateView,
):
    """Create a new coaching record."""

    model = CoachingRecord
    form_class = CoachingRecordForm
    template_name = "leadership/coaching_form.html"
    permission_required = LEADERSHIP_CREATE
    success_url = reverse_lazy(
        "leadership:coaching_list",
    )


class MentorshipListView(
    PermissionRequiredMixin,
    ListView,
):
    """List mentorship records."""

    model = MentorshipRecord
    template_name = "leadership/mentorship_list.html"
    context_object_name = "mentorship_records"
    paginate_by = 20
    permission_required = LEADERSHIP_VIEW

    def get_queryset(self):
        return MentorshipRecord.objects.select_related(
            "mentor__user",
            "mentee__user",
        ).order_by("-start_date")


class MentorshipCreateView(
    PermissionRequiredMixin,
    CreateView,
):
    """Create a new mentorship record."""

    model = MentorshipRecord
    form_class = MentorshipRecordForm
    template_name = "leadership/mentorship_form.html"
    permission_required = LEADERSHIP_CREATE
    success_url = reverse_lazy(
        "leadership:mentorship_list",
    )


class SuccessionListView(
    PermissionRequiredMixin,
    ListView,
):
    """List succession plans."""

    model = SuccessionPlan
    template_name = "leadership/succession_list.html"
    context_object_name = "succession_plans"
    paginate_by = 20
    permission_required = LEADERSHIP_VIEW


class SuccessionCreateView(
    PermissionRequiredMixin,
    CreateView,
):
    """Create a new succession plan."""

    model = SuccessionPlan
    form_class = SuccessionPlanForm
    template_name = "leadership/succession_form.html"
    permission_required = LEADERSHIP_CREATE
    success_url = reverse_lazy(
        "leadership:succession_list",
    )
