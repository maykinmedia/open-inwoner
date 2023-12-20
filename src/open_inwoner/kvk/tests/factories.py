from pathlib import Path

import factory
from simple_certmanager.constants import CertificateTypes

TEST_FILES = Path(__file__).parent.resolve() / "files"

SERVER_CERT_ROOT = TEST_FILES / "public_cert.crt"
CLIENT_CERT = TEST_FILES / "client_cert.crt"
PRIVATE_KEY = TEST_FILES / "private_key.key"


class CertificateFactory(factory.django.DjangoModelFactory):
    type = "cert_only"
    public_certificate = factory.django.FileField(
        from_path=str(TEST_FILES / "public_cert.crt")
    )

    class Meta:
        model = "simple_certmanager.Certificate"

    class Params:
        with_private_key = factory.Trait(
            private_key=factory.django.FileField(
                from_path=str(TEST_FILES / "private_key.key")
            )
        )


SERVER_CERT = CertificateFactory.build(
    label="Staat der Nederlanden Private Root CA - G1",
    type=CertificateTypes.cert_only,
    public_certificate__filepath=str(SERVER_CERT_ROOT),
)


CLIENT_CERT = CertificateFactory.build(
    label="KvK client cert",
    type=CertificateTypes.cert_only,
    public_certificate__filepath=str(CLIENT_CERT),
)


CLIENT_CERT_PAIR = CertificateFactory.build(
    label="Staat der Nederlanden Private Root CA - G1",
    type=CertificateTypes.key_pair,
    public_certificate__filepath=str(SERVER_CERT_ROOT),
    with_private_key=True,
)
