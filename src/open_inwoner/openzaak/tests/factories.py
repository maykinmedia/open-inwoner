import factory
from simple_certmanager.constants import CertificateTypes
from simple_certmanager.models import Certificate
from zgw_consumers.models import Service


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
