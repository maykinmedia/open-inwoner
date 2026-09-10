from django.core.exceptions import ValidationError

from django_setup_configuration import ConfigurationModel, DjangoModelRef
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed

from open_inwoner.configurations.bootstrap.utils import get_soap_service
from open_inwoner.soap.models import SoapService
from open_inwoner.ssd.models import SSDConfig


class SSDConfigurationModel(ConfigurationModel):
    """Configuration for the SSD SOAP service backing "Mijn uitkeringen"."""

    service_identifier: str = DjangoModelRef(SSDConfig, "service")

    class Meta:
        django_model_refs = {
            SSDConfig: [
                "applicatie_naam",
                "bedrijfs_naam",
                "gemeentecode",
            ],
        }


class SSDConfigurationStep(BaseConfigurationStep):
    """
    Configures the SSD SOAP service used to retrieve yearly/monthly benefits
    reports for "Mijn uitkeringen".

    Only the fields present in the YAML source are applied: re-running this
    step, or running it with a YAML source that only lists a handful of
    fields, does not reset the fields it omits back to their defaults.
    """

    verbose_name = "SSD configuration"
    enable_setting = "ssd_config_enable"
    namespace = "ssd_config"
    config_model = SSDConfigurationModel

    def execute(self, model: SSDConfigurationModel) -> None:
        config = SSDConfig.get_solo()

        try:
            service = get_soap_service(model.service_identifier)
        except SoapService.DoesNotExist as exc:
            raise ConfigurationRunFailed(
                "Unable to retrieve SoapService with identifier "
                f"`{model.service_identifier}`. Try first configuring the "
                "`soap_services_config` step."
            ) from exc

        config.service = service

        for field, value in model.model_dump(
            exclude={"service_identifier"}, exclude_unset=True
        ).items():
            setattr(config, field, value)

        try:
            config.full_clean()
            config.save()
        except ValidationError as exc:
            raise ConfigurationRunFailed(
                f"Something went wrong while saving SSDConfig: {exc}"
            ) from exc
