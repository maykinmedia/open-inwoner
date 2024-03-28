from django.urls import reverse_lazy

from open_inwoner.utils.middleware import BaseConditionalUserRedirectMiddleware


class NecessaryFieldsMiddleware(BaseConditionalUserRedirectMiddleware):
    """
    Redirect the user to a view to fill in necessary fields
    """

    redirect_url = reverse_lazy("profile:registration_necessary")

    def requires_redirect(self, request) -> bool:
        user = request.user
        return user.require_necessary_fields()  # and profile_page_is_published()
