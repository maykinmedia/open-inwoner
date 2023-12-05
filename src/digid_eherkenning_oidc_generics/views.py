import logging

from django.contrib import auth
from django.core.exceptions import SuspiciousOperation

from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView as _OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView as _OIDCAuthenticationRequestView,
)

from digid_eherkenning_oidc_generics.mixins import (
    SoloConfigDigiDMixin,
    SoloConfigEHerkenningMixin,
)

from .backends import (
    OIDCAuthenticationDigiDBackend,
    OIDCAuthenticationEHerkenningBackend,
)

logger = logging.getLogger(__name__)


class OIDCAuthenticationRequestView(_OIDCAuthenticationRequestView):
    def get_extra_params(self, request):
        kc_idp_hint = self.get_settings("OIDC_KEYCLOAK_IDP_HINT", "")
        if kc_idp_hint:
            return {"kc_idp_hint": kc_idp_hint}
        return {}


class OIDCAuthenticationCallbackView(_OIDCAuthenticationCallbackView):
    auth_backend_class = None

    # TODO find easier way to authenticate using the backend class directly, without
    # having to override all of this
    def get(self, request):
        """
        Callback handler for OIDC authorization code flow
        """

        if request.GET.get("error"):
            # Ouch! Something important failed.
            # Make sure the user doesn't get to continue to be logged in
            # otherwise the refresh middleware will force the user to
            # redirect to authorize again if the session refresh has
            # expired.
            if request.user.is_authenticated:
                auth.logout(request)
            assert not request.user.is_authenticated
        elif "code" in request.GET and "state" in request.GET:

            # Check instead of "oidc_state" check if the "oidc_states" session key exists!
            if "oidc_states" not in request.session:
                return self.login_failure()

            # State and Nonce are stored in the session "oidc_states" dictionary.
            # State is the key, the value is a dictionary with the Nonce in the "nonce" field.
            state = request.GET.get("state")
            if state not in request.session["oidc_states"]:
                msg = "OIDC callback state not found in session `oidc_states`!"
                raise SuspiciousOperation(msg)

            # Get the nonce from the dictionary for further processing and delete the entry to
            # prevent replay attacks.
            nonce = request.session["oidc_states"][state]["nonce"]
            del request.session["oidc_states"][state]

            # Authenticating is slow, so save the updated oidc_states.
            request.session.save()
            # Reset the session. This forces the session to get reloaded from the database after
            # fetching the token from the OpenID connect provider.
            # Without this step we would overwrite items that are being added/removed from the
            # session in parallel browser tabs.
            request.session = request.session.__class__(request.session.session_key)

            kwargs = {
                "request": request,
                "nonce": nonce,
            }
            self.user = self.auth_backend_class().authenticate(**kwargs)
            self.user.backend = f"{self.auth_backend_class.__module__}.{self.auth_backend_class.__name__}"

            if self.user and self.user.is_active:
                return self.login_success()
        return self.login_failure()


class DigiDOIDCAuthenticationRequestView(
    SoloConfigDigiDMixin, OIDCAuthenticationRequestView
):
    pass


class DigiDOIDCAuthenticationCallbackView(
    SoloConfigDigiDMixin, OIDCAuthenticationCallbackView
):
    auth_backend_class = OIDCAuthenticationDigiDBackend


class eHerkenningOIDCAuthenticationRequestView(
    SoloConfigEHerkenningMixin, OIDCAuthenticationRequestView
):
    pass


class eHerkenningOIDCAuthenticationCallbackView(
    SoloConfigEHerkenningMixin, OIDCAuthenticationCallbackView
):
    auth_backend_class = OIDCAuthenticationEHerkenningBackend
