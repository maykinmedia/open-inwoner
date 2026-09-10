from django.core.exceptions import ValidationError

from django_setup_configuration import ConfigurationModel
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed

from open_inwoner.kvk.models import KvKConfig


class KvKConfigurationModel(ConfigurationModel):
    """Configuration for the KvK (Chamber of Commerce) API."""

    class Meta:
        django_model_refs = {
            KvKConfig: ["api_root", "api_key"],
        }


class KvKConfigurationStep(BaseConfigurationStep):
    """
    Configures the KvK API used to look up company data (basisprofielen,
    vestigingen) for eHerkenning users.

    Only the fields present in the YAML source are applied: re-running this
    step, or running it with a YAML source that only lists a handful of
    fields, does not reset the fields it omits back to their defaults.
    Certificates are not managed by this step; attach those through the
    admin.
    """

    verbose_name = "KvK API configuration"
    enable_setting = "kvk_config_enable"
    namespace = "kvk_config"
    config_model = KvKConfigurationModel

    def execute(self, model: KvKConfigurationModel) -> None:
        config = KvKConfig.get_solo()

        for field, value in model.model_dump(exclude_unset=True).items():
            setattr(config, field, value)

        try:
            config.full_clean()
            config.save()
        except ValidationError as exc:
            raise ConfigurationRunFailed(
                f"Something went wrong while saving KvKConfig: {exc}"
            ) from exc
