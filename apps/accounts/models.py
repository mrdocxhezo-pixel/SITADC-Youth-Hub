import uuid
from typing import ClassVar

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, UUIDModel

from .constants import AccountStatus
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, UUIDModel, TimeStampedModel):
    """
    Custom User Model for SITADC Youth Hub using UUID primary key and Email login.
    """

    username = models.CharField(
        _("Username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
    )
    email = models.EmailField(_("Email address"), unique=True)
    first_name = models.CharField(_("First name"), max_length=150)
    last_name = models.CharField(_("Last name"), max_length=150)
    phone_number = models.CharField(_("Phone number"), max_length=20, blank=True)

    status = models.CharField(
        _("Account status"),
        max_length=50,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING_REGISTRATION,
        db_index=True,
    )

    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_staff = models.BooleanField(
        _("Staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )

    email_verified = models.BooleanField(_("Email verified"), default=False)
    phone_verified = models.BooleanField(_("Phone verified"), default=False)

    password_updated_at = models.DateTimeField(
        _("Password updated at"), null=True, blank=True
    )
    login_attempts = models.IntegerField(_("Failed login attempts"), default=0)
    locked_until = models.DateTimeField(_("Locked until"), null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())


class UserProfile(UUIDModel, TimeStampedModel):
    """
    Profile information for SITADC Youth Hub users.
    Stays separate from user credentials.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("User"),
    )
    profile_photo = models.ImageField(
        _("Profile photo"), upload_to="profiles/", null=True, blank=True
    )
    preferred_display_name = models.CharField(
        _("Preferred display name"), max_length=150, blank=True
    )
    gender = models.CharField(_("Gender"), max_length=20, blank=True)
    date_of_birth = models.DateField(_("Date of birth"), null=True, blank=True)
    alternative_contact_number = models.CharField(
        _("Alternative contact number"), max_length=20, blank=True
    )
    residential_address = models.TextField(_("Residential address"), blank=True)
    province = models.CharField(_("Province"), max_length=100, blank=True)
    district = models.CharField(_("District"), max_length=100, blank=True)
    biography = models.TextField(_("Biography"), blank=True)
    preferred_language = models.CharField(
        _("Preferred language"), max_length=10, default="en", blank=True
    )
    time_zone = models.CharField(
        _("Time zone"), max_length=100, default="Africa/Lusaka", blank=True
    )
    notification_preferences = models.JSONField(
        _("Notification preferences"), default=dict, blank=True
    )

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return f"Profile of {self.user.email}"


class UserInvitation(UUIDModel, TimeStampedModel):
    """
    Model tracking registration invitation tokens.
    Public registration is disabled.
    """

    class InvitationStatus(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        ACCEPTED = "ACCEPTED", _("Accepted")
        EXPIRED = "EXPIRED", _("Expired")
        REVOKED = "REVOKED", _("Revoked")

    email = models.EmailField(_("Recipient email"))
    token = models.UUIDField(
        _("Invitation token"), default=uuid.uuid4, unique=True, editable=False
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )
    expires_at = models.DateTimeField(_("Expires at"))
    accepted_at = models.DateTimeField(_("Accepted at"), null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
        verbose_name=_("Created by"),
    )

    class Meta:
        verbose_name = _("User Invitation")
        verbose_name_plural = _("User Invitations")
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self):
        return f"Invitation for {self.email} ({self.status})"

    def is_valid(self):
        return (
            self.status == self.InvitationStatus.PENDING
            and self.expires_at > timezone.now()
        )


class UserSession(UUIDModel, TimeStampedModel):
    """
    Model for tracking active user devices/sessions and supporting session management.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name=_("User"),
    )
    session_key = models.CharField(_("Session key"), max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)
    user_agent = models.TextField(_("User agent"), blank=True)
    last_activity = models.DateTimeField(_("Last activity"), default=timezone.now)
    is_active = models.BooleanField(_("Is active"), default=True)

    class Meta:
        verbose_name = _("User Session")
        verbose_name_plural = _("User Sessions")
        ordering: ClassVar[list[str]] = ["-last_activity"]

    def __str__(self):
        return f"Session {self.session_key} for {self.user.email}"


class OTPCode(UUIDModel, TimeStampedModel):
    """
    OTP codes for email verification, password reset, or MFA readiness.
    """

    class OTPPurpose(models.TextChoices):
        EMAIL_VERIFICATION = "EMAIL_VERIFICATION", _("Email Verification")
        PASSWORD_RESET = "PASSWORD_RESET", _("Password Reset")
        LOGIN = "LOGIN", _("Login")
        MFA = "MFA", _("Multi-Factor Authentication")

    email = models.EmailField(_("Email address"))
    code = models.CharField(_("OTP Code"), max_length=6)
    purpose = models.CharField(_("Purpose"), max_length=50, choices=OTPPurpose.choices)
    expires_at = models.DateTimeField(_("Expires at"))
    is_verified = models.BooleanField(_("Is verified"), default=False)

    class Meta:
        verbose_name = _("OTP Code")
        verbose_name_plural = _("OTP Codes")
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self):
        return f"{self.purpose} OTP for {self.email}"

    def is_valid(self):
        return not self.is_verified and self.expires_at > timezone.now()
