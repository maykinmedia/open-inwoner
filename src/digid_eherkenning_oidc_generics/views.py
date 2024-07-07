import logging

from django.conf import settings
from django.contrib import auth, messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from mozilla_django_oidc_db.utils import do_op_logout
from mozilla_django_oidc_db.views import (
    _OIDC_ERROR_SESSION_KEY,
    OIDCAuthenticationCallbackView as BaseCallbackView,
    OIDCInit,
    get_exception_message,
)
from solo.models import SingletonModel

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)

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


# XXX: can probably be cleaned up with digid_eherkenning.oidc
class OIDCCallbackView(BaseCallbackView):
    failure_url = reverse_lazy("oidc-error")
    generic_error_msg = ""

    def get(self, request):
        try:
            with transaction.atomic():
                response = super().get(request)
        except (IntegrityError, ValidationError) as exc:
            logger.exception(
                "Something went wrong while attempting to authenticate via OIDC",
                exc_info=exc,
            )
            exc_message = get_exception_message(exc)
            request.session[_OIDC_ERROR_SESSION_KEY] = exc_message
            response = self.login_failure()
        else:
            # Upstream library doesn't do any error handling by default.
            if _OIDC_ERROR_SESSION_KEY in request.session:
                del request.session[_OIDC_ERROR_SESSION_KEY]

        # XXX: move this to a separate model
        error_message_mapping = self.get_settings("ERROR_MESSAGE_MAPPING")

        error = request.GET.get("error_description")
        error_label = error_message_mapping.get(error, str(self.generic_error_msg))
        if error and error_label:
            request.session[_OIDC_ERROR_SESSION_KEY] = error_label
        elif _OIDC_ERROR_SESSION_KEY in request.session and error_label:
            request.session[_OIDC_ERROR_SESSION_KEY] = error_label

        return response


class BaseOIDCLogoutView(View):
    config_class: type[SingletonModel]

    def get_success_url(self):
        return resolve_url(settings.LOGOUT_REDIRECT_URL)

    def get(self, request):
        if id_token := request.session.get("oidc_id_token"):
            config = self.config_class.get_solo()
            do_op_logout(config, id_token)

        if "oidc_login_next" in request.session:
            del request.session["oidc_login_next"]

        auth.logout(request)

        return HttpResponseRedirect(self.get_success_url())


digid_init = OIDCInit.as_view(config_class=OpenIDConnectDigiDConfig)
eherkenning_init = OIDCInit.as_view(config_class=OpenIDConnectEHerkenningConfig)


# FIXME: mozilla-django-oidc-db has a proper construct for this now.
class DigiDOIDCAuthenticationCallbackView(OIDCCallbackView):
    generic_error_msg = GENERIC_DIGID_ERROR_MSG


class DigiDOIDCLogoutView(BaseOIDCLogoutView):
    config_class = OpenIDConnectDigiDConfig


# FIXME: mozilla-django-oidc-db has a proper construct for this now.
class eHerkenningOIDCAuthenticationCallbackView(OIDCCallbackView):
    generic_error_msg = GENERIC_EHERKENNING_ERROR_MSG


class eHerkenningOIDCLogoutView(BaseOIDCLogoutView):
    config_class = OpenIDConnectEHerkenningConfig
