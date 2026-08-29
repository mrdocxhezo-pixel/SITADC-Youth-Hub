"""Views for the Leadership Management module."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import redirect
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
from .services import CreateLeadershipAppointmentService, CreateLeadershipProfileService


def _form_error_message(exc: ValidationError) -> str:
    """Flatten a ValidationError into a single readable message."""
    if hasattr(exc, "message_dict"):
        return " ".join(
            str(message)
            for field_messages in exc.message_dict.values()
            for message in field_messages
        )
    return " ".join(str(message) for message in exc.messages)


class DashboardView(
    PermissionRequiredMixin,
    TemplateView,
):
    """Leadership module dashboard with summary statistics."""

    template_name = "leadership/dashboard.html"
    permission_required = LEADERSHIP_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Total leaders
        total_leaders = LeadershipProfile.objects.count()
        active_leaders = LeadershipProfile.objects.filter(
            status__in=["ACTIVE", "APPOINTED", "ACTING", "PROBATION"]
        ).count()
        inactive_leaders = LeadershipProfile.objects.filter(
            status__in=["SUSPENDED", "ON_LEAVE", "RESIGNED", "RETIRED", "REMOVED"]
        ).count()
        archived_leaders = LeadershipProfile.objects.filter(status="ARCHIVED").count()

        # By leadership level
        leaders_by_level = (
            LeadershipProfile.objects.values("leadership_level")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # By directorate
        leaders_by_directorate = (
            LeadershipProfile.objects.filter(directorate__isnull=False)
            .values("directorate__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # By region
        leaders_by_region = (
            LeadershipProfile.objects.filter(region__isnull=False)
            .values("region__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # Pending appointments
        pending_appointments = LeadershipAppointment.objects.filter(
            status__in=["PENDING_REVIEW", "PENDING_APPROVAL", "APPROVED"]
        ).count()

        # Directors (DIRECTORATE level)
        directors_count = LeadershipProfile.objects.filter(
            leadership_level="DIRECTORATE", status__in=["ACTIVE", "APPOINTED", "ACTING"]
        ).count()

        # Coordinators (REGIONAL, DISTRICT, COMMUNITY)
        coordinator_levels = [
            "REGIONAL_COORDINATOR",
            "DISTRICT_COORDINATOR",
            "COMMUNITY_COORDINATOR",
        ]
        coordinators_count = LeadershipProfile.objects.filter(
            leadership_level__in=coordinator_levels,
            status__in=["ACTIVE", "APPOINTED", "ACTING"],
        ).count()

        # Team Leaders
        team_leaders_count = LeadershipProfile.objects.filter(
            leadership_level="TEAM_LEADER", status__in=["ACTIVE", "APPOINTED", "ACTING"]
        ).count()

        # Report Authors
        report_authors_count = LeadershipProfile.objects.filter(
            leadership_level="REPORT_AUTHOR",
            status__in=["ACTIVE", "APPOINTED", "ACTING"],
        ).count()

        # Vacant positions (positions without active appointments)
        from apps.organizations.models import Position

        vacant_positions = (
            Position.objects.filter(status="ACTIVE")
            .exclude(assignments__status="ACTIVE")
            .count()
        )

        # Expiring appointments (within 30 days)
        from datetime import timedelta

        from django.utils import timezone

        expiring_soon = LeadershipAppointment.objects.filter(
            status="ACTIVE",
            term_end__isnull=False,
            term_end__lte=timezone.localdate() + timedelta(days=30),
            term_end__gte=timezone.localdate(),
        ).count()

        # Recently added leaders (last 30 days)
        recently_added = LeadershipProfile.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()

        # Recently updated profiles
        recently_updated = (
            LeadershipProfile.objects.filter(
                updated_at__gte=timezone.now() - timedelta(days=30)
            )
            .exclude(created_at__gte=timezone.now() - timedelta(days=30))
            .count()
        )

        # Recent appointments
        recent_appointments = LeadershipAppointment.objects.select_related(
            "profile__user",
            "position",
        ).order_by("-created_at")[:5]

        # View Leaders card statistics
        active_personnel = LeadershipProfile.objects.filter(
            status__in=["ACTIVE", "APPOINTED", "ACTING", "PROBATION"]
        ).count()
        
        # Staff count (those with leadership levels below executive/directorate level)
        staff_levels = ["TEAM_LEADER", "REPORT_AUTHOR", "COMMUNITY_COORDINATOR", "DISTRICT_COORDINATOR", "REGIONAL_COORDINATOR"]
        staff_count = LeadershipProfile.objects.filter(
            leadership_level__in=staff_levels,
            status__in=["ACTIVE", "APPOINTED", "ACTING", "PROBATION"]
        ).count()
        
        # Leaders count (board, executive, directorate levels)
        leader_levels = ["BOARD_OF_TRUSTEES", "NATIONAL_EXECUTIVE_COMMITTEE", "EXECUTIVE_DIRECTOR", "EXECUTIVE_MANAGEMENT", "DIRECTORATE"]
        leaders_count = LeadershipProfile.objects.filter(
            leadership_level__in=leader_levels,
            status__in=["ACTIVE", "APPOINTED", "ACTING", "PROBATION"]
        ).count()

        context.update(
            {
                "total_leaders": total_leaders,
                "active_leaders": active_leaders,
                "inactive_leaders": inactive_leaders,
                "archived_leaders": archived_leaders,
                "leaders_by_level": leaders_by_level,
                "leaders_by_directorate": leaders_by_directorate,
                "leaders_by_region": leaders_by_region,
                "pending_appointments": pending_appointments,
                "directors_count": directors_count,
                "coordinators_count": coordinators_count,
                "team_leaders_count": team_leaders_count,
                "report_authors_count": report_authors_count,
                "vacant_positions": vacant_positions,
                "expiring_appointments": expiring_soon,
                "recently_added": recently_added,
                "recently_updated": recently_updated,
                "recent_appointments": recent_appointments,
                # View Leaders card statistics
                "total_active_personnel": active_personnel,
                "total_leaders_count": leaders_count,
                "total_staff_count": staff_count,
            }
        )
        return context


class DirectoryView(
    PermissionRequiredMixin,
    ListView,
):
    """All Leaders & Staff directory with search, filtering, and pagination."""

    model = LeadershipProfile
    template_name = "leadership/directory.html"
    context_object_name = "profiles"
    paginate_by = 20
    permission_required = LEADERSHIP_VIEW

    # Statuses considered "currently serving" when no explicit status filter
    # is supplied; archived and exited personnel are hidden by default.
    DEFAULT_VISIBLE_STATUSES = (
        "ACTIVE",
        "APPOINTED",
        "ACTING",
        "PROBATION",
    )

    def get_queryset(self):
        queryset = (
            LeadershipProfile.objects.select_related(
                "user",
                "user__profile",
                "organizational_unit",
                "position",
                "directorate",
                "region",
                "district",
                "community",
                "supervisor__user",
            )
            .order_by("user__last_name", "user__first_name")
        )

        # An explicit status filter overrides the default visible statuses so
        # that selecting e.g. "Suspended" actually returns suspended records.
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)
        else:
            queryset = queryset.filter(status__in=self.DEFAULT_VISIBLE_STATUSES)

        # Search
        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query)
                | Q(user__last_name__icontains=search_query)
                | Q(user__email__icontains=search_query)
                | Q(reference_number__icontains=search_query)
                | Q(position__title__icontains=search_query)
                | Q(leadership_level__icontains=search_query)
                | Q(organizational_unit__name__icontains=search_query)
                | Q(directorate__name__icontains=search_query)
                | Q(region__name__icontains=search_query)
                | Q(district__name__icontains=search_query)
                | Q(community__name__icontains=search_query)
            )

        # Filters
        leadership_level = self.request.GET.get("leadership_level")
        if leadership_level:
            queryset = queryset.filter(leadership_level=leadership_level)

        position_id = self.request.GET.get("position")
        if position_id:
            queryset = queryset.filter(position_id=position_id)

        org_unit_id = self.request.GET.get("organizational_unit")
        if org_unit_id:
            queryset = queryset.filter(organizational_unit_id=org_unit_id)

        directorate_id = self.request.GET.get("directorate")
        if directorate_id:
            queryset = queryset.filter(directorate_id=directorate_id)

        region_id = self.request.GET.get("region")
        if region_id:
            queryset = queryset.filter(region_id=region_id)

        district_id = self.request.GET.get("district")
        if district_id:
            queryset = queryset.filter(district_id=district_id)

        community_id = self.request.GET.get("community")
        if community_id:
            queryset = queryset.filter(community_id=community_id)

        appointment_status = self.request.GET.get("appointment_status")
        if appointment_status:
            queryset = queryset.filter(
                appointments__status=appointment_status
            ).distinct()

        date_appointed_from = self.request.GET.get("date_appointed_from")
        if date_appointed_from:
            queryset = queryset.filter(appointment_date__gte=date_appointed_from)

        date_appointed_to = self.request.GET.get("date_appointed_to")
        if date_appointed_to:
            queryset = queryset.filter(appointment_date__lte=date_appointed_to)

        # Sorting
        sort_by = self.request.GET.get("sort", "user__last_name")
        valid_sort_fields = [
            "user__last_name",
            "user__first_name",
            "reference_number",
            "leadership_level",
            "position__title",
            "organizational_unit__name",
            "directorate__name",
            "region__name",
            "district__name",
            "community__name",
            "status",
            "appointment_date",
            "-user__last_name",
            "-user__first_name",
            "-reference_number",
            "-leadership_level",
            "-position__title",
            "-organizational_unit__name",
            "-directorate__name",
            "-region__name",
            "-district__name",
            "-community__name",
            "-status",
            "-appointment_date",
        ]
        if sort_by in valid_sort_fields:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Summary statistics for the directory page
        from django.db.models import Count
        
        base_queryset = LeadershipProfile.objects.all()
        
        total_personnel = base_queryset.count()
        active_leaders = base_queryset.filter(
            status__in=["ACTIVE", "APPOINTED", "ACTING", "PROBATION"]
        ).count()
        
        leader_levels = ["BOARD_OF_TRUSTEES", "NATIONAL_EXECUTIVE_COMMITTEE", "EXECUTIVE_DIRECTOR", "EXECUTIVE_MANAGEMENT", "DIRECTORATE"]
        staff_levels = ["TEAM_LEADER", "REPORT_AUTHOR", "COMMUNITY_COORDINATOR", "DISTRICT_COORDINATOR", "REGIONAL_COORDINATOR"]
        
        leaders_count = base_queryset.filter(
            leadership_level__in=leader_levels,
            status__in=["ACTIVE", "APPOINTED", "ACTING", "PROBATION"]
        ).count()
        
        staff_count = base_queryset.filter(
            leadership_level__in=staff_levels,
            status__in=["ACTIVE", "APPOINTED", "ACTING", "PROBATION"]
        ).count()
        
        directorates_count = base_queryset.filter(directorate__isnull=False).values("directorate").distinct().count()
        departments_count = base_queryset.filter(organizational_unit__isnull=False).values("organizational_unit").distinct().count()

        # Add filter choices
        from apps.organizations.models import OrganizationUnit, Position

        from .constants import AppointmentStatus, LeadershipLevel, LeadershipStatus

        context["leadership_levels"] = LeadershipLevel.choices
        positions_qs = Position.objects.filter(status="ACTIVE").order_by("title")
        context["positions"] = positions_qs
        org_units_qs = OrganizationUnit.objects.filter(status="ACTIVE").order_by("name")
        context["org_units"] = org_units_qs
        directorates_qs = OrganizationUnit.objects.filter(
            status="ACTIVE", unit_type="DIRECTORATE"
        ).order_by("name")
        context["directorates"] = directorates_qs
        regions_qs = OrganizationUnit.objects.filter(
            status="ACTIVE", unit_type="REGION"
        ).order_by("name")
        context["regions"] = regions_qs
        districts_qs = OrganizationUnit.objects.filter(
            status="ACTIVE", unit_type="DISTRICT"
        ).order_by("name")
        context["districts"] = districts_qs
        communities_qs = OrganizationUnit.objects.filter(
            status="ACTIVE", unit_type="COMMUNITY"
        ).order_by("name")
        context["communities"] = communities_qs
        context["statuses"] = LeadershipStatus.choices
        context["appointment_statuses"] = AppointmentStatus.choices

        # Current filter values
        get = self.request.GET.get
        context["current_search"] = get("search", "")
        context["current_leadership_level"] = get("leadership_level", "")
        context["current_position"] = get("position", "")
        context["current_org_unit"] = get("organizational_unit", "")
        context["current_directorate"] = get("directorate", "")
        context["current_region"] = get("region", "")
        context["current_district"] = get("district", "")
        context["current_community"] = get("community", "")
        context["current_status"] = get("status", "")
        context["current_appointment_status"] = get("appointment_status", "")
        context["current_date_from"] = get("date_appointed_from", "")
        context["current_date_to"] = get("date_appointed_to", "")
        context["current_sort"] = get("sort", "user__last_name")

        # Summary statistics
        context.update({
            "total_personnel": total_personnel,
            "active_leaders": active_leaders,
            "leaders_count": leaders_count,
            "staff_count": staff_count,
            "directorates_count": directorates_count,
            "departments_count": departments_count,
        })

        return context


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
            "organizational_unit",
        ).order_by("-effective_date")
        context["attendance"] = self.object.attendance_records.order_by(
            "-attendance_date",
        )[:10]
        context["leave_records"] = self.object.leave_records.order_by(
            "-start_date",
        )[:10]
        context["tasks"] = self.object.tasks.order_by("-due_date")[:10]
        context["goals"] = self.object.goals.order_by("-due_date")[:10]
        context["kpis"] = self.object.kpis.order_by("-period_end")[:10]
        context["coaching_records"] = self.object.coaching_records.order_by(
            "-session_date",
        )[:5]
        context["mentorship_records"] = self.object.mentorship_records.order_by(
            "-start_date",
        )[:5]
        context["performance_reviews"] = self.object.performance_reviews.order_by(
            "-period_end",
        )[:5]
        context["recognition_records"] = self.object.recognition_records.order_by(
            "-date_awarded",
        )[:5]
        context["disciplinary_records"] = self.object.disciplinary_records.order_by(
            "-incident_date",
        )[:5]
        context["documents"] = self.object.documents.order_by("-created_at")[:10]
        context["status_history"] = self.object.status_history.order_by(
            "-changed_at",
        )[:10]
        context["scorecards"] = self.object.scorecards.order_by("-period_end")[:5]
        context["succession_plans"] = SuccessionPlan.objects.filter(
            current_holder=self.object
        ).order_by("-created_at")

        # Direct reports
        context["direct_reports"] = self.object.direct_reports.filter(
            status__in=["ACTIVE", "APPOINTED", "ACTING"]
        ).select_related("user", "position", "organizational_unit")

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

    def form_valid(self, form):
        try:
            # Reference numbers are issued by the service layer, never
            # accepted from web input.
            payload = {
                key: value
                for key, value in form.cleaned_data.items()
                if key != "reference_number"
            }
            profile = CreateLeadershipProfileService(user=self.request.user).execute(
                **payload,
            )
        except ValidationError as exc:
            form.add_error(None, _form_error_message(exc))
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Leadership profile {profile.reference_number} created successfully.",
        )
        self.object = profile
        return redirect(self.get_success_url())


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
    """List all leadership appointments with search and filtering."""

    model = LeadershipAppointment
    template_name = "leadership/appointment_list.html"
    context_object_name = "appointments"
    paginate_by = 20
    permission_required = LEADERSHIP_VIEW

    def get_queryset(self):
        queryset = LeadershipAppointment.objects.select_related(
            "profile__user",
            "position",
            "organizational_unit",
            "appointing_authority",
        ).order_by("-created_at")

        # Search
        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(profile__user__first_name__icontains=search_query)
                | Q(profile__user__last_name__icontains=search_query)
                | Q(profile__user__email__icontains=search_query)
                | Q(reference_number__icontains=search_query)
                | Q(position__title__icontains=search_query)
                | Q(organizational_unit__name__icontains=search_query)
                | Q(appointing_authority__first_name__icontains=search_query)
                | Q(appointing_authority__last_name__icontains=search_query)
            )

        # Filters
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        appointment_type = self.request.GET.get("appointment_type")
        if appointment_type:
            queryset = queryset.filter(appointment_type=appointment_type)

        org_unit_id = self.request.GET.get("organizational_unit")
        if org_unit_id:
            queryset = queryset.filter(organizational_unit_id=org_unit_id)

        effective_from = self.request.GET.get("effective_from")
        if effective_from:
            queryset = queryset.filter(effective_date__gte=effective_from)

        effective_to = self.request.GET.get("effective_to")
        if effective_to:
            queryset = queryset.filter(effective_date__lte=effective_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filter choices
        from apps.organizations.models import OrganizationUnit

        from .constants import AppointmentStatus, AppointmentType

        context["appointment_statuses"] = AppointmentStatus.choices
        context["appointment_types"] = AppointmentType.choices
        org_units_qs = OrganizationUnit.objects.filter(status="ACTIVE").order_by("name")
        context["org_units"] = org_units_qs

        # Current filter values
        get = self.request.GET.get
        context["current_search"] = get("search", "")
        context["current_status"] = get("status", "")
        context["current_appointment_type"] = get("appointment_type", "")
        context["current_org_unit"] = get("organizational_unit", "")
        context["current_effective_from"] = get("effective_from", "")
        context["current_effective_to"] = get("effective_to", "")

        return context


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

    def form_valid(self, form):
        try:
            appointment = CreateLeadershipAppointmentService(
                user=self.request.user
            ).execute(**form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, _form_error_message(exc))
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Appointment {appointment.reference_number} created successfully.",
        )
        return redirect("leadership:appointment_detail", pk=appointment.pk)


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
