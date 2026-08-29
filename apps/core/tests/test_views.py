"""
Tests for core app views.

Uses RequestFactory instead of Django test Client to avoid the Python 3.14
incompatibility with Django's template context copy() in instrumented_test_render.
The issue is an upstream Python 3.14 alpha bug — copy(super()) returns a
plain object, and assigning to dicts fails. Pages work correctly at runtime.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestViews:
    def test_home_page_status(self, client):
        response = client.get(reverse("core:home"))
        assert response.status_code == 200

    def test_home_page_content(self, client):
        response = client.get(reverse("core:home"))
        assert b"SITADC Youth Hub" in response.content

    def test_about_page_status(self, client):
        response = client.get(reverse("core:about"))
        assert response.status_code == 200

    def test_about_page_content(self, client):
        response = client.get(reverse("core:about"))
        assert (
            b"Sustainable Initiatives Through Transformative Actions"
            in response.content
        )


@pytest.mark.django_db
class TestPhase05PlaceholderViews:
    """Tests for Phase 05 UI placeholder views (login, password reset, dashboard)."""

    def test_login_view_status(self, client):
        response = client.get(reverse("core:login"))
        assert response.status_code == 200

    def test_login_view_contains_form(self, client):
        response = client.get(reverse("core:login"))
        assert b"Sign in" in response.content
        assert b"id_username" in response.content
        assert b"id_password" in response.content

    def test_password_reset_view_status(self, client):
        response = client.get(reverse("core:password_reset"))
        assert response.status_code == 200

    def test_password_reset_view_contains_email_field(self, client):
        response = client.get(reverse("core:password_reset"))
        assert b"id_email" in response.content

    def test_password_reset_confirm_redirects_without_verification(self, client):
        response = client.get(
            reverse("core:password_reset_confirm", kwargs={"email": "test@example.com"})
        )
        assert response.status_code == 302
        assert response.url == reverse("core:password_reset")

    def test_password_reset_confirm_requires_prior_otp_verification(self, client):
        session = client.session
        session["reset_email_verified"] = "test@example.com"
        session.save()
        response = client.get(
            reverse("core:password_reset_confirm", kwargs={"email": "test@example.com"})
        )
        assert response.status_code == 200

    def test_dashboard_requires_login(self, client):
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 302
        assert response.url == (
            f"{reverse('core:login')}?next={reverse('dashboard:home')}"
        )

    def test_dashboard_contains_nav_for_superuser(
        self, client, django_user_model
    ):
        user = django_user_model.objects.create_superuser(
            email="dashboard-admin@example.com",
            username="dashboard-admin",
            first_name="Dashboard",
            last_name="Admin",
            password="Password123!@",
        )
        client.force_login(user)
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 200
        assert b"dashboard-sidebar" in response.content
        assert b"dashboard-topbar" in response.content
        assert reverse("stakeholders:dashboard").encode() in response.content
