from django.test import RequestFactory

from apps.core.middleware import RequestIDMiddleware, SecurityHeadersMiddleware


def dummy_get_response(request):
    from django.http import HttpResponse

    return HttpResponse("OK")


def test_request_id_middleware():
    factory = RequestFactory()
    request = factory.get("/")
    middleware = RequestIDMiddleware(dummy_get_response)

    response = middleware(request)

    assert hasattr(request, "request_id")
    assert response["X-Request-ID"] == request.request_id


def test_security_headers_middleware():
    factory = RequestFactory()
    request = factory.get("/")
    middleware = SecurityHeadersMiddleware(dummy_get_response)

    response = middleware(request)

    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["X-Frame-Options"] == "DENY"
