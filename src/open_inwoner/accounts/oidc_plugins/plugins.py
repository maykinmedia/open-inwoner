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


@register(OIDC_DIGID_IDENTIFIER)
class DigiDOIDCPlugin(AbstractUserOIDCPlugin):
    def get_schema(self) -> JSONObject:
        return DIGID_OPTIONS_SCHEMA

    def validate_settings(self) -> None:
        pass

    def handle_callback(self, request: HttpRequest) -> HttpResponseBase:
        return digid_callback(request)


@register(OIDC_EH_IDENTIFIER)
class eHerkenningOIDCPlugin(AbstractUserOIDCPlugin):
    def get_schema(self) -> JSONObject:
        return EHERKENNING_OPTIONS_SCHEMA

    def validate_settings(self) -> None:
        pass

    def handle_callback(self, request: HttpRequest) -> HttpResponseBase:
        return eherkenning_callback(request)


@register(OIDC_EIDAS_IDENTIFIER)
class EIDASOIDCPlugin(AbstractUserOIDCPlugin):
    def get_schema(self) -> JSONObject:
        return EIDAS_OPTIONS_SCHEMA

    def validate_settings(self) -> None:
        pass

    def handle_callback(self, request: HttpRequest) -> HttpResponseBase:
        return eidas_callback(request)
