from csp.contrib.rate_limiting import RateLimitedCSPMiddleware
from maykin_common.csp.middleware import DatabaseDirectivesMixin


class CSPMiddleware(DatabaseDirectivesMixin, RateLimitedCSPMiddleware):
    """
    Rate limited CSP middleware which adds the directives managed in the admin.
    """


class SkipStaffCSPMiddleware:
    """
    middleware to skip CSP if authenticated and staff by simulating the django-csp '@csp_exempt' decorator
    https://django-csp.readthedocs.io/en/latest/decorators.html#csp-exempt
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated and request.user.is_staff:
            response._csp_exempt = True
            response._csp_exempt_ro = True
        return response
