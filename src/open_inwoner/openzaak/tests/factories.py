import factory
from notifications_api_common.models import Subscription
from simple_certmanager.constants import CertificateTypes
from simple_certmanager.models import Certificate
from zgw_consumers.api_models.base import factory as zwg_factory
from zgw_consumers.api_models.catalogi import InformatieObjectType
from zgw_consumers.api_models.constants import RolOmschrijving
from zgw_consumers.models import Service
from zgw_consumers.test import generate_oas_component

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.api_models import Notification, Rol, ZaakType
from open_inwoner.openzaak.models import (
    CatalogusConfig,
    StatusTranslation,
    UserCaseInfoObjectNotification,
    UserCaseStatusNotification,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeStatusTypeConfig,
)


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


class CatalogusConfigFactory(factory.django.DjangoModelFactory):
    url = factory.Faker("url")
    domein = factory.Faker("pystr", max_chars=5)
    rsin = factory.Faker("pystr", max_chars=9)

    class Meta:
        model = CatalogusConfig


class ZaakTypeConfigFactory(factory.django.DjangoModelFactory):
    catalogus = factory.SubFactory(CatalogusConfigFactory)
    identificatie = factory.Faker("pystr", max_chars=50)
    omschrijving = factory.Faker("pystr", max_chars=80)

    class Meta:
        model = ZaakTypeConfig


class ZaakTypeInformatieObjectTypeConfigFactory(factory.django.DjangoModelFactory):
    zaaktype_config = factory.SubFactory(ZaakTypeConfigFactory)
    informatieobjecttype_url = factory.Faker("url")
    omschrijving = factory.Faker("pystr", max_chars=80)

    class Meta:
        model = ZaakTypeInformatieObjectTypeConfig

    @staticmethod
    def from_case_type_info_object_dicts(
        zaak_type: dict,
        info_object: dict,
        document_upload_enabled=False,
        document_notification_enabled=False,
        **extra_kwargs,
    ):
        kwargs = dict(
            zaaktype_config__identificatie=zaak_type["identificatie"],
            zaaktype_config__omschrijving=zaak_type["omschrijving"],
            informatieobjecttype_url=info_object["informatieobjecttype"],
            document_upload_enabled=document_upload_enabled,
            document_notification_enabled=document_notification_enabled,
            zaaktype_uuids=[zaak_type["uuid"]],
        )
        if zaak_type["catalogus"]:
            kwargs.update(
                zaaktype_config__catalogus__url=zaak_type["catalogus"],
            )
        else:
            kwargs.update(
                zaaktype_config__catalogus=None,
            )
        if extra_kwargs:
            kwargs.update(extra_kwargs)
        return ZaakTypeInformatieObjectTypeConfigFactory(**kwargs)


class ZaakTypeStatusTypeConfigFactory(factory.django.DjangoModelFactory):
    zaaktype_config = factory.SubFactory(ZaakTypeConfigFactory)
    statustype_url = factory.Faker("url")
    omschrijving = factory.Faker("pystr", max_chars=80)

    class Meta:
        model = ZaakTypeStatusTypeConfig


class UserCaseStatusNotificationFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    case_uuid = factory.Faker("uuid4")
    status_uuid = factory.Faker("uuid4")

    class Meta:
        model = UserCaseStatusNotification


class UserCaseInfoObjectNotificationFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    case_uuid = factory.Faker("uuid4")
    zaak_info_object_uuid = factory.Faker("uuid4")

    class Meta:
        model = UserCaseInfoObjectNotification


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


class StatusTranslationFactory(factory.django.DjangoModelFactory):
    status = factory.Faker("pystr", max_chars=50)
    translation = factory.Faker("pystr", max_chars=80)

    class Meta:
        model = StatusTranslation


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
