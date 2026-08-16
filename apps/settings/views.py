import json
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.models import UserSession
from apps.rbac.authorization import user_has_permission
from apps.settings.forms import (
    AccessibilitySettingsForm,
    CustomPasswordChangeForm,
    IntegrationSettingsForm,
    LanguageRegionSettingsForm,
    NotificationSettingsForm,
    ProfilePhotoForm,
    ProfileUpdateForm,
    PrivacySettingsForm,
    SystemSettingsForm,
    TwoFactorSettingsForm,
    UserSettingsDefaultForm,
    UserSettingsForm,
)
from apps.settings.models import (
    IntegrationSettings,
    SystemSettings,
    UserSettings,
    UserSettingsDefault,
)


@method_decorator(login_required, name="dispatch")
class SettingsBaseView(LoginRequiredMixin, TemplateView):
    """Base view for settings pages."""

    template_name = "settings/base.html"
    section = None
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if self.permission_required and not user_has_permission(request.user, self.permission_required):
            messages.error(request, _("You do not have permission to access this page."))
            return redirect("settings:settings_dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings_section"] = self.section
        context["user_settings"] = self.get_user_settings()
        context["system_settings"] = SystemSettings.load() if user_has_permission(self.request.user, "administration.manage") else None
        return context

    def get_user_settings(self):
        return UserSettings.objects.get_or_create(user=self.request.user)[0]


@method_decorator(login_required, name="dispatch")
class SettingsDashboardView(SettingsBaseView):
    """Settings dashboard/overview page."""

    template_name = "settings/dashboard.html"
    section = "dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_settings = self.get_user_settings()

        # Get active sessions
        active_sessions = UserSession.objects.filter(user=user, is_active=True).order_by("-last_activity")
        current_session_key = self.request.session.session_key

        # Security status
        last_password_change = user.password_updated_at
        last_login = user.last_login

        context.update({
            "active_sessions": active_sessions,
            "current_session_key": current_session_key,
            "last_password_change": last_password_change,
            "last_login": last_login,
            "profile_completion": self.calculate_profile_completion(user, user_settings),
            "security_score": self.calculate_security_score(user, user_settings),
        })
        return context

    def calculate_profile_completion(self, user, settings):
        fields = [
            user.first_name,
            user.last_name,
            user.phone_number,
            settings.profile_photo if hasattr(settings, 'profile_photo') else None,
        ]
        completed = sum(1 for f in fields if f)
        return int((completed / len(fields)) * 100)

    def calculate_security_score(self, user, settings):
        score = 0
        if user.password_updated_at:
            score += 20
        if user.email_verified:
            score += 20
        if user.phone_verified:
            score += 10
        # Check for 2FA
        if hasattr(user, 'otpdevice_set') and user.otpdevice_set.filter(confirmed=True).exists():
            score += 30
        return min(score, 100)


@method_decorator(login_required, name="dispatch")
class AccountSettingsView(SettingsBaseView):
    """Account settings page."""

    template_name = "settings/account.html"
    section = "account"

    def get(self, request):
        user_settings = self.get_user_settings()
        profile_form = ProfileUpdateForm(instance=request.user, user=request.user)
        photo_form = ProfilePhotoForm()
        return render(request, self.template_name, {
            "profile_form": profile_form,
            "photo_form": photo_form,
            "user_settings": user_settings,
        })

    def post(self, request):
        user_settings = self.get_user_settings()
        action = request.POST.get("action")

        if action == "update_profile":
            profile_form = ProfileUpdateForm(request.POST, instance=request.user, user=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, _("Profile updated successfully."))
                return redirect("settings:account")
        elif action == "update_photo":
            photo_form = ProfilePhotoForm(request.POST, request.FILES)
            if photo_form.is_valid():
                # Handle photo upload via user profile
                profile = request.user.profile
                profile.profile_photo = photo_form.cleaned_data["profile_photo"]
                profile.save()
                messages.success(request, _("Profile photo updated successfully."))
                return redirect("settings:account")

        profile_form = ProfileUpdateForm(request.POST, instance=request.user, user=request.user)
        photo_form = ProfilePhotoForm()
        return render(request, self.template_name, {
            "profile_form": profile_form,
            "photo_form": photo_form,
            "user_settings": user_settings,
        })


@method_decorator(login_required, name="dispatch")
class AppearanceSettingsView(SettingsBaseView):
    """Appearance & personalization settings."""

    template_name = "settings/appearance.html"
    section = "appearance"

    def get(self, request):
        user_settings = self.get_user_settings()
        form = UserSettingsForm(instance=user_settings)
        return render(request, self.template_name, {"form": form, "user_settings": user_settings})

    def post(self, request):
        user_settings = self.get_user_settings()
        form = UserSettingsForm(request.POST, instance=user_settings)
        if form.is_valid():
            form.save()
            messages.success(request, _("Appearance settings saved successfully."))
            return redirect("settings:appearance")
        return render(request, self.template_name, {"form": form, "user_settings": user_settings})


