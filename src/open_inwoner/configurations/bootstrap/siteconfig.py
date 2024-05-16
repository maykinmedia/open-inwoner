from django.conf import settings

from django_setup_configuration.configuration import BaseConfigurationStep

from open_inwoner.configurations.models import SiteConfiguration

from .base import ConfigSettingsBase


class SiteConfigurationSettings(ConfigSettingsBase):
    model = SiteConfiguration
    display_name = "General Configuration"
    namespace = "SITE"
    required_fields = (
        "name",
        "primary_color",
        "secondary_color",
        "accent_color",
    )
    excluded_fields = (
        "id",
        "email_logo",
        "footer_logo",
        "favicon",
        "openid_connect_logo",
        "extra_css",
        "logo",
        "hero_image_login",
        "theme_stylesheet",
    )


class SiteConfigurationStep(BaseConfigurationStep):
    """
    Set up general configuration ("Algemene configuratie")
    """

    verbose_name = "Site configuration"
    config_settings = SiteConfigurationSettings()

    def is_configured(self):
        config = SiteConfiguration.get_solo()
        required_settings = self.config_settings.get_required_settings()
        setting_to_config = self.config_settings.get_config_mapping()

        for required_setting in required_settings:
            config_field = setting_to_config[required_setting]
            if not getattr(config, config_field.name, None):
                return False
        return True

    def configure(self):
        config = SiteConfiguration.get_solo()
        setting_to_config = self.config_settings.get_config_mapping()

        for setting_name, config_field in setting_to_config.items():
            setting = getattr(settings, setting_name)
            if setting is not None:
                setattr(config, config_field.name, setting)
        config.save()

    def test_configuration(self):
        ...
