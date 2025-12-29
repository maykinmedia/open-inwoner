import factory
from objectsapiclient.models import ObjectsAPIServiceConfiguration
from zgw_consumers.constants import APITypes

from open_inwoner.mijn_aanvragen.tests.factories import ServiceFactory


class ObjectsAPIServiceConfigFactory(factory.django.DjangoModelFactory):
    objects_api_client_config = factory.SubFactory(
        ServiceFactory, api_type=APITypes.orc
    )
    objecttypes_api_client_config = factory.SubFactory(
        ServiceFactory, api_type=APITypes.orc
    )

    class Meta:
        model = ObjectsAPIServiceConfiguration
        abstract = False
