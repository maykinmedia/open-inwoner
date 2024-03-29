from django.urls import reverse_lazy

from open_inwoner.cms.utils.page_display import profile_page_is_published
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.middleware import BaseConditionalUserRedirectMiddleware


class NecessaryFieldsMiddleware(BaseConditionalUserRedirectMiddleware):
    """
    Redirect the user to a view to fill in necessary fields
    """

    redirect_url = reverse_lazy("profile:registration_necessary")

    def requires_redirect(self, request) -> bool:
        user = request.user
        return user.require_necessary_fields() and profile_page_is_published()


class EmailVerificationMiddleware(BaseConditionalUserRedirectMiddleware):
    """
    Redirect the user to a view to verify email
    """

    redirect_url = reverse_lazy("profile:email_verification_user")
    extra_pass_prefixes = (reverse_lazy("mail:verification"),)

    def requires_redirect(self, request) -> bool:
        user = request.user
        return (
            not user.has_verified_email()
            # and profile_page_is_published()
            and SiteConfiguration.get_solo().email_verification_required
        )
