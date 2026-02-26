from urllib.parse import urlencode

from django.conf import settings
from django.contrib import auth, messages
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

import structlog
from digid_eherkenning.oidc.models import BaseConfig
from digid_eherkenning.oidc.views import OIDCAuthenticationCallbackView
from mozilla_django_oidc_db.views import (
    _OIDC_ERROR_SESSION_KEY,
    AdminCallbackView,
    OIDCInit,
)

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import (
    OpenIDDigiDConfig,
    OpenIDEHerkenningConfig,
    OpenIDEIDASConfig,
)

from .auth import BlockEenmanszaakLoginMixin

logger = structlog.stdlib.get_logger(__name__)


GENERIC_DIGID_ERROR_MSG = _(
    "Inloggen bij deze organisatie is niet gelukt. Probeert u het later "
    "nog een keer. Lukt het nog steeds niet? Log in bij Mijn DigiD. "
    "Zo controleert u of uw DigiD goed werkt. Mogelijk is er een "
    "storing bij de organisatie waar u inlogt."
)
GENERIC_EHERKENNING_ERROR_MSG = _(
    "Inloggen bij deze organisatie is niet gelukt. Probeert u het later nog een keer. "
    "Lukt het nog steeds niet? Neem dan contact op met uw eHerkenning leverancier of "
    "kijk op https://www.eherkenning.nl"
)
GENERIC_EIDAS_ERROR_MSG = _(
    "Inloggen bij deze organisatie is niet gelukt. Probeert u het later nog een keer. "
    "Lukt het nog steeds niet? Neem dan contact op met uw eIDAS leverancier."
)


# XXX consider replacing this with mozilla_django_oidc_db.views.AdminLoginFailure?
# Or at least, make it consistent in the library.
class OIDCFailureView(View):
    def get(self, request):
        if _OIDC_ERROR_SESSION_KEY in self.request.session:
            message = self.request.session[_OIDC_ERROR_SESSION_KEY]
            del self.request.session[_OIDC_ERROR_SESSION_KEY]
            messages.error(request, message)
        else:
            messages.error(
                request,
                _("Something went wrong while logging in, please try again later."),
            )
        return HttpResponseRedirect(reverse("login"))


class CallbackView(OIDCAuthenticationCallbackView):
    expect_django_user = True

    failure_url = reverse_lazy("oidc-error")
    generic_error_msg = ""
    error_message_mapping: dict[tuple[str, str], str]

    def get(self, request):
        try:
            with transaction.atomic():
                response = super().get(request)
        except (IntegrityError, ValidationError):
            logger.exception(
                "Something went wrong while attempting to authenticate via OIDC",
            )
            request.session[_OIDC_ERROR_SESSION_KEY] = str(self.generic_error_msg)
            response = self.login_failure()
        else:
            # Upstream library doesn't do any error handling by default.
            if _OIDC_ERROR_SESSION_KEY in request.session:
                del request.session[_OIDC_ERROR_SESSION_KEY]

        if error_label := self._map_error(request):
            request.session[_OIDC_ERROR_SESSION_KEY] = error_label

        return response

    def _map_error(self, request) -> str:
        if not (error := request.GET.get("error")):
            return ""

        # Look up the error using both error code and description.
        error_description = request.GET.get("error_description", "")
        mapped_error = self.error_message_mapping.get((error, error_description))
        return mapped_error or str(self.generic_error_msg)


class OIDCLogoutView(View):
    config_class: type[BaseConfig] | None = None

    def get_success_url(self):
        return resolve_url(settings.LOGOUT_REDIRECT_URL)

    def get(self, request):
        if self.config_class is None:
            raise ImproperlyConfigured("Missing OIDCLogoutView config class")

        config = self.config_class.get_solo()

        id_token = request.session.get("oidc_id_token")
        if "oidc_login_next" in request.session:
            del request.session["oidc_login_next"]

        # Always destroy our session first before trying to initiate single-sign out
        auth.logout(request)

        # Try to initiate a frontchannel redirect
        if logout_endpoint := config.oidc_op_logout_endpoint:
            if settings.OIDC_FRONTEND_LOGOUT_WITH_HINTS:
                params = {
                    # The value MUST have been previously registered with the
                    # OP, either using the post_logout_redirect_uri
                    # registration parameter or via another mechanism.
                    "post_logout_redirect_uri": self.request.build_absolute_uri(
                        self.get_success_url()
                    ),
                }
                if id_token:
                    params["id_token_hint"] = id_token

                logout_endpoint += f"?{urlencode(params)}"

            return HttpResponseRedirect(logout_endpoint)

        logger.warning("No OIDC logout endpoint defined")
        return HttpResponseRedirect(self.get_success_url())


