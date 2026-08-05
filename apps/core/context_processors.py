def branding_context(request):
    """
    Provides global branding context variables for the SITADC Youth Hub.
    """
    return {
        "organization_name": "SITADC Youth Organization",
        "organization_logo": "images/app_logo.png",
        "homepage_background": "images/background.png",
    }
