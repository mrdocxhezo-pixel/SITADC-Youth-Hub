import uuid


class RequestIDMiddleware:
    """
    Middleware that attaches a unique request ID to each request.
    This request ID can be used for logging and tracking requests.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = str(uuid.uuid4())
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        return response


class CurrentUserMiddleware:
    """
    Middleware that extracts the current user and makes it globally available
    or attaches it to a specific context if needed.
    For now, it simply ensures request.user is accessible early
    or can be mapped to thread locals.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Additional user context logic would go here
        return self.get_response(request)


class OrganizationContextMiddleware:
    """
    Middleware for determining the current organization scope
    based on the user's session or subdomain.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Organization context logic would go here
        return self.get_response(request)


class TimezoneMiddleware:
    """
    Middleware to activate the user's specific timezone.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Timezone logic would go here
        return self.get_response(request)


class MaintenanceModeMiddleware:
    """
    Middleware to intercept requests if the application is in maintenance mode.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Maintenance logic would go here
        return self.get_response(request)


class AuditContextMiddleware:
    """
    Middleware to inject audit context (like IP, User Agent) into the request
    for downstream usage in services or models.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Audit logic would go here
        return self.get_response(request)


class SecurityHeadersMiddleware:
    """
    Middleware to add additional security headers
    not covered by Django's default SecurityMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        return response
