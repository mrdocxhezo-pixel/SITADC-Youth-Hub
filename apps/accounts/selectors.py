from django.db.models import QuerySet
from django.utils import timezone

from .constants import AccountStatus
from .models import User, UserInvitation, UserProfile, UserSession


def get_user_by_email(email: str) -> User:
    """Retrieve user by email address."""
    return User.objects.get(email__iexact=email)


def get_active_users() -> QuerySet[User]:
    """Retrieve all active users (is_active=True and status=ACTIVE)."""
    return User.objects.filter(is_active=True, status=AccountStatus.ACTIVE)


def get_pending_invitations() -> QuerySet[UserInvitation]:
    """Retrieve all pending and non-expired invitations."""
    return UserInvitation.objects.filter(
        status=UserInvitation.InvitationStatus.PENDING,
        expires_at__gt=timezone.now(),
    )


def get_expired_invitations() -> QuerySet[UserInvitation]:
    """Retrieve all expired invitations."""
    return UserInvitation.objects.filter(
        status=UserInvitation.InvitationStatus.PENDING,
        expires_at__lte=timezone.now(),
    )


def get_locked_accounts() -> QuerySet[User]:
    """Retrieve all locked accounts."""
    return User.objects.filter(locked_until__gt=timezone.now())


def get_active_sessions_for_user(user: User) -> QuerySet[UserSession]:
    """Retrieve all active tracked sessions for a specific user."""
    return UserSession.objects.filter(user=user, is_active=True)


def get_user_profile(user: User) -> UserProfile:
    """Retrieve user profile, or raise UserProfile.DoesNotExist."""
    return UserProfile.objects.get(user=user)
