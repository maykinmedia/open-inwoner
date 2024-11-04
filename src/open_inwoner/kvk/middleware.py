from django.urls import NoReverseMatch, reverse

from open_inwoner.kvk.branches import kvk_branch_selected_done
from open_inwoner.utils.middleware import BaseConditionalUserRedirectMiddleware


class KvKLoginMiddleware(BaseConditionalUserRedirectMiddleware):
    """Redirect authenticated eHerkenning users to select a company branch"""

    def requires_redirect(self, request):
        user = request.user
        return user.is_eherkenning_user and not kvk_branch_selected_done(
            request.session
        )

    def get_redirect_url(self, request):
        try:
            return reverse("kvk:branches")
        except NoReverseMatch:
            # TODO do we need this?
            # temporary fallback for tests
            return "/kvk/branches/"
