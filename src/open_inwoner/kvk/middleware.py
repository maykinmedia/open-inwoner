from django.urls import NoReverseMatch, reverse

from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext
from open_inwoner.utils.middleware import BaseConditionalUserRedirectMiddleware


class KvKLoginMiddleware(BaseConditionalUserRedirectMiddleware):
    """Redirect authenticated eHerkenning users to select a company branch"""

    def requires_redirect(self, request):
        if not request.user.is_eherkenning_user:
            return False

        context = EHerkenningSessionContext(request)
        return not context.is_initial_branch_selection_done()

    def get_redirect_url(self, request):
        try:
            return reverse("kvk:branches")
        except NoReverseMatch:
            # TODO do we need this?
            # temporary fallback for tests
            return "/kvk/branches/"
