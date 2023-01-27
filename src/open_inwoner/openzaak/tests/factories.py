import factory
from notifications_api_common.models import Subscription
from simple_certmanager.constants import CertificateTypes
from simple_certmanager.models import Certificate
from zgw_consumers.api_models.base import factory as zwg_factory
from zgw_consumers.api_models.constants import RolOmschrijving
from zgw_consumers.models import Service
from zgw_consumers.test import generate_oas_component

from open_inwoner.openzaak.api_models import Notification, Rol


class ServiceFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"API-{n}")
    api_root = factory.Sequence(lambda n: f"http://www.example{n}.com/api/v1/")

    class Meta:
        model = Service


class CertificateFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"Certificate-{n}")

    class Meta:
        model = Certificate

    class Params:
        cert_only = factory.Trait(
            type=CertificateTypes.cert_only,
            public_certificate=factory.django.FileField(filename="server.crt"),
        )
        key_pair = factory.Trait(
            type=CertificateTypes.key_pair,
            public_certificate=factory.django.FileField(filename="public.crt"),
            private_key=factory.django.FileField(filename="private.crt"),
        )


class SubscriptionFactory(factory.django.DjangoModelFactory):
    callback_url = factory.Faker("url")
    client_id = factory.Faker("word")
    secret = factory.Faker("pystr")
    channels = ["zaken"]

    class Meta:
        model = Subscription


class NotificationFactory(factory.Factory):
    kanaal = "zaken"
    resource = "zaak"
    resource_url = "https://zaken.nl/api/v1/zaken/uuid-0001"
    hoofd_object = factory.LazyAttribute(lambda obj: obj.resource_url)
    actie = "update"
    aanmaakdatum = factory.Faker("past_datetime")
    kenmerken = dict()

    class Meta:
        model = Notification


def generate_rol(
    type_: str,
    identification: dict,
    description: str = RolOmschrijving.initiator,
) -> Rol:
    # helper for readability
    component = generate_oas_component(
        "zrc",
        "schemas/Rol",
        betrokkeneType=type_,
        betrokkeneIdentificatie=identification,
        omschrijvingGeneriek=description,
    )
    return zwg_factory(Rol, component)
