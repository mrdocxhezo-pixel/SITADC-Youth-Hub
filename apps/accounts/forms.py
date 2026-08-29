from typing import ClassVar

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.locations.models import District, Province

from .models import UserProfile
from .validators import validate_password_strength


class LoginForm(forms.Form):
    """Form for user authentication."""

    username = forms.EmailField(
        label=_("Email address"),
        widget=forms.EmailInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Enter your email address",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Enter your password",
            }
        ),
    )
    remember = forms.BooleanField(
        label=_("Keep me signed in"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class RegisterForm(forms.Form):
    """Form for registering a new user account via an invitation."""

    username = forms.CharField(
        label=_("Username"),
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter username",
            }
        ),
    )
    first_name = forms.CharField(
        label=_("First name"),
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "First name",
            }
        ),
    )
    last_name = forms.CharField(
        label=_("Last name"),
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last name",
            }
        ),
    )
    phone_number = forms.CharField(
        label=_("Phone number"),
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Phone number",
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter strong password",
            }
        ),
    )
    confirm_password = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm password",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean() or {}
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", _("Passwords do not match."))

        if password:
            try:
                validate_password_strength(password)
            except ValidationError as e:
                self.add_error("password", e)

        return cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating personal profile details."""

    first_name = forms.CharField(
        label=_("First name"),
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label=_("Last name"),
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    phone_number = forms.CharField(
        label=_("Phone number"),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    province_location = forms.ModelChoiceField(
        label=_("Province / Region"),
        required=False,
        queryset=Province.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label=_("Select Province / Region"),
    )
    district_location = forms.ModelChoiceField(
        label=_("District"),
        required=False,
        queryset=District.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label=_("Select District"),
    )

    class Meta:
        model = UserProfile
        fields: ClassVar[list[str]] = [
            "preferred_display_name",
            "gender",
            "date_of_birth",
            "alternative_contact_number",
            "residential_address",
            "province",
            "district",
            "province_location",
            "district_location",
            "biography",
            "preferred_language",
            "time_zone",
            "profile_photo",
        ]
        widgets: ClassVar[dict] = {
            "preferred_display_name": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "alternative_contact_number": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "residential_address": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "province": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "district": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "biography": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "preferred_language": forms.TextInput(attrs={"class": "form-control"}),
            "time_zone": forms.TextInput(attrs={"class": "form-control"}),
            "profile_photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["phone_number"].initial = self.instance.user.phone_number

    def clean(self):
        cleaned = super().clean()
        province = cleaned.get("province_location")
        district = cleaned.get("district_location")
        if district and province and district.province_id != province.pk:
            self.add_error(
                "district_location",
                _("The selected district does not belong to the selected province."),
            )
        return cleaned

    def save(self, commit=True):
        profile = super().save(commit=False)
        # Mirror the structured FK values into the legacy text fields for
        # backward compatibility and search.
        province = self.cleaned_data.get("province_location")
        district = self.cleaned_data.get("district_location")
        if province:
            profile.province = province.name
        if district:
            profile.district = district.name
        if commit:
            profile.save()
            user = profile.user
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.phone_number = self.cleaned_data["phone_number"]
            user.save()
        return profile


class PasswordChangeForm(forms.Form):
    """Form for changing password from settings."""

    current_password = forms.CharField(
        label=_("Current Password"),
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    confirm_new_password = forms.CharField(
        label=_("Confirm New Password"),
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean() or {}
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        if (
            new_password
            and confirm_new_password
            and new_password != confirm_new_password
        ):
            self.add_error("confirm_new_password", _("Passwords do not match."))

        if new_password:
            try:
                validate_password_strength(new_password)
            except ValidationError as e:
                self.add_error("new_password", e)

        return cleaned_data


class PasswordResetRequestForm(forms.Form):
    """Form to request password reset link/OTP."""

    email = forms.EmailField(
        label=_("Email Address"),
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Enter your email"}
        ),
    )


class PasswordResetConfirmForm(forms.Form):
    """Form to enter new password after verifying token/OTP."""

    new_password = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    confirm_new_password = forms.CharField(
        label=_("Confirm New Password"),
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean() or {}
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        if (
            new_password
            and confirm_new_password
            and new_password != confirm_new_password
        ):
            self.add_error("confirm_new_password", _("Passwords do not match."))

        if new_password:
            try:
                validate_password_strength(new_password)
            except ValidationError as e:
                self.add_error("new_password", e)

        return cleaned_data


class OTPVerificationForm(forms.Form):
    """Form for verifying 6-digit OTP code."""

    code = forms.CharField(
        label=_("Verification Code"),
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg text-center letter-spacing-lg",
                "placeholder": "• • • • • •",
                "maxlength": "6",
                "autofocus": True,
            }
        ),
    )
