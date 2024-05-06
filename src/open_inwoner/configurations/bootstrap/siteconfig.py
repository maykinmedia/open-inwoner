from django.conf import settings

from django_setup_configuration.base import ConfigSettingsModel
from django_setup_configuration.configuration import BaseConfigurationStep

from open_inwoner.configurations.models import SiteConfiguration


class SiteConfigurationStep(BaseConfigurationStep):
    """
    Set up general configuration ("Algemene configuratie")
    """

    verbose_name = "Site configuration"
    enable_setting = "SITE_CONFIG_ENABLE"
    required_settings = [
        "SITE_NAME",
        "SITE_PRIMARY_COLOR",
        "SITE_SECONDARY_COLOR",
        "SITE_ACCENT_COLOR",
    ]
    config_settings = ConfigSettingsModel(
        models=[SiteConfiguration],
        namespace="SITE",
        file_name="siteconfig",
        excluded_fields=[
            "id",
            "email_logo",
            "footer_logo",
            "favicon",
            "openid_connect_logo",
            "extra_css",
            "logo",
            "hero_image_login",
            "theme_stylesheet",
        ],
    )

    def get_setting_to_config_mapping(self) -> dict:
        setting_to_config = {
            self.config_settings.get_setting_name(field): field
            for field in self.config_settings.config_fields
        }
        return setting_to_config

    def is_configured(self):
        config = SiteConfiguration.get_solo()
        setting_to_config = self.get_setting_to_config_mapping()

        for required_setting in self.required_settings:
            config_field = setting_to_config[required_setting]
            if not getattr(config, config_field.name, None):
                return False
        return True

    def configure(self):
        config = SiteConfiguration.get_solo()
        setting_to_config = self.get_setting_to_config_mapping()

        for setting_name, config_field in setting_to_config.items():
            setting = getattr(settings, setting_name)
            if setting is not None:
                setattr(config, config_field.name, setting)
        config.save()

    def test_configuration(self):
        ...
