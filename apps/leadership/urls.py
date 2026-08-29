"""URL configuration for the Leadership Management module."""

from django.urls import path, reverse_lazy
from django.views.generic import RedirectView

from . import views

app_name = "leadership"

urlpatterns = [
    # Dashboard
    path(
        "dashboard/",
        views.DashboardView.as_view(),
        name="dashboard",
    ),
    # Profile landing - redirect to directory
    path(
        "profile/",
        RedirectView.as_view(url=reverse_lazy("leadership:directory"), permanent=False),
        name="profile_index",
    ),
    # All Leaders & Staff Directory
    path(
        "leaders/",
        views.DirectoryView.as_view(),
        name="all_leaders",
    ),
    # Directory (legacy path)
    path(
        "directory/",
        views.DirectoryView.as_view(),
        name="directory",
    ),
    # Profiles
    path(
        "profile/create/",
        views.ProfileCreateView.as_view(),
        name="profile_create",
    ),
    path(
        "profile/<uuid:pk>/",
        views.ProfileDetailView.as_view(),
        name="profile_detail",
    ),
    path(
        "profile/<uuid:pk>/update/",
        views.ProfileUpdateView.as_view(),
        name="profile_update",
    ),
    # Appointments
    path(
        "appointments/",
        views.AppointmentListView.as_view(),
        name="appointment_list",
    ),
    path(
        "appointments/create/",
        views.AppointmentCreateView.as_view(),
        name="appointment_create",
    ),
    path(
        "appointments/<uuid:pk>/",
        views.AppointmentDetailView.as_view(),
        name="appointment_detail",
    ),
    path(
        "appointments/<uuid:pk>/update/",
        views.AppointmentUpdateView.as_view(),
        name="appointment_update",
    ),
    # Performance Reviews
    path(
        "reviews/",
        views.ReviewListView.as_view(),
        name="review_list",
    ),
    path(
        "reviews/create/",
        views.ReviewCreateView.as_view(),
        name="review_create",
    ),
    path(
        "reviews/<uuid:pk>/",
        views.ReviewDetailView.as_view(),
        name="review_detail",
    ),
    # Attendance
    path(
        "attendance/",
        views.AttendanceListView.as_view(),
        name="attendance_list",
    ),
    path(
        "attendance/mark/",
        views.AttendanceCreateView.as_view(),
        name="attendance_create",
    ),
    # Coaching
    path(
        "coaching/",
        views.CoachingListView.as_view(),
        name="coaching_list",
    ),
    path(
        "coaching/create/",
        views.CoachingCreateView.as_view(),
        name="coaching_create",
    ),
    # Mentorship
    path(
        "mentorship/",
        views.MentorshipListView.as_view(),
        name="mentorship_list",
    ),
    path(
        "mentorship/create/",
        views.MentorshipCreateView.as_view(),
        name="mentorship_create",
    ),
    # Succession
    path(
        "succession/",
        views.SuccessionListView.as_view(),
        name="succession_list",
    ),
    path(
        "succession/create/",
        views.SuccessionCreateView.as_view(),
        name="succession_create",
    ),
]
