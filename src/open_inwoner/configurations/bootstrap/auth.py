from django.conf import settings

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed

from digid_eherkenning_oidc_generics.admin import (
    OpenIDConnectDigiDConfigForm,
    OpenIDConnectEHerkenningConfigForm,
)
from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)


class DigiDOIDCConfigurationStep(BaseConfigurationStep):
    """
    Configure DigiD authentication via OpenID Connect
    """

    verbose_name = "Configuration for DigiD via OpenID Connect"
    required_settings = [
        "DIGID_OIDC_OIDC_RP_CLIENT_ID",
        "DIGID_OIDC_OIDC_RP_CLIENT_SECRET",
        # NOTE these are part of the model, but not actually part of the admin form
        # "DIGID_OIDC_OIDC_USE_NONCE",
        # "DIGID_OIDC_OIDC_NONCE_SIZE",
        # "DIGID_OIDC_OIDC_STATE_SIZE",
        # "DIGID_OIDC_OIDC_EXEMPT_URLS",
    ]
    all_settings = required_settings + [
        "DIGID_OIDC_IDENTIFIER_CLAIM_NAME",
        "DIGID_OIDC_OIDC_RP_SCOPES_LIST",
        "DIGID_OIDC_OIDC_RP_SIGN_ALGO",
        "DIGID_OIDC_OIDC_RP_IDP_SIGN_KEY",
        "DIGID_OIDC_OIDC_OP_DISCOVERY_ENDPOINT",
        "DIGID_OIDC_OIDC_OP_JWKS_ENDPOINT",
        "DIGID_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT",
        "DIGID_OIDC_OIDC_OP_TOKEN_ENDPOINT",
        "DIGID_OIDC_OIDC_OP_USER_ENDPOINT",
        "DIGID_OIDC_OIDC_OP_LOGOUT_ENDPOINT",
        "DIGID_OIDC_USERINFO_CLAIMS_SOURCE",
        "DIGID_OIDC_ERROR_MESSAGE_MAPPING",
        "DIGID_OIDC_OIDC_KEYCLOAK_IDP_HINT",
    ]
    enable_setting = "DIGID_OIDC_ENABLE"

    def is_configured(self) -> bool:
        return OpenIDConnectDigiDConfig.get_solo().enabled

    def configure(self):
        config = OpenIDConnectDigiDConfig.get_solo()

        # Use the model defaults
        form_data = {
            field.name: getattr(config, field.name)
            for field in OpenIDConnectDigiDConfig._meta.fields
        }

        # Only override field values with settings if they are defined
        for setting in self.all_settings:
            value = getattr(settings, setting, None)
            if value is not None:
                model_field_name = setting.split("DIGID_OIDC_")[1].lower()
                form_data[model_field_name] = value

        form_data["enabled"] = True

        # Saving the form with the default error_message_mapping `{}` causes the save to fail
        if not form_data["error_message_mapping"]:
            del form_data["error_message_mapping"]

        # Use the admin for to apply validation and fetch URLs from the discovery endpoint
        form = OpenIDConnectDigiDConfigForm(data=form_data)
        if not form.is_valid():
            raise ConfigurationRunFailed(
                f"Something went wrong while saving configuration: {form.errors}"
            )

        form.save()

    def test_configuration(self):
        """
        TODO not sure if it is feasible (because there are different possible IdPs),
        but it would be nice if we could test the login automatically
        """


class eHerkenningOIDCConfigurationStep(BaseConfigurationStep):
    """
    Configure eHerkenning authentication via OpenID Connect
    """

    verbose_name = "Configuration for eHerkenning via OpenID Connect"
    required_settings = [
        "EHERKENNING_OIDC_OIDC_RP_CLIENT_ID",
        "EHERKENNING_OIDC_OIDC_RP_CLIENT_SECRET",
        # NOTE these are part of the model, but not actually part of the admin form
        # "EHERKENNING_OIDC_OIDC_USE_NONCE",
        # "EHERKENNING_OIDC_OIDC_NONCE_SIZE",
        # "EHERKENNING_OIDC_OIDC_STATE_SIZE",
        # "EHERKENNING_OIDC_OIDC_EXEMPT_URLS",
    ]
    all_settings = required_settings + [
        "EHERKENNING_OIDC_IDENTIFIER_CLAIM_NAME",
        "EHERKENNING_OIDC_OIDC_RP_SCOPES_LIST",
        "EHERKENNING_OIDC_OIDC_RP_SIGN_ALGO",
        "EHERKENNING_OIDC_OIDC_RP_IDP_SIGN_KEY",
        "EHERKENNING_OIDC_OIDC_OP_DISCOVERY_ENDPOINT",
        "EHERKENNING_OIDC_OIDC_OP_JWKS_ENDPOINT",
        "EHERKENNING_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT",
        "EHERKENNING_OIDC_OIDC_OP_TOKEN_ENDPOINT",
        "EHERKENNING_OIDC_OIDC_OP_USER_ENDPOINT",
        "EHERKENNING_OIDC_OIDC_OP_LOGOUT_ENDPOINT",
        "EHERKENNING_OIDC_USERINFO_CLAIMS_SOURCE",
        "EHERKENNING_OIDC_ERROR_MESSAGE_MAPPING",
        "EHERKENNING_OIDC_OIDC_KEYCLOAK_IDP_HINT",
    ]
    enable_setting = "EHERKENNING_OIDC_ENABLE"

    def is_configured(self) -> bool:
        return OpenIDConnectEHerkenningConfig.get_solo().enabled

    def configure(self):
        config = OpenIDConnectEHerkenningConfig.get_solo()

        # Use the model defaults
        form_data = {
            field.name: getattr(config, field.name)
            for field in OpenIDConnectEHerkenningConfig._meta.fields
        }

        # Only override field values with settings if they are defined
        for setting in self.all_settings:
            value = getattr(settings, setting, None)
            if value is not None:
                model_field_name = setting.split("EHERKENNING_OIDC_")[1].lower()
                form_data[model_field_name] = value

        form_data["enabled"] = True

        # Saving the form with the default error_message_mapping `{}` causes the save to fail
        if not form_data["error_message_mapping"]:
            del form_data["error_message_mapping"]

        # Use the admin for to apply validation and fetch URLs from the discovery endpoint
        form = OpenIDConnectEHerkenningConfigForm(data=form_data)
        if not form.is_valid():
            raise ConfigurationRunFailed(
                f"Something went wrong while saving configuration: {form.errors}"
            )

        form.save()

    def test_configuration(self):
        """
        TODO not sure if it is feasible (because there are different possible IdPs),
        but it would be nice if we could test the login automatically
        """
