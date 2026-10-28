from csp.contrib.rate_limiting import RateLimitedCSPMiddleware
from maykin_common.csp.middleware import DatabaseDirectivesMixin


class CSPMiddleware(DatabaseDirectivesMixin, RateLimitedCSPMiddleware):
    """
    Rate limited CSP middleware which adds the directives managed in the admin.
    """
