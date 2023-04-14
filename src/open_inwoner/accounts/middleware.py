import logging

from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch, reverse

logger = logging.getLogger(__name__)


class NecessaryFieldsMiddleware:
    """
    Redirect the user to a view to fill in necessary fields
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            necessary_fields_url = reverse("profile:registration_necessary")
        except NoReverseMatch:
            logger.warning(
                "cannot reverse 'profile:registration_necessary' URL: apphook not active"
            )
            return self.get_response(request)

        user = request.user
        if user.is_authenticated:

            # If the user is currently not editing their information, but it is required
            # redirect to that view.

            # DigiD can be disabled, in which case the digid app isn't available
            digid_logout = "/digid/logout/"
            try:
                digid_logout = reverse("digid:logout")
            except:  # nosec
                pass
            if (
                not request.path.startswith(
                    (necessary_fields_url, reverse("logout"), digid_logout)
                )
                and request.user.require_necessary_fields()
            ):
                return HttpResponseRedirect(necessary_fields_url)

        return self.get_response(request)
