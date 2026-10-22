from django.conf import settings


class ReportingEndpointsMiddleware:
    """
    Declare the Reporting API endpoint as the "default" group, so browsers deliver
    reports there, e.g. Permissions Policy violations, which go to the "default"
    group unless a policy directive sets `report-to`.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if settings.REPORTING_API_ENABLED:
            # relative URLs are resolved against the URL of the response
            response.headers.setdefault(
                "Reporting-Endpoints", f'default="{settings.REPORTING_API_URI}"'
            )

        return response
