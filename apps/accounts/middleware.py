import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import UserSession

logger = logging.getLogger(__name__)


class SessionTrackerMiddleware:
    """
    Middleware that tracks active user sessions by logging IP address,
    User Agent, and updating last activity timestamp in the database.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.session.session_key:
            session_key = request.session.session_key
            ip = self._get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

            # Avoid a write on every request; this keeps concurrent reads from
            # serializing on SQLite while login and session-management flows
            # continue to update the tracked session metadata.
            UserSession.objects.get_or_create(
                session_key=session_key,
                defaults={
                    "user": request.user,
                    "ip_address": ip,
                    "user_agent": user_agent,
                    "last_activity": timezone.now(),
                    "is_active": True,
                },
            )

        response = self.get_response(request)
        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class SessionTimeoutMiddleware:
    """
    Middleware that logs out a user after a period of inactivity.
    Configuration setting: `SESSION_TIMEOUT_SECONDS`
    (defaults to 900 seconds / 15 minutes).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity_str = request.session.get("last_activity")
            timeout_seconds = getattr(settings, "SESSION_TIMEOUT_SECONDS", 900)

            now = timezone.now().timestamp()

            if last_activity_str:
                elapsed = now - float(last_activity_str)
                if elapsed > timeout_seconds:
                    # Invalidate session in database
                    session_key = request.session.session_key
                    if session_key:
                        UserSession.objects.filter(session_key=session_key).update(
                            is_active=False
                        )

                    logout(request)
                    messages.warning(
                        request,
                        _(
                            "Your session has expired due to inactivity. "
                            "Please sign in again."
                        ),
                    )
                    next_path = request.path
                    from django.urls import reverse

                    login_url = (
                        reverse(settings.LOGIN_URL)
                        if not settings.LOGIN_URL.startswith("/")
                        else settings.LOGIN_URL
                    )
                    return redirect(f"{login_url}?next={next_path}")

            update_interval = getattr(
                settings, "SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS", 60
            )
            if not last_activity_str or elapsed >= update_interval:
                request.session["last_activity"] = str(now)

        response = self.get_response(request)
        return response
