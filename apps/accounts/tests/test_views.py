import pytest
from django.urls import reverse

from apps.accounts.constants import AccountStatus
from apps.accounts.models import OTPCode, User, UserSession
from apps.accounts.services import CreateInvitationService, GenerateOTPService


@pytest.mark.django_db
def test_login_view(client):
    """Test login page rendering and authentication."""
    user = User.objects.create_user(
        email="loginview@example.com",
        username="loginviewuser",
        first_name="Login",
        last_name="View",
        password="Password123!@",
    )
    user.status = AccountStatus.ACTIVE
    user.save()

    # Get login page
    response = client.get(reverse("core:login"))
    assert response.status_code == 200
    assert "Sign in" in response.content.decode()

    # Login POST fail
    response = client.post(
        reverse("core:login"),
        {"username": "loginview@example.com", "password": "WrongPassword"},
    )
    assert response.status_code == 200
    assert "Invalid credentials." in response.content.decode()

    # Login POST success
    response = client.post(
        reverse("core:login"),
        {"username": "loginview@example.com", "password": "Password123!@"},
    )
    assert response.status_code == 302
    assert response["Location"] == reverse("core:dashboard_preview")


@pytest.mark.django_db
def test_register_view(client):
    """Test registration via invitation link."""
    inv = CreateInvitationService().execute(email="registerview@example.com")

    # Get registration form with token
    response = client.get(reverse("core:register", kwargs={"token": inv.token}))
    assert response.status_code == 200
    assert "Create your account" in response.content.decode()

    # Register POST success
    response = client.post(
        reverse("core:register", kwargs={"token": inv.token}),
        {
            "username": "registerviewuser",
            "first_name": "Register",
            "last_name": "View",
            "phone_number": "999999",
            "password": "Password123!@",
            "confirm_password": "Password123!@",
        },
    )
    assert response.status_code == 302
    assert response["Location"] == reverse(
        "core:verify_email", kwargs={"email": "registerview@example.com"}
    )

    # Verify user exists in database
    user = User.objects.get(email="registerview@example.com")
    assert user.username == "registerviewuser"
    assert user.email_verified is False


@pytest.mark.django_db
def test_verify_email_view(client):
    """Test email verification with OTP."""
    user = User.objects.create_user(
        email="emailverify@example.com",
        username="emailverifyuser",
        first_name="Email",
        last_name="Verify",
    )
    user.status = AccountStatus.PENDING_VERIFICATION
    user.save()

    otp = GenerateOTPService().execute(
        email="emailverify@example.com",
        purpose=OTPCode.OTPPurpose.EMAIL_VERIFICATION,
    )

    # POST OTP verification
    response = client.post(
        reverse("core:verify_email", kwargs={"email": user.email}),
        {"code": otp.code},
    )
    assert response.status_code == 302
    assert response["Location"] == reverse("core:login")

    user.refresh_from_db()
    assert user.email_verified is True
    assert user.status == AccountStatus.ACTIVE


@pytest.mark.django_db
def test_profile_view(client):
    """Test profile page access and editing."""
    user = User.objects.create_user(
        email="profileview@example.com",
        username="profileviewuser",
        first_name="Profile",
        last_name="View",
        password="Password123!@",
    )
    user.status = AccountStatus.ACTIVE
    user.save()
    from apps.accounts.models import UserProfile

    UserProfile.objects.create(user=user, preferred_display_name="Profile View")

    # Authenticate client
    client.login(username="profileview@example.com", password="Password123!@")

    # Get profile page
    response = client.get(reverse("core:profile"))
    assert response.status_code == 200

    # POST profile changes
    response = client.post(
        reverse("core:profile"),
        {
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast",
            "phone_number": "1234567890",
            "preferred_display_name": "Updated Display",
            "gender": "Male",
            "province": "Lusaka",
            "district": "Lusaka",
        },
    )
    assert response.status_code == 302
    assert response["Location"] == reverse("core:profile")

    user.refresh_from_db()
    assert user.first_name == "UpdatedFirst"
    assert user.last_name == "UpdatedLast"
    assert user.phone_number == "1234567890"
    assert user.profile.preferred_display_name == "Updated Display"
    assert user.profile.province == "Lusaka"


