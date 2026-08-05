import pytest
from django.core.exceptions import ValidationError

from apps.accounts.constants import AccountStatus
from apps.accounts.models import OTPCode, User, UserInvitation
from apps.accounts.services import (
    AcceptInvitationService,
    AuthenticateUserService,
    ChangePasswordService,
    CreateInvitationService,
    GenerateOTPService,
    VerifyEmailService,
    VerifyOTPService,
)


@pytest.mark.django_db
def test_create_invitation_service():
    """Verify CreateInvitationService revokes previous pending invitations."""
    email = "invite@example.com"
    # Create a previous invitation
    prev_inv = CreateInvitationService().execute(email=email)

    # Create new one
    new_inv = CreateInvitationService().execute(email=email)

    prev_inv.refresh_from_db()
    assert prev_inv.status == UserInvitation.InvitationStatus.REVOKED
    assert new_inv.status == UserInvitation.InvitationStatus.PENDING
    assert new_inv.email == email


@pytest.mark.django_db
def test_accept_invitation_service():
    """Verify AcceptInvitationService registers a user and consumes the invitation."""
    inv = CreateInvitationService().execute(email="newuser@example.com")

    user = AcceptInvitationService().execute(
        token_str=str(inv.token),
        username="newuser",
        first_name="New",
        last_name="User",
        password="Password123!@",
        phone_number="123456",
    )

    assert user.email == "newuser@example.com"
    assert user.username == "newuser"
    assert user.profile is not None
    assert user.profile.preferred_display_name == "New User"

    inv.refresh_from_db()
    assert inv.status == UserInvitation.InvitationStatus.ACCEPTED
    assert inv.accepted_at is not None


@pytest.mark.django_db
def test_authenticate_user_service():
    """Verify AuthenticateUserService checks credentials and locking."""
    user = User.objects.create_user(
        email="auth@example.com",
        username="authuser",
        first_name="Auth",
        last_name="User",
        password="TestPassword123!",
    )
    user.status = AccountStatus.ACTIVE
    user.save()

    # Success
    auth_user = AuthenticateUserService().execute(
        email="auth@example.com", password="TestPassword123!"
    )
    assert auth_user == user

    # Fail
    with pytest.raises(ValidationError):
        AuthenticateUserService().execute(
            email="auth@example.com", password="WrongPassword"
        )

    user.refresh_from_db()
    assert user.login_attempts == 1

    # Lockout test
    user.login_attempts = 4
    user.save()
    with pytest.raises(ValidationError):
        AuthenticateUserService().execute(
            email="auth@example.com", password="WrongPassword"
        )
    user.refresh_from_db()
    assert user.is_locked() is True


@pytest.mark.django_db
def test_change_password_service():
    """Verify ChangePasswordService updates passwords and hashes securely."""
    user = User.objects.create_user(
        email="change@example.com",
        username="changeuser",
        first_name="Change",
        last_name="User",
        password="OldPassword123!",
    )

    # Wrong current password
    with pytest.raises(ValidationError):
        ChangePasswordService().execute(
            target_user=user,
            current_password="WrongPassword",
            new_password="NewPassword123!@",
        )

    # Success
    ChangePasswordService().execute(
        target_user=user,
        current_password="OldPassword123!",
        new_password="NewPassword123!@",
    )
    assert user.check_password("NewPassword123!@") is True
    assert user.password_updated_at is not None


@pytest.mark.django_db
def test_otp_services():
    """Verify OTP generation and verification."""
    email = "otp@example.com"
    otp = GenerateOTPService().execute(
        email=email, purpose=OTPCode.OTPPurpose.EMAIL_VERIFICATION
    )
    assert otp.email == email
    assert len(otp.code) == 6

    # Verify Success
    verified_otp = VerifyOTPService().execute(
        email=email, code=otp.code, purpose=OTPCode.OTPPurpose.EMAIL_VERIFICATION
    )
    assert verified_otp.is_verified is True

    # Verify Fail (already verified)
    with pytest.raises(ValidationError):
        VerifyOTPService().execute(
            email=email, code=otp.code, purpose=OTPCode.OTPPurpose.EMAIL_VERIFICATION
        )


@pytest.mark.django_db
def test_verify_email_service():
    """Verify VerifyEmailService verifies email and activates user."""
    user = User.objects.create_user(
        email="verify@example.com",
        username="verifyuser",
        first_name="Verify",
        last_name="User",
    )
    user.status = AccountStatus.PENDING_VERIFICATION
    user.save()

    otp = GenerateOTPService().execute(
        email=user.email, purpose=OTPCode.OTPPurpose.EMAIL_VERIFICATION
    )

    VerifyEmailService().execute(email=user.email, code=otp.code)

    user.refresh_from_db()
    assert user.email_verified is True
    assert user.status == AccountStatus.ACTIVE
    assert user.is_active is True
