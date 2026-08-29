from django.shortcuts import render


def home(request):
    return render(request, "core/home.html")


def about(request):
    return render(request, "core/about.html")


# ============================================
# UI Placeholder Views (Phase 05)
# These are temporary views for rendering the
# design system templates. They will be replaced
# by real authentication views in Phase 06.
# ============================================


def login_view(request):
    """Placeholder login page (UI only)."""
    return render(request, "auth/login.html")
