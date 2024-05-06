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
from django_setup_configuration.base import ConfigSettingsModel
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


#
# DigiD OIDC
#
class DigiDOIDCConfigurationStep(BaseConfigurationStep):
    """
    Configure DigiD authentication via OpenID Connect
    """

    verbose_name = "Configuration for DigiD via OpenID Connect"
    enable_setting = "DIGID_OIDC_CONFIG_ENABLE"
    required_settings = [
        "DIGID_OIDC_OIDC_RP_CLIENT_ID",
        "DIGID_OIDC_OIDC_RP_CLIENT_SECRET",
    ]
    config_settings = ConfigSettingsModel(
        models=[OpenIDConnectDigiDConfig],
        namespace="DIGID_OIDC",
        file_name="digid_oidc",
    )

    def get_setting_to_config_mapping(self) -> dict:
        setting_to_config = {
            self.config_settings.get_setting_name(field): field
            for field in self.config_settings.config_fields
        }
        return setting_to_config

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
        setting_to_config = self.get_setting_to_config_mapping()

        for setting_name, config_field in setting_to_config.items():
            setting_value = getattr(settings, setting_name, None)
            if setting_value is not None:
                form_data[config_field.name] = setting_value

        form_data["enabled"] = True

        # Saving the form with the default error_message_mapping `{}` causes the save to fail
        if not form_data["error_message_mapping"]:
            del form_data["error_message_mapping"]

        # Use the admin form to apply validation and fetch URLs from the discovery endpoint
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


#
# eHerkenning OIDC
#
class eHerkenningOIDCConfigurationStep(BaseConfigurationStep):
    """
    Configure eHerkenning authentication via OpenID Connect
    """

    verbose_name = "Configuration for eHerkenning via OpenID Connect"
    enable_setting = "EHERKENNING_OIDC_CONFIG_ENABLE"
    required_settings = [
        "EHERKENNING_OIDC_OIDC_RP_CLIENT_ID",
        "EHERKENNING_OIDC_OIDC_RP_CLIENT_SECRET",
    ]
    config_settings = ConfigSettingsModel(
        models=[OpenIDConnectEHerkenningConfig],
        display_name="eHerkenning OIDC Configuration",
        file_name="eherkenning_oidc",
        namespace="EHERKENNING_OIDC",
    )

    def get_setting_to_config_mapping(self) -> dict:
        setting_to_config = {
            self.config_settings.get_setting_name(field): field
            for field in self.config_settings.config_fields
        }
        return setting_to_config

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
        setting_to_config = self.get_setting_to_config_mapping()

        for setting_name, config_field in setting_to_config.items():
            setting_value = getattr(settings, setting_name, None)
            if setting_value is not None:
                form_data[config_field.name] = setting_value

        form_data["enabled"] = True

        # Saving the form with the default error_message_mapping `{}` causes the save to fail
        if not form_data["error_message_mapping"]:
            del form_data["error_message_mapping"]

        # Use the admin form to apply validation and fetch URLs from the discovery endpoint
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


#
# Admin OIDC
#
class AdminOIDCConfigurationStep(BaseConfigurationStep):
    """
    Configure admin login via OpenID Connect
    """

    verbose_name = "Configuration for admin login via OpenID Connect"
    enable_setting = "ADMIN_OIDC_CONFIG_ENABLE"
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
    config_settings = ConfigSettingsModel(
        models=[OpenIDConnectConfig],
        file_name="admin_oidc",
        namespace="ADMIN_OIDC",
    )

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

        # Use the admin form to apply validation and fetch URLs from the discovery endpoint
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


#
# DigiD SAML
#
class DigiDConfigurationStep(BaseConfigurationStep):
    """
    Configure DigiD via SAML
    """

    verbose_name = "Configuration for DigiD via SAML"
    enable_setting = "DIGID_CONFIG_ENABLE"
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
    config_settings = ConfigSettingsModel(
        models=[DigidConfiguration],
        file_name="digid_saml",
        namespace="DIGID",
    )

    def get_setting_to_config_mapping(self) -> dict:
        setting_to_config = {
            self.config_settings.get_setting_name(field): field
            for field in self.config_settings.config_fields
        }
        return setting_to_config

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
        setting_to_config = self.get_setting_to_config_mapping()

        for setting_name, config_field in setting_to_config.items():
            if config_field.name.startswith("certificate"):
                continue
            setting_value = getattr(settings, setting_name, None)
            if setting_value is not None:
                form_data[config_field.name] = setting_value

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


#
# eHerkenning SAML
#
class eHerkenningConfigurationStep(BaseConfigurationStep):
    """
    Configure eHerkenning via SAML
    """

    verbose_name = "Configuration for eHerkenning via SAML"
    enable_setting = "EHERKENNING_CONFIG_ENABLE"
    required_settings = [
        "EHERKENNING_BASE_URL",
        "EHERKENNING_CERTIFICATE_LABEL",
        "EHERKENNING_CERTIFICATE_PUBLIC_CERTIFICATE",
        "EHERKENNING_CERTIFICATE_TYPE",
        "EHERKENNING_ENTITY_ID",
        "EHERKENNING_MAKELAAR_ID",
        "EHERKENNING_METADATA_FILE_SOURCE",
        "EHERKENNING_OIN",
        "EHERKENNING_PRIVACY_POLICY",
        "EHERKENNING_SERVICE_DESCRIPTION",
        "EHERKENNING_SERVICE_NAME",
    ]
    config_settings = ConfigSettingsModel(
        models=[EherkenningConfiguration],
        file_name="eherkenning_saml",
        namespace="EHERKENNING",
    )

    def get_setting_to_config_mapping(self) -> dict:
        setting_to_config = {
            self.config_settings.get_setting_name(field): field
            for field in self.config_settings.config_fields
        }
        return setting_to_config

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
        setting_to_config = self.get_setting_to_config_mapping()

        for setting_name, config_field in setting_to_config.items():
            if config_field.name.startswith("certificate"):
                continue

            setting_value = getattr(settings, setting_name, None)
            if setting_value is not None:
                form_data[config_field.name] = setting_value

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
