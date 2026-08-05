import logging
import secrets
from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.services import BaseService

from .constants import AccountStatus
from .models import OTPCode, User, UserInvitation, UserProfile, UserSession
from .validators import validate_invitation_token, validate_password_strength

logger = logging.getLogger(__name__)


class CreateInvitationService(BaseService):
    """
    Creates a new user invitation.
    Invalidates any previous pending invitations for the same email.
    """

    def _execute(self, email: str, expires_in_days: int = 7) -> UserInvitation:
        # Revoke or clean up previous pending/valid invitations for this email
        UserInvitation.objects.filter(
            email__iexact=email, status=UserInvitation.InvitationStatus.PENDING
        ).update(status=UserInvitation.InvitationStatus.REVOKED)

        # Calculate expiration date
        expires_at = timezone.now() + timedelta(days=expires_in_days)

        # Create the new invitation
        invitation = UserInvitation.objects.create(
            email=email.lower(),
            expires_at=expires_at,
            created_by=self.user,
        )

        logger.info(
            f"Created invitation {invitation.token} for email {email} "
            f"(Expires: {expires_at})"
        )
        return invitation


class AcceptInvitationService(BaseService):
    """
    Registers a new user using a valid invitation token.
    Updates the invitation status to ACCEPTED.
    """

    def _execute(
        self,
        token_str: str,
        username: str,
        first_name: str,
        last_name: str,
        password: str,
        phone_number: str = "",
    ) -> User:
        # Validate the token
        invitation = validate_invitation_token(token_str)

        # Check if username or email is already taken
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(
                _("A user with that username already exists."),
                code="username_taken",
            )
        if User.objects.filter(email__iexact=invitation.email).exists():
            raise ValidationError(
                _("A user with that email already exists."),
                code="email_taken",
            )

        # Validate password strength
        validate_password_strength(password)

        # Create user account
        user = User.objects.create_user(
            email=invitation.email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            phone_number=phone_number,
            # Requires email verification next
            status=AccountStatus.PENDING_VERIFICATION,
            email_verified=False,
        )

        # Create profile
        UserProfile.objects.create(
            user=user,
            preferred_display_name=f"{first_name} {last_name}",
        )

        # Update invitation status
        invitation.status = UserInvitation.InvitationStatus.ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.save()

        logger.info(
            f"User {user.email} registered successfully via "
            f"invitation {invitation.token}"
        )
        return user


class AuthenticateUserService(BaseService):
    """
    Authenticates a user via email and password.
    Implements failed attempt tracking and brute force lockout.
    """

    def execute(self, email: str, password: str) -> User:
        # Override execute to bypass transaction.atomic()
        # so that failed login attempts persist even if a ValidationError is raised.
        try:
            return self._execute(email, password)
        except Exception as e:
            logger.exception(f"Error executing {self.__class__.__name__}: {e!s}")
            raise

    def _execute(self, email: str, password: str) -> User:
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Prevent timing attacks by hashing password anyway
            User().set_password(password)
            raise ValidationError(
                _("Invalid credentials."),
                code="invalid_credentials",
            ) from None

        # Check if account is locked
        if user.is_locked():
            raise ValidationError(
                _(
                    "This account is temporarily locked due to too many "
                    "failed login attempts. Please try again later."
                ),
                code="account_locked",
            )

        # Check if user is active/disabled/suspended
        if not user.is_active or user.status in [
            AccountStatus.SUSPENDED,
            AccountStatus.INACTIVE,
            AccountStatus.ARCHIVED,
        ]:
            raise ValidationError(
                _("This account is suspended or disabled. Please contact support."),
                code="account_disabled",
            )

        # Authenticate credentials using standard Django kwargs
        authenticated_user = authenticate(username=email, password=password)

        if authenticated_user is None:
            # Increment failed attempts
            user.login_attempts += 1
            if user.login_attempts >= 5:  # Lock after 5 failed attempts
                user.locked_until = timezone.now() + timedelta(minutes=15)
                logger.warning(
                    f"User account {user.email} locked until {user.locked_until} "
                    "due to failed login attempts"
                )
            user.save()
            raise ValidationError(
                _("Invalid credentials."),
                code="invalid_credentials",
            )

        # Authentication success: reset login attempts
        if user.login_attempts > 0 or user.locked_until:
            user.login_attempts = 0
            user.locked_until = None
            user.save()

        return user


class ActivateUserService(BaseService):
    """
    Activates an inactive or suspended user account.
    """

    def _execute(self, user_to_activate: User) -> User:
        user_to_activate.status = AccountStatus.ACTIVE
        user_to_activate.is_active = True
        user_to_activate.save()
        logger.info(
            f"User account {user_to_activate.email} activated by "
            f"administrator {self.user}"
        )
        return user_to_activate


