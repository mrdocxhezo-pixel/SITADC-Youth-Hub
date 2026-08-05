from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/<uuid:token>/", views.RegisterView.as_view(), name="register"),
    path(
        "verify-email/<str:email>/",
        views.VerifyEmailView.as_view(),
        name="verify_email",
    ),
    path(
        "resend-verification/<str:email>/",
        views.resend_verification_otp_view,
        name="resend_verification",
    ),
    path(
        "password-reset/",
        views.PasswordResetRequestView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/verify/<str:email>/",
        views.PasswordResetVerifyView.as_view(),
        name="password_reset_verify",
    ),
    path(
        "password-reset/confirm/<str:email>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("password-change/", views.password_change_view, name="password_change"),
    path("profile/", views.profile_view, name="profile"),
    path("sessions/", views.SessionManagementView.as_view(), name="sessions"),
    path(
        "sessions/terminate/<uuid:session_id>/",
        views.terminate_session_view,
        name="terminate_session",
    ),
    path(
        "sessions/terminate-all/",
        views.terminate_all_sessions_view,
        name="terminate_all_sessions",
    ),
]
