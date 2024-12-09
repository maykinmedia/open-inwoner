import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import auth, messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from digid_eherkenning.oidc.models import BaseConfig
from digid_eherkenning.oidc.views import OIDCAuthenticationCallbackView
from mozilla_django_oidc_db.utils import do_op_logout
from mozilla_django_oidc_db.views import _OIDC_ERROR_SESSION_KEY, OIDCInit

from ..models import OpenIDDigiDConfig, OpenIDEHerkenningConfig
from .auth import BlockEenmanszaakLoginMixin

logger = logging.getLogger(__name__)


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
        except (IntegrityError, ValidationError) as exc:
            logger.exception(
                "Something went wrong while attempting to authenticate via OIDC",
                exc_info=exc,
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

        error_description = request.GET.get("error_description", "")

        # Look up the combination of error code and description in the mapping.
        mapped_error = self.error_message_mapping.get((error, error_description))
        return mapped_error or str(self.generic_error_msg)


class OIDCLogoutView(View):
    config_class: type[BaseConfig] | None = None

    def get_success_url(self):
        return resolve_url(settings.LOGOUT_REDIRECT_URL)

    def get(self, request):
        assert self.config_class is not None
        config = self.config_class.get_solo()

        if not (logout_endpoint := config.oidc_op_logout_endpoint):
            logger.warning("No OIDC logout endpoint defined")

        id_token = request.session.get("oidc_id_token")
        if "oidc_login_next" in request.session:
            del request.session["oidc_login_next"]

        # Always destroy our session, having obtained the OIDC artifacts from the session
        auth.logout(request)

        # Try to initiate a frontchannel redirect
        if id_token:
            if not logout_endpoint:
                # Fallback: no frontchannel flow possible
                # TODO: we can actually still redirect here, but it might be a
                # bad UX, because no id token hint.
                do_op_logout(config, id_token)
            else:
                params = {
                    "id_token_hint": id_token,
                    # The value MUST have been previously registered with the
                    # OP, either using the post_logout_redirect_uris
                    # Registration parameter or via another mechanism.
                    "post_logout_redirect_uri": self.request.build_absolute_uri(
                        self.get_success_url()
                    ),
                }
                logout_url = f"{logout_endpoint}?{urlencode(params)}"
                return HttpResponseRedirect(logout_url)

        return HttpResponseRedirect(self.get_success_url())


class DigiDOIDCAuthenticationCallbackView(CallbackView):
    generic_error_msg = GENERIC_DIGID_ERROR_MSG
    error_message_mapping = {
        ("access_denied", "The user cancelled"): (
            "Je hebt het inloggen met DigiD geannuleerd."
        )
    }


class EHerkenningOIDCAuthenticationCallbackView(
    BlockEenmanszaakLoginMixin,
    CallbackView,
):
    generic_error_msg = GENERIC_EHERKENNING_ERROR_MSG
    error_message_mapping = {
        ("access_denied", "The user cancelled"): (
            "Je hebt het inloggen met eHerkenning geannuleerd."
        )
    }

    def get_failure_url(self):
        return settings.LOGIN_URL


digid_init = OIDCInit.as_view(config_class=OpenIDDigiDConfig)
digid_callback = DigiDOIDCAuthenticationCallbackView.as_view()
digid_logout = OIDCLogoutView.as_view(config_class=OpenIDDigiDConfig)

eherkenning_init = OIDCInit.as_view(config_class=OpenIDEHerkenningConfig)
eherkenning_callback = EHerkenningOIDCAuthenticationCallbackView.as_view()
eherkenning_logout = OIDCLogoutView.as_view(config_class=OpenIDEHerkenningConfig)
