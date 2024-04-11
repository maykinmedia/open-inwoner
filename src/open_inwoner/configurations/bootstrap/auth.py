from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import RequestFactory

from digid_eherkenning.admin import (
    DigidConfigurationAdmin,
    EherkenningConfigurationAdmin,
)
from digid_eherkenning.models import DigidConfiguration, EherkenningConfiguration
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed
from mozilla_django_oidc_db.forms import OpenIDConnectConfigForm
from mozilla_django_oidc_db.models import OpenIDConnectConfig
from simple_certmanager.models import Certificate

from digid_eherkenning_oidc_generics.admin import (
    OpenIDConnectDigiDConfigForm,
    OpenIDConnectEHerkenningConfigForm,
)
from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)
from open_inwoner.configurations.models import SiteConfiguration


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


class AdminOIDCConfigurationStep(BaseConfigurationStep):
    """
    Configure admin login via OpenID Connect
    """

    verbose_name = "Configuration for admin login via OpenID Connect"
    required_settings = [
        "ADMIN_OIDC_OIDC_RP_CLIENT_ID",
        "ADMIN_OIDC_OIDC_RP_CLIENT_SECRET",
    ]
    all_settings = required_settings + [
        "ADMIN_OIDC_OIDC_RP_SCOPES_LIST",
        "ADMIN_OIDC_OIDC_RP_SIGN_ALGO",
        "ADMIN_OIDC_OIDC_RP_IDP_SIGN_KEY",
        "ADMIN_OIDC_OIDC_OP_DISCOVERY_ENDPOINT",
        "ADMIN_OIDC_OIDC_OP_JWKS_ENDPOINT",
        "ADMIN_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT",
        "ADMIN_OIDC_OIDC_OP_TOKEN_ENDPOINT",
        "ADMIN_OIDC_OIDC_OP_USER_ENDPOINT",
        "ADMIN_OIDC_USERNAME_CLAIM",
        "ADMIN_OIDC_GROUPS_CLAIM",
        "ADMIN_OIDC_CLAIM_MAPPING",
        "ADMIN_OIDC_SYNC_GROUPS",
        "ADMIN_OIDC_SYNC_GROUPS_GLOB_PATTERN",
        "ADMIN_OIDC_DEFAULT_GROUPS",
        "ADMIN_OIDC_MAKE_USERS_STAFF",
        "ADMIN_OIDC_SUPERUSER_GROUP_NAMES",
        "ADMIN_OIDC_OIDC_USE_NONCE",
        "ADMIN_OIDC_OIDC_NONCE_SIZE",
        "ADMIN_OIDC_OIDC_STATE_SIZE",
        "ADMIN_OIDC_OIDC_EXEMPT_URLS",
        "ADMIN_OIDC_USERINFO_CLAIMS_SOURCE",
    ]
    enable_setting = "ADMIN_OIDC_ENABLE"

    def is_configured(self) -> bool:
        return OpenIDConnectConfig.get_solo().enabled

    def configure(self):
        config = OpenIDConnectConfig.get_solo()

        # Use the model defaults
        form_data = {
            field.name: getattr(config, field.name)
            for field in OpenIDConnectConfig._meta.fields
        }

        # `email` is in the claim_mapping by default, but email is used as the username field
        # by OIP, and you cannot map the username field when using OIDC
        if "email" in form_data["claim_mapping"]:
            del form_data["claim_mapping"]["email"]

        # Only override field values with settings if they are defined
        for setting in self.all_settings:
            value = getattr(settings, setting, None)
            if value is not None:
                model_field_name = setting.split("ADMIN_OIDC_")[1].lower()
                if model_field_name == "default_groups":
                    for group_name in value:
                        Group.objects.get_or_create(name=group_name)
                    value = Group.objects.filter(name__in=value)

                form_data[model_field_name] = value
        form_data["enabled"] = True

        # Use the admin for to apply validation and fetch URLs from the discovery endpoint
        form = OpenIDConnectConfigForm(data=form_data)
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


