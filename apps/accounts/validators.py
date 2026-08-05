import re

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def validate_password_strength(value: str):
    """
    Validates that a password:
    - Is at least 12 characters long.
    - Contains at least one uppercase letter.
    - Contains at least one lowercase letter.
    - Contains at least one digit.
    - Contains at least one special character.
    """
    if len(value) < 12:
        raise ValidationError(
            _("Password must be at least 12 characters long."),
            code="password_too_short",
        )
    if not re.search(r"[A-Z]", value):
        raise ValidationError(
            _("Password must contain at least one uppercase letter."),
            code="password_no_uppercase",
        )
    if not re.search(r"[a-z]", value):
        raise ValidationError(
            _("Password must contain at least one lowercase letter."),
            code="password_no_lowercase",
        )
    if not re.search(r"\d", value):
        raise ValidationError(
            _("Password must contain at least one digit."),
            code="password_no_digit",
        )
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValidationError(
            _("Password must contain at least one special character."),
            code="password_no_special",
        )


def validate_invitation_token(token_str: str):
    """
    Validates token format and checks if invitation exists and is valid.
    """
    import uuid

    from .models import UserInvitation

    try:
        token_uuid = uuid.UUID(token_str)
    except ValueError:
        raise ValidationError(
            _("Invalid token format."), code="invalid_token_format"
        ) from None

    try:
        invitation = UserInvitation.objects.get(token=token_uuid)
    except UserInvitation.DoesNotExist:
        raise ValidationError(
            _("Invitation not found."), code="invitation_not_found"
        ) from None

    if not invitation.is_valid():
        if invitation.status == UserInvitation.InvitationStatus.ACCEPTED:
            raise ValidationError(
                _("This invitation has already been accepted."),
                code="invitation_accepted",
            )
        elif invitation.expires_at <= timezone.now():
            raise ValidationError(
                _("This invitation has expired."), code="invitation_expired"
            )
        else:
            raise ValidationError(
                _("This invitation is invalid or has been revoked."),
                code="invitation_revoked",
            )
    return invitation