@method_decorator(login_required, name="dispatch")
class NotificationSettingsView(SettingsBaseView):
    """Notification settings page."""

    template_name = "settings/notifications.html"
    section = "notifications"

    def get(self, request):
        user_settings = self.get_user_settings()
        form = NotificationSettingsForm(instance=user_settings)
        return render(request, self.template_name, {"form": form, "user_settings": user_settings})

    def post(self, request):
        user_settings = self.get_user_settings()
        form = NotificationSettingsForm(request.POST, instance=user_settings)
        if form.is_valid():
            form.save()
            messages.success(request, _("Notification settings saved successfully."))
            return redirect("settings:notifications")
        return render(request, self.template_name, {"form": form, "user_settings": user_settings})


@method_decorator(login_required, name="dispatch")
class SecuritySettingsView(SettingsBaseView):
    """Security settings page."""

    template_name = "settings/security.html"
    section = "security"

    def get(self, request):
        user_settings = self.get_user_settings()
        password_form = CustomPasswordChangeForm(user=request.user)
        two_factor_form = TwoFactorSettingsForm()
        return render(request, self.template_name, {
            "password_form": password_form,
            "two_factor_form": two_factor_form,
            "user_settings": user_settings,
        })

    def post(self, request):
        user_settings = self.get_user_settings()
        action = request.POST.get("action")

        if action == "change_password":
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, _("Password changed successfully."))
                return redirect("settings:security")
        elif action == "update_2fa":
            two_factor_form = TwoFactorSettingsForm(request.POST)
            if two_factor_form.is_valid():
                # Handle 2FA settings
                messages.success(request, _("Two-factor authentication settings updated."))
                return redirect("settings:security")

        password_form = CustomPasswordChangeForm(user=request.user)
        two_factor_form = TwoFactorSettingsForm()
        return render(request, self.template_name, {
            "password_form": password_form,
            "two_factor_form": two_factor_form,
            "user_settings": user_settings,
        })


@method_decorator(login_required, name="dispatch")
class PrivacySettingsView(SettingsBaseView):
    """Privacy settings page."""

    template_name = "settings/privacy.html"
    section = "privacy"

    def get(self, request):
        user_settings = self.get_user_settings()
        form = PrivacySettingsForm(instance=user_settings)
        return render(request, self.template_name, {"form": form, "user_settings": user_settings})

    def post(self, request):
        user_settings = self.get_user_settings()
        form = PrivacySettingsForm(request.POST, instance=user_settings)
        if form.is_valid():
            form.save()
            messages.success(request, _("Privacy settings saved successfully."))
            return redirect("settings:privacy")
        return render(request, self.template_name, {"form": form, "user_settings": user_settings})


@method_decorator(login_required, name="dispatch")
class SessionsSettingsView(SettingsBaseView):
    """Sessions & devices settings page."""

    template_name = "settings/sessions.html"
    section = "sessions"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        active_sessions = UserSession.objects.filter(user=user, is_active=True).order_by("-last_activity")
        current_session_key = self.request.session.session_key

        context.update({
            "active_sessions": active_sessions,
            "current_session_key": current_session_key,
        })
        return context

    def post(self, request):
        action = request.POST.get("action")
        session_id = request.POST.get("session_id")

        if action == "terminate" and session_id:
            session = get_object_or_404(UserSession, id=session_id, user=request.user)
            if session.session_key != request.session.session_key:
                session.is_active = False
                session.save()
                messages.success(request, _("Session terminated successfully."))
            else:
                messages.error(request, _("Cannot terminate current session."))
        elif action == "terminate_all":
            UserSession.objects.filter(user=request.user, is_active=True).exclude(
                session_key=request.session.session_key
            ).update(is_active=False)
            messages.success(request, _("All other sessions terminated successfully."))

        return redirect("settings:sessions")


@method_decorator(login_required, name="dispatch")
class LanguageRegionSettingsView(SettingsBaseView):
    """Language, region & time settings page."""

    template_name = "settings/language_region.html"
    section = "language_region"

    def get(self, request):
        user_settings = self.get_user_settings()
        form = LanguageRegionSettingsForm(instance=user_settings)
        return render(request, self.template_name, {"form": form, "user_settings": user_settings})

    def post(self, request):
        user_settings = self.get_user_settings()
        form = LanguageRegionSettingsForm(request.POST, instance=user_settings)
        if form.is_valid():
            form.save()
            messages.success(request, _("Language & region settings saved successfully."))
            return redirect("settings:language_region")
        return render(request, self.template_name, {"form": form, "user_settings": user_settings})


