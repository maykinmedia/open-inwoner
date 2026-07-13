from typing import Any

from django.http import HttpRequest, HttpResponseBase

from digid_eherkenning.oidc.schemas import (
    DIGID_OPTIONS_SCHEMA,
    EHERKENNING_OPTIONS_SCHEMA,
)
from mozilla_django_oidc_db.plugins import AbstractUserOIDCPlugin
from mozilla_django_oidc_db.registry import register
from mozilla_django_oidc_db.typing import JSONObject

from open_inwoner.accounts.views.auth_oidc import (
    digid_callback,
    eherkenning_callback,
    eidas_callback,
)

from .constants import OIDC_DIGID_IDENTIFIER, OIDC_EH_IDENTIFIER, OIDC_EIDAS_IDENTIFIER
from .schema import EIDAS_OPTIONS_SCHEMA


class LegacyCallbackURLMixin:
    """
    Advertise the legacy per-provider callback URL as ``redirect_uri`` to the IdP.

    .. deprecated:: The per-provider callback URLs (``/digid-oidc/callback/`` etc.)
       predate the plugin architecture, which routes all callbacks through the single
       generic ``/oidc/callback/`` endpoint. They are kept as the advertised
       ``redirect_uri`` because customers have whitelisted them in their identity
       provider configuration, and switching would break logins until every IdP
       whitelist is updated. Once all environments also whitelist
       ``/oidc/callback/``, remove this mixin and the legacy callback routes in the
       ``*_urls`` modules.
    """

    legacy_callback_url_name: str

    def get_setting(self, attr: str, *args) -> Any:
        if attr == "OIDC_AUTHENTICATION_CALLBACK_URL":
            return self.legacy_callback_url_name
        return super().get_setting(attr, *args)


@register(OIDC_DIGID_IDENTIFIER)
class DigiDOIDCPlugin(LegacyCallbackURLMixin, AbstractUserOIDCPlugin):
    legacy_callback_url_name = "digid_oidc:callback"

    def get_schema(self) -> JSONObject:
        return DIGID_OPTIONS_SCHEMA

    def validate_settings(self) -> None:
        pass

    def handle_callback(self, request: HttpRequest) -> HttpResponseBase:
        return digid_callback(request)


@register(OIDC_EH_IDENTIFIER)
class eHerkenningOIDCPlugin(LegacyCallbackURLMixin, AbstractUserOIDCPlugin):
    legacy_callback_url_name = "eherkenning_oidc:callback"

    def get_schema(self) -> JSONObject:
        return EHERKENNING_OPTIONS_SCHEMA

    def validate_settings(self) -> None:
        pass

    def handle_callback(self, request: HttpRequest) -> HttpResponseBase:
        return eherkenning_callback(request)


@register(OIDC_EIDAS_IDENTIFIER)
class EIDASOIDCPlugin(LegacyCallbackURLMixin, AbstractUserOIDCPlugin):
    legacy_callback_url_name = "eidas_oidc:callback"

    def get_schema(self) -> JSONObject:
        return EIDAS_OPTIONS_SCHEMA

    def validate_settings(self) -> None:
        pass

    def handle_callback(self, request: HttpRequest) -> HttpResponseBase:
        return eidas_callback(request)
