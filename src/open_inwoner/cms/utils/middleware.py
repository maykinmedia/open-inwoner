from django.http import HttpResponseRedirect

from cms.toolbar.utils import get_toolbar_from_request

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


class DropToolbarMiddleware:
    """
    Hide the django-cms toolbar if the staff user is not 2FA verified

    Needed because only the admin has forced OTP,
      so the inline editing iframes of django-cms could be accessed but then show a confusing 2FA flow
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self.force_disable_toolbar(request):
            request.session["cms_edit"] = False
            request.session["cms_preview"] = False
            request.session["cms_toolbar_disabled"] = True

            toolbar = get_toolbar_from_request(request)
            toolbar.show_toolbar = False

        response = self.get_response(request)
        return response

    def force_disable_toolbar(self, request):
        if not request.user.is_staff or not request.user.is_verified():
            return True
        else:
            return False
