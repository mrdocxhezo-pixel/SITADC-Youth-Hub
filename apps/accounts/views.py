import logging

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from .forms import (
    LoginForm,
    OTPVerificationForm,
    PasswordChangeForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    ProfileUpdateForm,
    RegisterForm,
)
from .models import OTPCode, User, UserSession
from .selectors import get_active_sessions_for_user
from .services import (
    AcceptInvitationService,
    AuthenticateUserService,
    ChangePasswordService,
    GenerateOTPService,
    TerminateSessionService,
    VerifyEmailService,
    VerifyOTPService,
)

logger = logging.getLogger(__name__)


def login_view(request):
    """
    User login view with Remember Me support.
    """
    if request.user.is_authenticated:
        return redirect("core:dashboard_preview")

    next_url = (
        request.GET.get("next") or request.POST.get("next") or "core:dashboard_preview"
    )

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            remember = form.cleaned_data["remember"]

            try:
                user = AuthenticateUserService(user=None).execute(
                    email=email, password=password
                )

                # Standard Django login
                auth_login(request, user)

                # Remember Me handling
                if remember:
                    # Keep session for 30 days
                    request.session.set_expiry(2592000)
                else:
                    # Expire when browser closes
                    request.session.set_expiry(0)

                # Track user session
                ip = request.META.get("REMOTE_ADDR")
                ua = request.META.get("HTTP_USER_AGENT", "")[:255]
                UserSession.objects.update_or_create(
                    session_key=request.session.session_key,
                    defaults={
                        "user": user,
                        "ip_address": ip,
                        "user_agent": ua,
                        "last_activity": timezone.now(),
                        "is_active": True,
                    },
                )

                messages.success(request, _("Signed in successfully."))
                if next_url.startswith("/"):
                    return redirect(next_url)
                return redirect(next_url)

            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = LoginForm()

    return render(request, "auth/login.html", {"form": form, "next": next_url})


def logout_view(request):
    """
    User logout view. Invalidates session.
    """
    if request.user.is_authenticated:
        # Terminate active session in DB
        session_key = request.session.session_key
        if session_key:
            TerminateSessionService(user=request.user).execute(session_key=session_key)

        auth_logout(request)
        messages.success(request, _("Signed out successfully."))

    return redirect("core:login")


