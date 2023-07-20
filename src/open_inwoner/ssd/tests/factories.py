import factory

from open_inwoner.soap.tests.factories import SoapServiceFactory

from ..models import JaaropgaveConfig, MaandspecificatieConfig, SSDConfig


class SSDConfigFactory(factory.django.DjangoModelFactory):
    service = factory.SubFactory(SoapServiceFactory)
    applicatie_naam = "Open Inwoner"
    bedrijfs_naam = "Maykin"
    gemeentecode = "12345"

    class Meta:
        model = SSDConfig

    # class Params:
    #     with_jaaropgave = factory.Trait(
    #         jaaropgave=factory.RelatedFactory(
    #             "open_inwoner.ssd.tests.factories.JaaropgaveConfigFactory"
    #         )
    #     )
    #     with_maandspecificatie = factory.Trait(
    #         maandspecificatie=factory.RelatedFactory(
    #             "open_inwoner.ssd.tests.factories.MaandspecificatieConfigFactory"
    #         )
    #     )


class JaaropgaveConfigFactory(factory.django.DjangoModelFactory):
    client = factory.RelatedFactory(SSDConfigFactory)
    jaaropgave_enabled = True
    jaaropgave_delta = 3
    jaaropgave_available_from = "29-01"

    class Meta:
        model = JaaropgaveConfig


class MaandspecificatieConfigFactory(factory.django.DjangoModelFactory):
    client = factory.RelatedFactory(SSDConfigFactory)
    maandspecificatie_enabled = True
    maandspecificatie_delta = 12
    maandspecificatie_available_from = 25

    class Meta:
        model = MaandspecificatieConfig
