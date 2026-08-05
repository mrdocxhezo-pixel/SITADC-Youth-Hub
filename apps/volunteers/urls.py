"""
URL routing for the volunteer management module.
"""

from django.urls import path

from . import views

app_name = "volunteers"

urlpatterns = [
    path("dashboard/", views.VolunteerDashboardView.as_view(), name="dashboard"),
    path("directory/", views.VolunteerDirectoryView.as_view(), name="directory"),
    path("profile/create/", views.VolunteerCreateView.as_view(), name="create"),
    path("profile/<uuid:pk>/", views.VolunteerDetailView.as_view(), name="detail"),
    path("profile/<uuid:pk>/edit/", views.VolunteerUpdateView.as_view(), name="update"),
    path(
        "profile/<uuid:pk>/id-card/",
        views.VolunteerIdCardView.as_view(),
        name="id_card",
    ),
    # Recruitment & Applications
    path(
        "recruitment/",
        views.VolunteerRecruitmentListView.as_view(),
        name="recruitment_list",
    ),
    path(
        "recruitment/create/",
        views.VolunteerRecruitmentCreateView.as_view(),
        name="recruitment_create",
    ),
    path("apply/", views.VolunteerApplicationCreateView.as_view(), name="apply"),
    path(
        "apply/success/",
        views.VolunteerApplicationSuccessView.as_view(),
        name="application_success",
    ),
    path(
        "application/<uuid:pk>/",
        views.VolunteerApplicationDetailView.as_view(),
        name="application_detail",
    ),
    path(
        "application/<uuid:pk>/review/",
        views.VolunteerApplicationReviewView.as_view(),
        name="application_review",
    ),
    path(
        "application/<uuid:application_pk>/screening/",
        views.VolunteerScreeningView.as_view(),
        name="application_screening",
    ),
    path(
        "application/<uuid:application_pk>/interview/",
        views.VolunteerInterviewView.as_view(),
        name="application_interview",
    ),
    path(
        "application/<uuid:pk>/cv/",
        views.VolunteerApplicationCVDownloadView.as_view(),
        name="application_cv_download",
    ),
    path(
        "profile/<uuid:profile_pk>/onboarding/",
        views.VolunteerOnboardingView.as_view(),
        name="onboarding",
    ),
    # Assignments
    path(
        "assignments/",
        views.VolunteerAssignmentListView.as_view(),
        name="assignment_list",
    ),
    path(
        "assignments/create/",
        views.VolunteerAssignmentCreateView.as_view(),
        name="assignment_create",
    ),
    # Attendance
    path(
        "attendance/",
        views.VolunteerAttendanceListView.as_view(),
        name="attendance_list",
    ),
    path(
        "attendance/log/",
        views.VolunteerAttendanceCreateView.as_view(),
        name="attendance_create",
    ),
    # Training
    path("trainings/", views.VolunteerTrainingListView.as_view(), name="training_list"),
    path(
        "trainings/add/",
        views.VolunteerTrainingCreateView.as_view(),
        name="training_create",
    ),
    # Performance
    path(
        "performance/",
        views.VolunteerPerformanceListView.as_view(),
        name="performance_list",
    ),
    path(
        "performance/add/",
        views.VolunteerPerformanceCreateView.as_view(),
        name="performance_create",
    ),
    # Recognition
    path(
        "recognitions/",
        views.VolunteerRecognitionListView.as_view(),
        name="recognition_list",
    ),
    path(
        "recognitions/award/",
        views.VolunteerRecognitionCreateView.as_view(),
        name="recognition_create",
    ),
    # Leave
    path("leaves/", views.VolunteerLeaveListView.as_view(), name="leave_list"),
    path(
        "leaves/apply/", views.VolunteerLeaveCreateView.as_view(), name="leave_create"
    ),
    path(
        "leaves/<uuid:pk>/approve/",
        views.VolunteerLeaveApproveView.as_view(),
        name="leave_approve",
    ),
    # Exit
    path("exits/", views.VolunteerExitListView.as_view(), name="exit_list"),
    path(
        "exits/initiate/", views.VolunteerExitCreateView.as_view(), name="exit_create"
    ),
    # Reports & Exports
    path("reports/", views.VolunteerReportView.as_view(), name="reports"),
    # Activity Logs
    path(
        "activity-logs/",
        views.VolunteerActivityLogListView.as_view(),
        name="activity_log_list",
    ),
    path(
        "activity-logs/log/",
        views.VolunteerActivityLogCreateView.as_view(),
        name="activity_log_create",
    ),
    # Disciplinary
    path(
        "disciplinary/",
        views.VolunteerDisciplinaryListView.as_view(),
        name="disciplinary_list",
    ),
    path(
        "disciplinary/open/",
        views.VolunteerDisciplinaryCreateView.as_view(),
        name="disciplinary_create",
    ),
    path(
        "disciplinary/<uuid:pk>/",
        views.VolunteerDisciplinaryDetailView.as_view(),
        name="disciplinary_detail",
    ),
    path(
        "disciplinary/<uuid:pk>/decide/",
        views.VolunteerDisciplinaryDecisionView.as_view(),
        name="disciplinary_decide",
    ),
    # Communications
    path(
        "communications/",
        views.VolunteerCommunicationListView.as_view(),
        name="communication_list",
    ),
    path(
        "communications/record/",
        views.VolunteerCommunicationCreateView.as_view(),
        name="communication_create",
    ),
    # Documents
    path("documents/", views.VolunteerDocumentListView.as_view(), name="document_list"),
    path(
        "documents/upload/",
        views.VolunteerDocumentUploadView.as_view(),
        name="document_upload",
    ),
    path(
        "documents/<uuid:pk>/review/",
        views.VolunteerDocumentReviewView.as_view(),
        name="document_review",
    ),
    path(
        "documents/<uuid:pk>/archive/",
        views.VolunteerDocumentArchiveView.as_view(),
        name="document_archive",
    ),
    path(
        "documents/<uuid:pk>/download/",
        views.VolunteerDocumentDownloadView.as_view(),
        name="document_download",
    ),
    # Taxonomy
    path(
        "categories/",
        views.VolunteerCategoryListView.as_view(),
        name="category_list",
    ),
    path(
        "categories/create/",
        views.VolunteerCategoryCreateView.as_view(),
        name="category_create",
    ),
    path(
        "categories/<uuid:pk>/edit/",
        views.VolunteerCategoryUpdateView.as_view(),
        name="category_update",
    ),
]
