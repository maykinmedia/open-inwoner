from django.http import HttpResponseRedirect

from open_inwoner.configurations.models import SiteConfiguration


class AnonymousHomePageRedirectMiddleware:
    """
    Redirect the user from home page to a desired page provided via the
    SiteConfiguration singleton. The validity of the path or url is being
    checked in the admin form.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not request.user.is_authenticated and (
            request.path == "/" or request.path == "/nl/"
        ):
            config = SiteConfiguration.get_solo()
            if config.redirect_to:
                return HttpResponseRedirect(config.redirect_to)

        return response
