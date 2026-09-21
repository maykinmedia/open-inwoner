from django.core.exceptions import ValidationError

from django_setup_configuration import ConfigurationModel, DjangoModelRef
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed
from objectsapiclient.models import ObjectsAPIServiceConfiguration
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from open_inwoner.configurations.bootstrap.utils import get_service


class ObjectsAPIConfigurationModel(ConfigurationModel):
    """
    Configuration for the Objects/Objecttypes API services backing the "Mijn
    taken" plugin's "externe taken".
    """

    objects_api_identifier: str = DjangoModelRef(
        ObjectsAPIServiceConfiguration, "objects_api_client_config"
    )
    objecttypes_api_identifier: str = DjangoModelRef(
        ObjectsAPIServiceConfiguration, "objecttypes_api_client_config"
    )


class ObjectsAPIConfigurationStep(BaseConfigurationStep):
    """
    Configures the Objects API and Objecttypes API services the "Mijn taken"
    plugin (`TasksPlugin`) uses to fetch "externe taken".
    """

    verbose_name = "Objects API configuration"
    enable_setting = "objects_api_config_enable"
    namespace = "objects_api_config"
    config_model = ObjectsAPIConfigurationModel

    def execute(self, model: ObjectsAPIConfigurationModel) -> None:
        config = ObjectsAPIServiceConfiguration.get_solo()

        for identifier, attr in (
            (model.objects_api_identifier, "objects_api_client_config"),
            (model.objecttypes_api_identifier, "objecttypes_api_client_config"),
        ):
            try:
                service = get_service(identifier)
            except Service.DoesNotExist as exc:
                raise ConfigurationRunFailed(
                    f"Unable to retrieve Service with identifier `{identifier}`. "
                    "Try first configuring the `zgw_consumers` configuration "
                    "steps."
                ) from exc

            if service.api_type != APITypes.orc:
                raise ConfigurationRunFailed(
                    f"Found service with identifier `{identifier}`, but expected "
                    f"`api_type` to equal `{APITypes.orc}` and got "
                    f"`{service.api_type}`."
                )

            setattr(config, attr, service)

        try:
            config.full_clean()
            config.save()
        except ValidationError as exc:
            raise ConfigurationRunFailed(
                f"Something went wrong while saving ObjectsAPIServiceConfiguration: "
                f"{exc}"
            ) from exc
