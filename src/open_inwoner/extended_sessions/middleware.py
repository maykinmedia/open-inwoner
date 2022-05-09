from datetime import timedelta

from django.conf import settings


SESSION_EXPIRES_IN_HEADER = "X-Session-Expires-In"


class SessionTimeoutMiddleware:
    """
    Allows us to set the expiry time of the session based on what
    is configured in our GlobalConfiguration
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timeout = (
            settings.ADMIN_SESSION_COOKIE_AGE
            if request.user.is_staff
            else settings.SESSION_COOKIE_AGE
        )
        # https://docs.djangoproject.com/en/2.2/topics/http/sessions/#django.contrib.sessions.backends.base.SessionBase.set_expiry
        print(request.session)
        request.session.set_expiry(timeout)
        response = self.get_response(request)
        response[SESSION_EXPIRES_IN_HEADER] = timeout
        return response