class DigiDConfigurationStep(BaseConfigurationStep):
    """
    Configure DigiD via SAML
    """

    verbose_name = "Configuration for DigiD via SAML"
    required_settings = [
        "DIGID_CERTIFICATE_LABEL",
        "DIGID_CERTIFICATE_TYPE",
        "DIGID_CERTIFICATE_PUBLIC_CERTIFICATE",
        "DIGID_METADATA_FILE_SOURCE",
        "DIGID_ENTITY_ID",
        "DIGID_BASE_URL",
        "DIGID_SERVICE_NAME",
        "DIGID_SERVICE_DESCRIPTION",
    ]
    all_settings = required_settings + [
        "DIGID_CERTIFICATE_PRIVATE_KEY",
        "DIGID_WANT_ASSERTIONS_SIGNED",
        "DIGID_WANT_ASSERTIONS_ENCRYPTED",
        "DIGID_ARTIFACT_RESOLVE_CONTENT_TYPE",
        "DIGID_KEY_PASSPHRASE",
        "DIGID_SIGNATURE_ALGORITHM",
        "DIGID_DIGEST_ALGORITHM",
        "DIGID_TECHNICAL_CONTACT_PERSON_TELEPHONE",
        "DIGID_TECHNICAL_CONTACT_PERSON_EMAIL",
        "DIGID_ORGANIZATION_URL",
        "DIGID_ORGANIZATION_NAME",
        "DIGID_ATTRIBUTE_CONSUMING_SERVICE_INDEX",
        "DIGID_REQUESTED_ATTRIBUTES",
        "DIGID_SLO",
    ]
    enable_setting = "DIGID_ENABLED"

    def is_configured(self) -> bool:
        config = DigidConfiguration.get_solo()
        return bool(
            config.certificate
            and config.metadata_file_source
            and config.entity_id
            and config.base_url
            and config.service_name
            and config.service_description
        )

    def configure(self):
        config = DigidConfiguration.get_solo()

        # Use the model defaults
        form_data = {
            field.name: getattr(config, field.name)
            for field in DigidConfiguration._meta.fields
        }

        # Only override field values with settings if they are defined
        for setting in self.all_settings:
            value = getattr(settings, setting, None)
            if value is not None:
                model_field_name = setting.split("DIGID_")[1].lower()
                if model_field_name.startswith("certificate"):
                    continue

                form_data[model_field_name] = value

        certificate, _ = Certificate.objects.get_or_create(
            label=settings.DIGID_CERTIFICATE_LABEL,
            defaults={
                "type": settings.DIGID_CERTIFICATE_TYPE,
            },
        )

        # Save the certificates separately, to ensure the resulting file is stored in
        # private media
        with open(settings.DIGID_CERTIFICATE_PUBLIC_CERTIFICATE) as public_cert:
            certificate.public_certificate.save("digid.crt", public_cert)

        if settings.DIGID_CERTIFICATE_PRIVATE_KEY:
            with open(settings.DIGID_CERTIFICATE_PRIVATE_KEY) as private_key:
                certificate.private_key.save("digid.key", private_key)

        form_data["certificate"] = certificate

        request = RequestFactory().get("/")
        digid_admin = DigidConfigurationAdmin(DigidConfiguration, AdminSite())
        form_class = digid_admin.get_form(request)

        form = form_class(data=form_data)
        if not form.is_valid():
            raise ConfigurationRunFailed(
                f"Something went wrong while saving configuration: {form.errors}"
            )

        try:
            form.save()
        except ValidationError as e:
            raise ConfigurationRunFailed(
                "Something went wrong while saving configuration"
            ) from e

    def test_configuration(self):
        """
        TODO
        """


