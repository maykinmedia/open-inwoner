import factory

from open_inwoner.soap.tests.factories import SoapServiceFactory

from ..models import SSDConfig


class SSDConfigFactory(factory.django.DjangoModelFactory):
    service = factory.SubFactory(SoapServiceFactory)
    applicatie_naam = "Open Inwoner"
    bedrijfs_naam = "Maykin"
    gemeentecode = "12345"

    class Meta:
        model = SSDConfig