class DeactivateUserService(BaseService):
    """
    Deactivates/Suspends a user account.
    """

    def _execute(
        self, user_to_deactivate: User, status: str = AccountStatus.SUSPENDED
    ) -> User:
        if status not in [
            AccountStatus.SUSPENDED,
            AccountStatus.INACTIVE,
            AccountStatus.ARCHIVED,
        ]:
            status = AccountStatus.SUSPENDED
        user_to_deactivate.status = status
        user_to_deactivate.save()
        logger.info(
            f"User account {user_to_deactivate.email} deactivated with "
            f"status {status} by {self.user}"
        )
        return user_to_deactivate


class ChangePasswordService(BaseService):
    """
    Securely changes the user's password.
    Requires validating current password.
    """

    def _execute(
        self, target_user: User, current_password: str, new_password: str
    ) -> User:
        if not target_user.check_password(current_password):
            raise ValidationError(
                _("Your current password is incorrect."),
                code="incorrect_current_password",
            )

        validate_password_strength(new_password)

        target_user.set_password(new_password)
        target_user.password_updated_at = timezone.now()
        target_user.save()

        logger.info(f"Password changed for user {target_user.email}")
        return target_user


class GenerateOTPService(BaseService):
    """
    Generates a 6-digit OTP code for verification/resets.
    Invalidates previous OTPs for that email/purpose.
    """

    def _execute(self, email: str, purpose: str, expiry_minutes: int = 10) -> OTPCode:
        # Invalidate old OTPs
        OTPCode.objects.filter(
            email__iexact=email, purpose=purpose, is_verified=False
        ).update(is_verified=True)

        # OTPs must use a cryptographically secure source of randomness.
        code = "".join(secrets.choice("0123456789") for _ in range(6))
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

        otp = OTPCode.objects.create(
            email=email.lower(),
            code=code,
            purpose=purpose,
            expires_at=expires_at,
        )

        # Console logging for easy access in dev
        logger.info(
            f"Generated OTP {code} for {email} "
            f"(Purpose: {purpose}, Expires: {expires_at})"
        )
        return otp


class VerifyOTPService(BaseService):
    """
    Verifies an OTP code for a specific email and purpose.
    Marks the code as verified if valid.
    """

    def _execute(self, email: str, code: str, purpose: str) -> OTPCode:
        try:
            otp = OTPCode.objects.get(
                email__iexact=email,
                code=code,
                purpose=purpose,
                is_verified=False,
                expires_at__gt=timezone.now(),
            )
        except OTPCode.DoesNotExist:
            raise ValidationError(
                _("Invalid or expired OTP code."),
                code="invalid_otp",
            ) from None

        otp.is_verified = True
        otp.save()
        logger.info(f"Verified OTP code for {email} (Purpose: {purpose})")
        return otp


class VerifyEmailService(BaseService):
    """
    Verifies email using an OTP code, and activates the user account if pending.
    """

    def _execute(self, email: str, code: str) -> User:
        # Verify the OTP first
        VerifyOTPService(user=self.user).execute(
            email=email, code=code, purpose=OTPCode.OTPPurpose.EMAIL_VERIFICATION
        )

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise ValidationError(_("User not found."), code="user_not_found") from None

        user.email_verified = True
        if user.status == AccountStatus.PENDING_VERIFICATION:
            user.status = AccountStatus.ACTIVE
            user.is_active = True

        user.save()
        logger.info(f"Email verified and user active for {user.email}")
        return user


class TerminateSessionService(BaseService):
    """
    Invalidates a tracked UserSession and deletes Django's backend session.
    If session_key is None and user is provided, terminates ALL active
    sessions for that user.
    """

    def _execute(
        self,
        session_key: str | None = None,
        target_user: User | None = None,
    ) -> None:
        if session_key:
            # Terminate a single session
            UserSession.objects.filter(session_key=session_key).update(is_active=False)
            try:
                session = Session.objects.get(session_key=session_key)
                session.delete()
            except Session.DoesNotExist:
                pass
            logger.info(f"Terminated session {session_key}")
        elif target_user:
            # Terminate all sessions for a user
            user_sessions = UserSession.objects.filter(user=target_user, is_active=True)
            session_keys = list(user_sessions.values_list("session_key", flat=True))

            user_sessions.update(is_active=False)
            Session.objects.filter(session_key__in=session_keys).delete()
            logger.info(
                f"Terminated all {len(session_keys)} sessions for "
                f"user {target_user.email}"
            )
