"""Forms for dashboard personalization."""

from django import forms

from .models import UserDashboardPreference


class DashboardPreferencesForm(forms.ModelForm):
    """User-level look-and-feel preferences for the dashboard."""

    class Meta:
        model = UserDashboardPreference
        fields = ["theme", "preferred_chart_style", "default_reporting_period"]
        widgets = {
            "theme": forms.Select(attrs={"class": "form-select"}),
            "preferred_chart_style": forms.Select(attrs={"class": "form-select"}),
            "default_reporting_period": forms.Select(attrs={"class": "form-select"}),
        }