class RegisterView(View):
    """
    View for registration by invitation token.
    """

    def get(self, request, token):
        # Validate token first
        try:
            from .validators import validate_invitation_token

            invitation = validate_invitation_token(str(token))
        except ValidationError as e:
            return render(request, "auth/error.html", {"error_message": e.message})

        form = RegisterForm(initial={"username": invitation.email.split("@")[0]})
        return render(
            request, "auth/register.html", {"form": form, "invitation": invitation}
        )

    def post(self, request, token):
        try:
            from .validators import validate_invitation_token

            invitation = validate_invitation_token(str(token))
        except ValidationError as e:
            return render(request, "auth/error.html", {"error_message": e.message})

        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = AcceptInvitationService(user=None).execute(
                    token_str=str(token),
                    username=form.cleaned_data["username"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    password=form.cleaned_data["password"],
                    phone_number=form.cleaned_data["phone_number"],
                )

                # Generate Email Verification OTP
                GenerateOTPService(user=user).execute(
                    email=user.email,
                    purpose=OTPCode.OTPPurpose.EMAIL_VERIFICATION,
                )

                messages.success(
                    request,
                    _(
                        "Registration completed! Please verify your email "
                        "using the OTP sent to your mailbox."
                    ),
                )
                return redirect("core:verify_email", email=user.email)

            except ValidationError as e:
                form.add_error(None, e)

        return render(
            request, "auth/register.html", {"form": form, "invitation": invitation}
        )


class VerifyEmailView(View):
    """
    Verify email with 6-digit OTP code.
    """

    def get(self, request, email):
        form = OTPVerificationForm()
        return render(request, "auth/verify_email.html", {"form": form, "email": email})

    def post(self, request, email):
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            try:
                VerifyEmailService(user=None).execute(email=email, code=code)
                messages.success(
                    request,
                    _("Email verified successfully! You can now log in."),
                )
                return redirect("core:login")
            except ValidationError as e:
                form.add_error("code", e)

        return render(request, "auth/verify_email.html", {"form": form, "email": email})


def resend_verification_otp_view(request, email):
    """
    Resends the email verification OTP code.
    """
    try:
        user = User.objects.get(email__iexact=email)
        if user.email_verified:
            messages.info(request, _("This email is already verified."))
            return redirect("core:login")

        GenerateOTPService(user=user).execute(
            email=email, purpose=OTPCode.OTPPurpose.EMAIL_VERIFICATION
        )
        messages.success(
            request,
            _("A new verification code has been generated and printed to console."),
        )
    except User.DoesNotExist:
        messages.error(request, _("No account found for that email address."))

    return redirect("core:verify_email", email=email)


class PasswordResetRequestView(View):
    """
    Password reset request page.
    """

    def get(self, request):
        form = PasswordResetRequestForm()
        return render(request, "auth/forgot_password.html", {"form": form})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                user = User.objects.get(email__iexact=email)
                # Generate password reset OTP
                GenerateOTPService(user=user).execute(
                    email=email, purpose=OTPCode.OTPPurpose.PASSWORD_RESET
                )
            except User.DoesNotExist:
                # Silently handle to prevent email harvesting
                pass

            messages.success(
                request,
                _(
                    "If the email exists, a password reset verification code "
                    "has been printed to the console."
                ),
            )
            return redirect("core:password_reset_verify", email=email)

        return render(request, "auth/forgot_password.html", {"form": form})


class PasswordResetVerifyView(View):
    """
    Verify OTP for password reset.
    """

    def get(self, request, email):
        form = OTPVerificationForm()
        return render(
            request, "auth/password_reset_verify.html", {"form": form, "email": email}
        )

    def post(self, request, email):
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            try:
                # Verify the OTP
                VerifyOTPService(user=None).execute(
                    email=email,
                    code=code,
                    purpose=OTPCode.OTPPurpose.PASSWORD_RESET,
                )
                # Save to session that OTP has been verified
                request.session["reset_email_verified"] = email
                return redirect("core:password_reset_confirm", email=email)
            except ValidationError as e:
                form.add_error("code", e)

        return render(
            request, "auth/password_reset_verify.html", {"form": form, "email": email}
        )


class PasswordResetConfirmView(View):
    """
    Enter new password and confirm reset.
    """

    def get(self, request, email):
        if request.session.get("reset_email_verified") != email:
            messages.error(request, _("Verification required first."))
            return redirect("core:password_reset")

        form = PasswordResetConfirmForm()
        return render(
            request, "auth/reset_password.html", {"form": form, "email": email}
        )

    def post(self, request, email):
        if request.session.get("reset_email_verified") != email:
            messages.error(request, _("Verification required first."))
            return redirect("core:password_reset")

        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(email__iexact=email)
                password = form.cleaned_data["new_password"]

                with transaction.atomic():
                    user.set_password(password)
                    user.password_updated_at = timezone.now()
                    user.login_attempts = 0
                    user.locked_until = None
                    user.save()

                # Clear verified email from session
                del request.session["reset_email_verified"]

                messages.success(
                    request,
                    _("Password has been reset successfully! You can now log in."),
                )
                return redirect("core:login")

            except Exception as e:
                logger.error(f"Error resetting password: {e}")
                form.add_error(None, _("Failed to reset password."))

        return render(
            request, "auth/reset_password.html", {"form": form, "email": email}
        )


@login_required
def password_change_view(request):
    """
    Secure password change view for authenticated users.
    """
    if request.method == "POST":
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data["current_password"]
            new_password = form.cleaned_data["new_password"]
            try:
                ChangePasswordService(user=request.user).execute(
                    target_user=request.user,
                    current_password=current_password,
                    new_password=new_password,
                )
                messages.success(request, _("Password changed successfully."))
                return redirect("core:profile")
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = PasswordChangeForm()

    return render(request, "auth/change_password.html", {"form": form})


@login_required
def profile_view(request):
    """
    Profile management view.
    """
    profile = request.user.profile

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully."))
            return redirect("core:profile")
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, "auth/profile.html", {"form": form, "profile": profile})


class SessionManagementView(LoginRequiredMixin, View):
    """
    View user active devices and sessions, with ability to terminate them.
    """

    def get(self, request):
        sessions = get_active_sessions_for_user(request.user)
        current_session_key = request.session.session_key
        return render(
            request,
            "auth/sessions.html",
            {
                "sessions": sessions,
                "current_session_key": current_session_key,
            },
        )


@login_required
def terminate_session_view(request, session_id):
    """
    Terminates a specific tracked session.
    """
    user_session = get_object_or_404(UserSession, id=session_id, user=request.user)
    TerminateSessionService(user=request.user).execute(
        session_key=user_session.session_key
    )
    messages.success(request, _("Session terminated successfully."))
    return redirect("core:sessions")


@login_required
def terminate_all_sessions_view(request):
    """
    Terminates all sessions except the current active one.
    """
    current_key = request.session.session_key
    active_sessions = get_active_sessions_for_user(request.user)

    count = 0
    for sess in active_sessions:
        if sess.session_key != current_key:
            TerminateSessionService(user=request.user).execute(
                session_key=sess.session_key
            )
            count += 1

    messages.success(
        request,
        _("Terminated %(count)s other active session(s).") % {"count": count},
    )
    return redirect("core:sessions")
