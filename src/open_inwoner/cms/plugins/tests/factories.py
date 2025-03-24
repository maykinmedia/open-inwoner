import factory
from objectsapiclient.models import Configuration
from zgw_consumers.constants import APITypes

from open_inwoner.openzaak.tests.factories import ServiceFactory


class ObjectsAPIConfigFactory(factory.django.DjangoModelFactory):
    objects_api_service = factory.SubFactory(ServiceFactory, api_type=APITypes.orc)
    object_type_api_service = factory.SubFactory(ServiceFactory, api_type=APITypes.orc)

    class Meta:
        model = Configuration
        abstract = False
