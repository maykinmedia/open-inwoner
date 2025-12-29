from cms.toolbar.utils import get_toolbar_from_request


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
        return (not request.user.is_staff) or (not request.user.is_verified())
