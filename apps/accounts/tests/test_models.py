from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.constants import AccountStatus
from apps.accounts.models import OTPCode, User, UserInvitation


@pytest.mark.django_db
def test_create_user():
    """Verify custom User model creation."""
    user = User.objects.create_user(
        email="testuser@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        password="SecurePassword123!",
    )
    assert user.email == "testuser@example.com"
    assert user.username == "testuser"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.status == AccountStatus.PENDING_REGISTRATION
    assert user.email_verified is False
    assert user.check_password("SecurePassword123!") is True
    assert str(user) == "Test User (testuser@example.com)"


@pytest.mark.django_db
def test_create_superuser():
    """Verify superuser creation on custom User manager."""
    admin = User.objects.create_superuser(
        email="admin@example.com",
        username="admin",
        first_name="Admin",
        last_name="User",
        password="AdminPassword123!",
    )
    assert admin.email == "admin@example.com"
    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.status == AccountStatus.ACTIVE
    assert admin.email_verified is True


@pytest.mark.django_db
def test_user_lockout():
    """Verify account locking functionality."""
    user = User.objects.create_user(
        email="testuser@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
    )
    assert user.is_locked() is False

    user.locked_until = timezone.now() + timedelta(minutes=10)
    user.save()
    assert user.is_locked() is True

    user.locked_until = timezone.now() - timedelta(minutes=1)
    user.save()
    assert user.is_locked() is False


@pytest.mark.django_db
def test_invitation_validity():
    """Verify invitation is_valid logic."""
    inv = UserInvitation.objects.create(
        email="invitee@example.com",
        expires_at=timezone.now() + timedelta(days=1),
    )
    assert inv.is_valid() is True

    # Check status expired
    inv.status = UserInvitation.InvitationStatus.EXPIRED
    inv.save()
    assert inv.is_valid() is False

    # Check expires_at in past
    inv.status = UserInvitation.InvitationStatus.PENDING
    inv.expires_at = timezone.now() - timedelta(minutes=1)
    inv.save()
    assert inv.is_valid() is False


@pytest.mark.django_db
def test_otp_code_validity():
    """Verify OTP validity check."""
    otp = OTPCode.objects.create(
        email="test@example.com",
        code="123456",
        purpose=OTPCode.OTPPurpose.EMAIL_VERIFICATION,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    assert otp.is_valid() is True

    otp.is_verified = True
    otp.save()
    assert otp.is_valid() is False
