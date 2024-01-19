import logging

from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch, reverse

from furl import furl

from open_inwoner.kvk.branches import kvk_branch_selected_done

logger = logging.getLogger(__name__)


class KvKLoginMiddleware:
    """Redirect authenticated eHerkenning users to select a company branch"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        # pass through
        if (
            not user.is_authenticated
            or not user.is_eherkenning_user
            or kvk_branch_selected_done(request.session)
        ):
            return self.get_response(request)

        # let the user logout and avoid redirect circles
        try:
            logout = reverse("logout")
            eherkenning_logout = reverse("eherkenning:logout")
            branches = reverse("kvk:branches")
        except NoReverseMatch:
            logout = "/accounts/logout/"
            eherkenning_logout = "/eherkenning/logout/"
            branches = "/kvk/branches/"

        if request.path.startswith((logout, eherkenning_logout, branches)):
            return self.get_response(request)

        # redirect to company branch choice
        redirect = furl(reverse("kvk:branches"))
        redirect.args.update(request.GET)

        return HttpResponseRedirect(redirect.url)
