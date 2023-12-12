import logging

from django.conf import settings
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse_lazy
from django.views import View

import requests
from furl import furl
from mozilla_django_oidc.views import (
    OIDCAuthenticationRequestView as _OIDCAuthenticationRequestView,
)
from mozilla_django_oidc_db.views import (
    AdminLoginFailure,
    OIDCCallbackView as _OIDCCallbackView,
)

from digid_eherkenning_oidc_generics.mixins import (
    SoloConfigDigiDMixin,
    SoloConfigEHerkenningMixin,
)

logger = logging.getLogger(__name__)


class OIDCAuthenticationRequestView(_OIDCAuthenticationRequestView):
    def get_extra_params(self, request):
        kc_idp_hint = self.get_settings("OIDC_KEYCLOAK_IDP_HINT", "")
        if kc_idp_hint:
            return {"kc_idp_hint": kc_idp_hint}
        return {}


class OIDCFailureView(AdminLoginFailure):
    template_name = "digid_eherkenning_oidc_login_failure.html"


class OIDCCallbackView(_OIDCCallbackView):
    failure_url = reverse_lazy("oidc-error")


class OIDCLogoutView(View):
    def get_success_url(self):
        return resolve_url(settings.LOGOUT_REDIRECT_URL)

    def get(self, request):
        if "oidc_id_token" in request.session:
            logout_endpoint = self.config_class.get_solo().oidc_op_logout_endpoint
            if logout_endpoint:
                logout_url = furl(logout_endpoint).set(
                    {
                        "id_token_hint": request.session["oidc_id_token"],
                    }
                )
                requests.get(str(logout_url))

            del request.session["oidc_id_token"]

        if "oidc_login_next" in request.session:
            del request.session["oidc_login_next"]

        auth.logout(request)

        return HttpResponseRedirect(self.get_success_url())


class DigiDOIDCAuthenticationRequestView(
    SoloConfigDigiDMixin, OIDCAuthenticationRequestView
):
    pass


class DigiDOIDCAuthenticationCallbackView(SoloConfigDigiDMixin, OIDCCallbackView):
    pass


class DigiDOIDCLogoutView(SoloConfigDigiDMixin, OIDCLogoutView):
    pass


class eHerkenningOIDCAuthenticationRequestView(
    SoloConfigEHerkenningMixin, OIDCAuthenticationRequestView
):
    pass


class eHerkenningOIDCAuthenticationCallbackView(
    SoloConfigEHerkenningMixin, OIDCCallbackView
):
    pass


class eHerkenningOIDCLogoutView(SoloConfigEHerkenningMixin, OIDCLogoutView):
    pass
