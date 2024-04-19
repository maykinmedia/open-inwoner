from django.conf import settings

from django_setup_configuration.configuration import BaseConfigurationStep

from open_inwoner.configurations.models import SiteConfiguration

from .models import SiteConfigurationSettings


class SiteConfigurationStep(BaseConfigurationStep):
    """
    Set up general configuration ("Algemene configuratie")
    """

    verbose_name = "Site configuration"

    def is_configured(self):
        config = SiteConfiguration.get_solo()
        config_settings = SiteConfigurationSettings()
        required_settings = config_settings.get_required_settings()
        setting_to_config = config_settings.get_config_mapping()

        for required_setting in required_settings:
            config_field = setting_to_config[required_setting]
            if not getattr(config, config_field.name, None):
                return False
        return True

    def configure(self):
        config = SiteConfiguration.get_solo()
        config_settings = SiteConfigurationSettings()
        setting_to_config = config_settings.get_config_mapping()

        for setting_name, config_field in setting_to_config.items():
            setting = getattr(settings, setting_name)
            if setting is not None:
                setattr(config, config_field.name, setting)
        config.save()

    def test_configuration(self):
        ...
