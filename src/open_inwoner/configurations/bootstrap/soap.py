from django_setup_configuration import ConfigurationModel, DjangoModelRef
from django_setup_configuration.configuration import BaseConfigurationStep

from open_inwoner.soap.models import SoapService


class SoapServiceConfig(ConfigurationModel):
    """A single SOAP service, e.g. the SSD GWS endpoint."""

    # SoapService has no dedicated slug/identifier field, unlike
    # zgw_consumers.Service -- `label` doubles as both the human-readable
    # name and the identifier other steps refer to it by (see
    # bootstrap.utils.get_soap_service()).
    identifier: str = DjangoModelRef(SoapService, "label", examples=["ssd-mock"])

    class Meta:
        django_model_refs = {
            SoapService: ["url"],
        }


class SoapServicesConfigurationModel(ConfigurationModel):
    services: list[SoapServiceConfig]


class SoapServiceConfigurationStep(BaseConfigurationStep):
    """
    Configure one or more `SoapService` instances (SOAP/WS-* endpoints, e.g.
    the SSD GWS service), analogous to zgw_consumers' ServiceConfigurationStep
    for REST/ZGW services. Client/server certificates aren't settable here --
    attach those in the admin for a real (mutual-TLS) connection.
    """

    verbose_name = "SOAP service configuration"
    enable_setting = "soap_services_config_enable"
    namespace = "soap_services_config"
    config_model = SoapServicesConfigurationModel

    def execute(self, model: SoapServicesConfigurationModel) -> None:
        for service in model.services:
            SoapService.objects.update_or_create(
                label=service.identifier,
                defaults={"url": service.url},
            )
