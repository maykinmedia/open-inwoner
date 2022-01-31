import factory
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service


class ServiceFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"API-{n}")
    api_root = factory.Sequence(lambda n: f"http://www.example{n}.com/api/v1/")

    class Meta:
        model = Service
