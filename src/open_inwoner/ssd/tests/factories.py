import factory

from open_inwoner.soap.tests.factories import SoapServiceFactory

from ..models import SSDConfig


class SSDConfigFactory(factory.django.DjangoModelFactory):
    service = factory.SubFactory(SoapServiceFactory)
    applicatie_naam = "Open Inwoner"
    bedrijfs_naam = "Maykin"
    gemeentecode = "12345"

    # report options
    jaaropgave_enabled = True
    jaaropgave_range = 3
    jaaropgave_available_from = "29-01"
    maandspecificatie_enabled = True
    maandspecificatie_range = 3
    maandspecificatie_available_from = 25

    class Meta:
        model = SSDConfig
