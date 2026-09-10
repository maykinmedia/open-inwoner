from django_setup_configuration import ConfigurationModel, DjangoModelRef
from django_setup_configuration.configuration import BaseConfigurationStep

from open_inwoner.soap.models import SoapService


class SoapServiceConfig(ConfigurationModel):
    """A single SOAP service, e.g. the SSD GWS endpoint."""

    identifier: str = DjangoModelRef(SoapService, "slug", examples=["ssd-mock"])

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
                slug=service.identifier,
                defaults={"url": service.url},
            )