class eHerkenningConfigurationStep(BaseConfigurationStep):
    """
    Configure eHerkenning via SAML
    """

    verbose_name = "Configuration for eHerkenning via SAML"
    required_settings = [
        "EHERKENNING_CERTIFICATE_LABEL",
        "EHERKENNING_CERTIFICATE_TYPE",
        "EHERKENNING_CERTIFICATE_PUBLIC_CERTIFICATE",
        "EHERKENNING_METADATA_FILE_SOURCE",
        "EHERKENNING_ENTITY_ID",
        "EHERKENNING_BASE_URL",
        "EHERKENNING_SERVICE_NAME",
        "EHERKENNING_SERVICE_DESCRIPTION",
        "EHERKENNING_OIN",
        "EHERKENNING_MAKELAAR_ID",
        "EHERKENNING_PRIVACY_POLICY",
    ]
    all_settings = required_settings + [
        "EHERKENNING_CERTIFICATE_PRIVATE_KEY",
        "EHERKENNING_WANT_ASSERTIONS_SIGNED",
        "EHERKENNING_WANT_ASSERTIONS_ENCRYPTED",
        "EHERKENNING_ARTIFACT_RESOLVE_CONTENT_TYPE",
        "EHERKENNING_KEY_PASSPHRASE",
        "EHERKENNING_SIGNATURE_ALGORITHM",
        "EHERKENNING_DIGEST_ALGORITHM",
        "EHERKENNING_ENTITY_ID",
        "EHERKENNING_BASE_URL",
        "EHERKENNING_SERVICE_NAME",
        "EHERKENNING_SERVICE_DESCRIPTION",
        "EHERKENNING_TECHNICAL_CONTACT_PERSON_TELEPHONE",
        "EHERKENNING_TECHNICAL_CONTACT_PERSON_EMAIL",
        "EHERKENNING_ORGANIZATION_URL",
        "EHERKENNING_ORGANIZATION_NAME",
        "EHERKENNING_EH_LOA",
        "EHERKENNING_EH_ATTRIBUTE_CONSUMING_SERVICE_INDEX",
        "EHERKENNING_EH_REQUESTED_ATTRIBUTES",
        "EHERKENNING_EH_SERVICE_UUID",
        "EHERKENNING_EH_SERVICE_INSTANCE_UUID",
        "EHERKENNING_EIDAS_LOA",
        "EHERKENNING_EIDAS_ATTRIBUTE_CONSUMING_SERVICE_INDEX",
        "EHERKENNING_EIDAS_REQUESTED_ATTRIBUTES",
        "EHERKENNING_EIDAS_SERVICE_UUID",
        "EHERKENNING_EIDAS_SERVICE_INSTANCE_UUID",
        "EHERKENNING_NO_EIDAS",
        "EHERKENNING_SERVICE_LANGUAGE",
    ]
    enable_setting = "EHERKENNING_ENABLE"

    def is_configured(self) -> bool:
        config = EherkenningConfiguration.get_solo()
        site_config = SiteConfiguration.get_solo()
        return site_config.eherkenning_enabled and bool(
            config.certificate
            and config.metadata_file_source
            and config.entity_id
            and config.base_url
            and config.service_name
            and config.service_description
            and config.oin
            and config.makelaar_id
            and config.privacy_policy
            and config.service_language
        )

    def configure(self):
        config = EherkenningConfiguration.get_solo()

        # Use the model defaults
        form_data = {
            field.name: getattr(config, field.name)
            for field in EherkenningConfiguration._meta.fields
        }

        # Only override field values with settings if they are defined
        for setting in self.all_settings:
            value = getattr(settings, setting, None)
            if value is not None:
                model_field_name = setting.split("EHERKENNING_")[1].lower()
                if model_field_name.startswith("certificate"):
                    continue

                form_data[model_field_name] = value

        certificate, _ = Certificate.objects.get_or_create(
            label=settings.EHERKENNING_CERTIFICATE_LABEL,
            defaults={
                "type": settings.EHERKENNING_CERTIFICATE_TYPE,
            },
        )

        # Save the certificates separately, to ensure the resulting file is stored in
        # private media
        with open(settings.EHERKENNING_CERTIFICATE_PUBLIC_CERTIFICATE) as public_cert:
            certificate.public_certificate.save("eherkenning.crt", public_cert)

        if settings.EHERKENNING_CERTIFICATE_PRIVATE_KEY:
            with open(settings.EHERKENNING_CERTIFICATE_PRIVATE_KEY) as private_key:
                certificate.private_key.save("eherkenning.key", private_key)

        form_data["certificate"] = certificate

        request = RequestFactory().get("/")
        eherkenning_admin = EherkenningConfigurationAdmin(
            EherkenningConfiguration, AdminSite()
        )
        form_class = eherkenning_admin.get_form(request)

        form = form_class(data=form_data)
        if not form.is_valid():
            raise ConfigurationRunFailed(
                f"Something went wrong while saving configuration: {form.errors}"
            )

        try:
            form.save()
        except ValidationError as e:
            raise ConfigurationRunFailed(
                "Something went wrong while saving configuration"
            ) from e

        site_config = SiteConfiguration.get_solo()
        site_config.eherkenning_enabled = True
        site_config.save()

    def test_configuration(self):
        """
        TODO
        """
