from django.contrib.auth.decorators import login_required
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


def password_reset_view(request):
    """Placeholder forgot password page (UI only)."""
    return render(request, "auth/forgot_password.html")


def password_reset_confirm_view(request):
    """Placeholder reset password page (UI only)."""
    return render(request, "auth/reset_password.html")


@login_required
def dashboard_preview(request):
    """Placeholder dashboard shell for layout testing (UI only)."""
    return render(request, "core/dashboard_preview.html")
