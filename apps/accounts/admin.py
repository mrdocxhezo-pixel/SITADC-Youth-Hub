from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import OTPCode, User, UserInvitation, UserProfile, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for Custom User Model.
    """

    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "status",
        "is_staff",
        "is_active",
        "email_verified",
    )
    list_filter = ("status", "is_staff", "is_active", "email_verified")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "phone_number")},
        ),
        (
            _("Account status & Verification"),
            {"fields": ("status", "email_verified", "phone_verified")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Important dates"),
            {"fields": ("last_login", "password_updated_at", "locked_until")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "password",
                    "status",
                    "is_active",
                ),
            },
        ),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "preferred_display_name", "province", "district")
    search_fields = (
        "user__email",
        "user__username",
        "preferred_display_name",
        "province",
        "district",
    )
    list_filter = ("province", "district")


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "token",
        "status",
        "expires_at",
        "accepted_at",
        "created_by",
    )
    list_filter = ("status", "expires_at")
    search_fields = ("email", "token")
    readonly_fields = ("token",)


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "session_key", "ip_address", "last_activity", "is_active")
    list_filter = ("is_active", "last_activity")
    search_fields = ("user__email", "session_key", "ip_address")
    readonly_fields = ("session_key",)


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "code", "purpose", "expires_at", "is_verified")
    list_filter = ("purpose", "is_verified", "expires_at")
    search_fields = ("email", "code")