@pytest.mark.django_db
def test_sessions_view(client):
    """Test sessions management page and revoking session."""
    user = User.objects.create_user(
        email="sessionsview@example.com",
        username="sessionsviewuser",
        first_name="Sessions",
        last_name="View",
        password="Password123!@",
    )
    user.status = AccountStatus.ACTIVE
    user.save()

    # Authenticate client
    client.login(username="sessionsview@example.com", password="Password123!@")

    # Create another session in DB
    other_session = UserSession.objects.create(
        user=user,
        session_key="other_dummy_session_key",
        ip_address="1.1.1.1",
        user_agent="Firefox",
    )

    # Get sessions page
    response = client.get(reverse("core:sessions"))
    assert response.status_code == 200
    assert (
        "other_dummy_session_key" not in response.content.decode()
    )  # Displays device name instead of key

    # Terminate the other session
    response = client.get(
        reverse("core:terminate_session", kwargs={"session_id": other_session.id})
    )
    assert response.status_code == 302
    assert response["Location"] == reverse("core:sessions")

    other_session.refresh_from_db()
    assert other_session.is_active is False


@pytest.mark.django_db
def test_password_reset_full_flow(client):
    """Test request OTP, verify it, and confirm a new password."""
    user = User.objects.create_user(
        email="resetflow@example.com",
        username="resetflowuser",
        first_name="Reset",
        last_name="Flow",
        password="OldPassword123!",
    )
    user.status = AccountStatus.ACTIVE
    user.save()

    # Request password reset
    response = client.post(
        reverse("core:password_reset"), {"email": "resetflow@example.com"}
    )
    assert response.status_code == 302
    assert response["Location"] == reverse(
        "core:password_reset_verify", kwargs={"email": "resetflow@example.com"}
    )

    otp = OTPCode.objects.get(
        email__iexact="resetflow@example.com",
        purpose=OTPCode.OTPPurpose.PASSWORD_RESET,
        is_verified=False,
    )

    # Verify the OTP
    response = client.post(
        reverse(
            "core:password_reset_verify", kwargs={"email": "resetflow@example.com"}
        ),
        {"code": otp.code},
    )
    assert response.status_code == 302
    assert response["Location"] == reverse(
        "core:password_reset_confirm", kwargs={"email": "resetflow@example.com"}
    )

    # Confirm new password
    response = client.post(
        reverse(
            "core:password_reset_confirm", kwargs={"email": "resetflow@example.com"}
        ),
        {
            "new_password": "NewPassword456!@",
            "confirm_new_password": "NewPassword456!@",
        },
    )
    assert response.status_code == 302
    assert response["Location"] == reverse("core:login")

    # Old password no longer works, new password does
    assert (
        client.login(username="resetflow@example.com", password="OldPassword123!")
        is False
    )
    assert (
        client.login(username="resetflow@example.com", password="NewPassword456!@")
        is True
    )


@pytest.mark.django_db
def test_password_reset_confirm_requires_verification(client):
    """POST to password reset confirm without OTP verification is rejected."""
    User.objects.create_user(
        email="resetguard@example.com",
        username="resetguarduser",
        first_name="Reset",
        last_name="Guard",
        password="OldPassword123!",
    )

    response = client.post(
        reverse(
            "core:password_reset_confirm",
            kwargs={"email": "resetguard@example.com"},
        ),
        {
            "new_password": "NewPassword456!@",
            "confirm_new_password": "NewPassword456!@",
        },
    )
    assert response.status_code == 302
    assert response["Location"] == reverse("core:password_reset")
