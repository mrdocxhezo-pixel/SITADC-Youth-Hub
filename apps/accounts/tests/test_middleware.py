import pytest
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.utils import timezone

from apps.accounts.middleware import SessionTimeoutMiddleware, SessionTrackerMiddleware
from apps.accounts.models import User, UserSession


def dummy_get_response(request):
    from django.http import HttpResponse

    return HttpResponse("OK")


@pytest.mark.django_db
def test_session_tracker_middleware():
    """Verify SessionTrackerMiddleware creates a missing session record."""
    user = User.objects.create_user(
        email="session@example.com",
        username="sessionuser",
        first_name="Session",
        last_name="User",
    )

    factory = RequestFactory()
    request = factory.get("/")
    request.user = user

    # Initialize session
    session_middleware = SessionMiddleware(dummy_get_response)
    session_middleware(request)
    request.session.create()

    # Track session
    tracker = SessionTrackerMiddleware(dummy_get_response)
    tracker(request)

    session_key = request.session.session_key
    assert (
        UserSession.objects.filter(session_key=session_key, user=user).exists() is True
    )

    # Existing records are read without a write on every request.
    db_session = UserSession.objects.get(session_key=session_key)
    old_activity = db_session.last_activity

    tracker(request)
    db_session.refresh_from_db()
    assert db_session.last_activity >= old_activity


@pytest.mark.django_db
def test_session_timeout_middleware(settings):
    """Verify SessionTimeoutMiddleware logs out user on timeout."""
    settings.SESSION_TIMEOUT_SECONDS = 5
    user = User.objects.create_user(
        email="timeout@example.com",
        username="timeoutuser",
        first_name="Timeout",
        last_name="User",
    )

    factory = RequestFactory()
    request = factory.get("/")
    request.user = user

    # Initialize Session & Message middlewares
    SessionMiddleware(dummy_get_response)(request)
    request.session.create()
    MessageMiddleware(dummy_get_response)(request)

    # Set last activity to 10 seconds ago (exceeding settings.SESSION_TIMEOUT_SECONDS)
    request.session["last_activity"] = str(timezone.now().timestamp() - 10)

    # Track session key in DB
    original_session_key = request.session.session_key
    UserSession.objects.create(
        user=user,
        session_key=original_session_key,
        last_activity=timezone.now(),
    )

    timeout_middleware = SessionTimeoutMiddleware(dummy_get_response)
    response = timeout_middleware(request)

    # User should be redirected to login page due to logout
    assert response.status_code == 302
    assert "login" in response["Location"]
    assert request.user.is_authenticated is False

    # Tracked session should be marked inactive in DB
    db_session = UserSession.objects.get(session_key=original_session_key)
    assert db_session.is_active is False


@pytest.mark.django_db
def test_session_timeout_throttles_activity_session_writes(settings):
    settings.SESSION_TIMEOUT_SECONDS = 900
    settings.SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS = 60
    user = User.objects.create_user(
        email="activity@example.com",
        username="activityuser",
        first_name="Activity",
        last_name="User",
    )
    factory = RequestFactory()
    request = factory.get("/")
    request.user = user
    SessionMiddleware(dummy_get_response)(request)
    request.session.create()
    recent_activity = str(timezone.now().timestamp() - 10)
    request.session["last_activity"] = recent_activity
    request.session.modified = False

    SessionTimeoutMiddleware(dummy_get_response)(request)

    assert request.session["last_activity"] == recent_activity
    assert request.session.modified is False
