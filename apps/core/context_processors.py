def branding_context(request):
    """
    Provides global branding context variables for the SITADC Youth Hub.
    """
    return {
        "organization_name": "SITADC Youth Organization",
        "organization_logo": "images/app_logo.png",
        "homepage_background": "images/background.png",
    }


def dashboard_preferences_context(request):
    """
    Provides user dashboard preferences to all templates.
    """
    if not request.user.is_authenticated:
        return {}

    try:
        from apps.dashboard.models import UserDashboardPreference
        pref, _ = UserDashboardPreference.objects.get_or_create(user=request.user)
        return {
            "dashboard_pref": pref,
            "dashboard_theme": pref.theme,
            "dashboard_chart_style": pref.preferred_chart_style,
            "dashboard_reporting_period": pref.default_reporting_period,
        }
    except Exception:
        return {}