class GenericOIDCLogoutView(OIDCLogoutView):
    """
    Generic OIDC logout view that doesn't require a specific config class.
    This is used for the generic admin OIDC logout endpoint.

    Note: This view should only be used for users with login_type=oidc.
    DigiD/eHerkenning/eIDAS users should use their respective logout endpoints
    which handle SSO logout at the identity provider.
    """

    config_class = None

    def get(self, request):
        if request.user.is_authenticated and hasattr(request.user, "login_type"):
            if request.user.login_type != LoginTypeChoices.oidc:
                correct_logout_url = request.user.get_logout_url()
                logger.warning(
                    "User with non-generic OIDC login_type attempted to use generic "
                    "OIDC logout endpoint, redirecting to correct logout URL",
                    user_id=request.user.id,
                    login_type=request.user.login_type,
                    redirect_to=correct_logout_url,
                )
                return HttpResponseRedirect(correct_logout_url)

        # For generic OIDC logout, we don't have a specific config to check
        # Just log out the user and redirect
        if "oidc_login_next" in request.session:
            del request.session["oidc_login_next"]

        auth.logout(request)
        return HttpResponseRedirect(self.get_success_url())


generic_oidc_logout = GenericOIDCLogoutView.as_view()


class DigiDOIDCAuthenticationCallbackView(CallbackView):
    generic_error_msg = GENERIC_DIGID_ERROR_MSG
    error_message_mapping = {
        (
            "access_denied",
            "The user cancelled",
        ): "U heeft het inloggen met DigiD geannuleerd.",
        (
            "login_required",
            "",
        ): "Uw DigiD-sessie is verlopen. Log alstublieft opnieuw in.",
    }


class EHerkenningOIDCAuthenticationCallbackView(
    BlockEenmanszaakLoginMixin,
    CallbackView,
):
    generic_error_msg = GENERIC_EHERKENNING_ERROR_MSG
    error_message_mapping = {
        (
            "access_denied",
            "The user cancelled",
        ): "U heeft het inloggen met eHerkenning geannuleerd.",
        (
            "login_required",
            "",
        ): "Uw eHerkenning-sessie is verlopen. Log alstublieft opnieuw in.",
    }

    def get_failure_url(self):
        return settings.LOGIN_URL


digid_init = OIDCInit.as_view(config_class=OpenIDDigiDConfig)
digid_callback = DigiDOIDCAuthenticationCallbackView.as_view()
digid_logout = OIDCLogoutView.as_view(config_class=OpenIDDigiDConfig)

eherkenning_init = OIDCInit.as_view(config_class=OpenIDEHerkenningConfig)
eherkenning_callback = EHerkenningOIDCAuthenticationCallbackView.as_view()
eherkenning_logout = OIDCLogoutView.as_view(config_class=OpenIDEHerkenningConfig)


class EIDASOIDCAuthenticationCallbackView(AdminCallbackView):
    failure_url = reverse_lazy("oidc-error")
    error_message_mapping = {
        (
            "access_denied",
            "The user cancelled",
        ): "U heeft het inloggen met eIDAS geannuleerd.",
    }

    def get(self, request):
        response = super().get(request)

        # Map eIDAS-specific error codes to user-friendly messages.
        # This is a bit inelegant (we're adding error mapping after the parent's
        # error handling), but it avoids duplicating the entire error handling
        # logic from AdminCallbackView. We want consistent error handling behavior
        # with DigiD/eHerkenning views (which use CallbackView from digid_eherkenning),
        # but eIDAS uses mozilla_django_oidc_db, so we leverage AdminCallbackView's
        # existing error handling and just add custom message mapping on top.
        if error_label := self._map_error(request):
            request.session[_OIDC_ERROR_SESSION_KEY] = error_label

        return response

    def _map_error(self, request) -> str:
        if not (error := request.GET.get("error")):
            return ""

        # Look up the error using both error code and description.
        error_description = request.GET.get("error_description", "")
        mapped_error = self.error_message_mapping.get((error, error_description))
        return mapped_error or str(GENERIC_EIDAS_ERROR_MSG)


eidas_init = OIDCInit.as_view(config_class=OpenIDEIDASConfig)
eidas_callback = EIDASOIDCAuthenticationCallbackView.as_view()
eidas_logout = OIDCLogoutView.as_view(config_class=OpenIDEIDASConfig)
