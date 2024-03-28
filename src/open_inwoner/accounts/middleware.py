import logging

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch, reverse, reverse_lazy

from furl import furl

from open_inwoner.cms.utils.page_display import profile_page_is_published
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.middleware import BaseConditionalUserRedirectMiddleware

logger = logging.getLogger(__name__)


class NecessaryFieldsMiddleware___OLD:
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

        if request.path.startswith(settings.MEDIA_URL) or request.path.startswith(
            settings.PRIVATE_MEDIA_URL
        ):
            return self.get_response(request)

        user = request.user
        if user.is_authenticated:

            # If the user is currently not editing their information, but it is required
            # redirect to that view.

            try:
                digid_logout = reverse("digid:logout")
                digid_slo_redirect = reverse("digid:slo-redirect")
            except NoReverseMatch:
                # temporary fix to make tests pass in case reverse fails
                digid_logout = "/digid/logout/"
                digid_slo_redirect = "/digid/slo/redirect/"
            if (
                not request.path.startswith(
                    (
                        necessary_fields_url,
                        reverse("logout"),
                        digid_logout,
                        digid_slo_redirect,
                        reverse("kvk:branches"),
                    )
                )
                and request.user.require_necessary_fields()
            ):
                redirect = furl(reverse("profile:registration_necessary"))
                if request.path != settings.LOGIN_REDIRECT_URL:
                    redirect.set({"next": request.path})
                return HttpResponseRedirect(redirect.url)

        return self.get_response(request)


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
            and profile_page_is_published()
            and SiteConfiguration.get_solo().email_verification_required
        )
