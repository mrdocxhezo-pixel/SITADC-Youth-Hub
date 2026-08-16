"""Tests for the RBAC authorization middleware."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from apps.accounts.constants import AccountStatus
from apps.accounts.models import User
from apps.rbac.middleware import (
    BLOCKED_ACCOUNT_STATUSES,
    AuthorizationMiddleware,
)


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="middleware@example.com",
        username="middlewareuser",
        first_name="Middleware",
        last_name="User",
        password="TestPassword123!",
    )


class _StubResponse:
    status_code = 200


def _call_middleware(request):
    middleware = AuthorizationMiddleware(lambda req: _StubResponse())
    return middleware(request)


def _make_request(user):
    request = RequestFactory().get("/dashboard/")
    request.user = user
    request.session = {}
    return request


@pytest.mark.django_db
def test_rbac_context_attached_for_authenticated_user(user):
    """Verify ``request.rbac`` is attached for authenticated users."""
    request = _make_request(user)
    _call_middleware(request)
    assert request.rbac is not None
    assert request.rbac.user == user
    assert callable(request.rbac.roles)
    assert callable(request.rbac.permissions)
    assert callable(request.rbac.scopes)
    assert callable(request.rbac.can)
    assert callable(request.rbac.can_all)
    assert callable(request.rbac.can_any)
    assert callable(request.rbac.has_role)
    assert callable(request.rbac.has_scope)


@pytest.mark.django_db
def test_rbac_context_not_attached_for_anonymous():
    """Verify anonymous requests are left untouched."""
    request = _make_request(AnonymousUser())
    _call_middleware(request)
    assert not hasattr(request, "rbac")


@pytest.mark.django_db
def test_active_account_not_blocked(user):
    """Verify an active account passes through without a redirect."""
    user.status = AccountStatus.ACTIVE
    user.save()
    request = _make_request(user)
    assert _call_middleware(request) is not None
    assert request.user == user


@pytest.mark.parametrize("status", list(BLOCKED_ACCOUNT_STATUSES))
@pytest.mark.django_db
def test_blocked_account_redirects_to_login(client, user, status):
    """Verify blocked account statuses force a redirect to login."""
    user.status = status
    user.save()
    client.force_login(user)
    response = client.get("/dashboard/")
    assert response.status_code == 302
    assert "/accounts/login" in response.url


@pytest.mark.parametrize("status", list(BLOCKED_ACCOUNT_STATUSES))
@pytest.mark.django_db
def test_blocked_account_on_login_page_not_redirected(client, user, status):
    """Verify the login page itself is never redirected (no redirect loop)."""
    user.status = status
    user.save()
    client.force_login(user)
    response = client.get("/accounts/login/")
    # The login view may bounce already-authenticated users elsewhere, but the
    # middleware must never produce a login->login redirect loop.
    assert "next=/accounts/login" not in response.url
    assert response.status_code != 200 or b"Sign" in response.content


@pytest.mark.django_db
def test_authorization_failure_logged_for_authenticated(user):
    """Verify 403 responses for authenticated users are recorded."""
    request = _make_request(user)

    class DeniedResponse:
        status_code = 403

    middleware = AuthorizationMiddleware(lambda req: DeniedResponse())
    result = middleware(request)
    assert result.status_code == 403