@method_decorator(login_required, name="dispatch")
class AccessibilitySettingsView(SettingsBaseView):
    """Accessibility settings page."""

    template_name = "settings/accessibility.html"
    section = "accessibility"

    def get(self, request):
        user_settings = self.get_user_settings()
        form = AccessibilitySettingsForm(instance=user_settings)
        return render(request, self.template_name, {"form": form, "user_settings": user_settings})

    def post(self, request):
        user_settings = self.get_user_settings()
        form = AccessibilitySettingsForm(request.POST, instance=user_settings)
        if form.is_valid():
            form.save()
            messages.success(request, _("Accessibility settings saved successfully."))
            return redirect("settings:accessibility")
        return render(request, self.template_name, {"form": form, "user_settings": user_settings})


# Admin-only views
@method_decorator(login_required, name="dispatch")
class OrganizationSettingsView(SettingsBaseView):
    """Organization settings (admin only)."""

    template_name = "settings/organization.html"
    section = "organization"
    permission_required = "organizations.manage"

    def get(self, request):
        # Implementation for organization settings
        return render(request, self.template_name, {})


@method_decorator(login_required, name="dispatch")
class UserRoleSettingsView(SettingsBaseView):
    """User & role settings (admin only)."""

    template_name = "settings/users_roles.html"
    section = "users_roles"
    permission_required = "administration.manage"

    def get(self, request):
        return render(request, self.template_name, {})


@method_decorator(login_required, name="dispatch")
class ReportingSettingsView(SettingsBaseView):
    """Reporting settings (admin only)."""

    template_name = "settings/reporting.html"
    section = "reporting"
    permission_required = "reports.manage"

    def get(self, request):
        return render(request, self.template_name, {})


@method_decorator(login_required, name="dispatch")
class SystemSettingsView(SettingsBaseView):
    """System settings (system admin only)."""

    template_name = "settings/system.html"
    section = "system"
    permission_required = "administration.manage"

    def get(self, request):
        system_settings = SystemSettings.load()
        form = SystemSettingsForm(instance=system_settings)
        return render(request, self.template_name, {"form": form, "system_settings": system_settings})

    def post(self, request):
        system_settings = SystemSettings.load()
        form = SystemSettingsForm(request.POST, instance=system_settings)
        if form.is_valid():
            form.save()
            messages.success(request, _("System settings saved successfully."))
            return redirect("settings:system")
        return render(request, self.template_name, {"form": form, "system_settings": system_settings})


@method_decorator(login_required, name="dispatch")
class DataStorageSettingsView(SettingsBaseView):
    """Data & storage settings (admin only)."""

    template_name = "settings/data_storage.html"
    section = "data_storage"
    permission_required = "administration.manage"

    def get(self, request):
        return render(request, self.template_name, {})


@method_decorator(login_required, name="dispatch")
class AuditComplianceSettingsView(SettingsBaseView):
    """Audit & compliance settings (admin only)."""

    template_name = "settings/audit.html"
    section = "audit"
    permission_required = "administration.manage"

    def get(self, request):
        return render(request, self.template_name, {})


@method_decorator(login_required, name="dispatch")
class IntegrationsSettingsView(SettingsBaseView):
    """Integrations settings (admin only)."""

    template_name = "settings/integrations.html"
    section = "integrations"
    permission_required = "administration.manage"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["integrations"] = IntegrationSettings.objects.all()
        return context


@method_decorator(login_required, name="dispatch")
class HelpSupportSettingsView(SettingsBaseView):
    """Help & support settings page."""

    template_name = "settings/help.html"
    section = "help"

    def get(self, request):
        return render(request, self.template_name, {})


# AJAX endpoints
@login_required
def settings_ajax_save(request, section):
    """AJAX endpoint for saving settings without page reload."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)

    user_settings = UserSettings.objects.get_or_create(user=request.user)[0]

    section_forms = {
        "appearance": UserSettingsForm,
        "notifications": NotificationSettingsForm,
        "privacy": PrivacySettingsForm,
        "language_region": LanguageRegionSettingsForm,
        "accessibility": AccessibilitySettingsForm,
    }

    form_class = section_forms.get(section)
    if not form_class:
        return JsonResponse({"success": False, "error": "Invalid section"}, status=400)

    form = form_class(request.POST, instance=user_settings)
    if form.is_valid():
        form.save()
        return JsonResponse({"success": True, "message": _("Settings saved successfully.")})

    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
def settings_get_section(request, section):
    """AJAX endpoint for getting section data."""
    if request.method != "GET":
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)

    # Return section-specific data
    return JsonResponse({"success": True, "data": {}})