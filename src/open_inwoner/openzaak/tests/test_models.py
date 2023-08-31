from datetime import timedelta
from uuid import uuid4

from django.test import TestCase

from freezegun import freeze_time
from zgw_consumers.api_models.base import factory
from zgw_consumers.test import generate_oas_component

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.api_models import ZaakType
from open_inwoner.openzaak.models import (
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
)
from open_inwoner.openzaak.tests.factories import (
    CatalogusConfigFactory,
    UserCaseStatusNotificationFactory,
    ZaakTypeConfigFactory,
    ZaakTypeInformatieObjectTypeConfigFactory,
)
from open_inwoner.openzaak.tests.shared import CATALOGI_ROOT


class ZaakTypeConfigModelTestCase(TestCase):
    def test_queryset_filter_case_type_with_catalog(self):
        catalog = CatalogusConfigFactory(
            url=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )
        zaak_type_config = ZaakTypeConfigFactory(
            catalogus=catalog,
            identificatie="AAAA",
        )
        case_type = factory(
            ZaakType,
            generate_oas_component(
                "ztc",
                "schemas/ZaakType",
                uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                catalogus=catalog.url,
                identificatie="AAAA",
            ),
        )

        actual = list(ZaakTypeConfig.objects.filter_case_type(case_type))
        self.assertEqual(actual, [zaak_type_config])

    def test_queryset_filter_case_type_without_catalog(self):
        zaak_type_config = ZaakTypeConfigFactory(
            catalogus=None,
            identificatie="AAAA",
        )
        case_type = factory(
            ZaakType,
            generate_oas_component(
                "ztc",
                "schemas/ZaakType",
                uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                catalogus=None,
                identificatie="AAAA",
            ),
        )

        actual = list(ZaakTypeConfig.objects.filter_case_type(case_type))
        self.assertEqual(actual, [zaak_type_config])


class ZaakTypeInformatieObjectTypeConfigFactoryModelTestCase(TestCase):
    def test_queryset_filter_case_type_with_catalog(self):
        catalog = CatalogusConfigFactory(
            url=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )
        zaak_type_config = ZaakTypeConfigFactory(
            catalogus=catalog,
            identificatie="AAAA",
        )
        a1 = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url="https://example.com/v1/infoobject/a1",
            zaaktype_uuids=["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
        )
        a2 = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url="https://example.com/v1/infoobject/a2",
            zaaktype_uuids=[],
        )
        b = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url="https://example.com/v1/infoobject/bbb",
            zaaktype_uuids=["aaaaaaaa-aaaa-bbbb-aaaa-aaaaaaaaaaaa"],
        )
        c = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config__catalogus=catalog,
            zaaktype_config__identificatie="CCC",
            informatieobjecttype_url="https://example.com/v1/infoobject/bbb",
            zaaktype_uuids=["aaaaaaaa-aaaa-bbbb-aaaa-aaaaaaaaaaaa"],
        )
        case_type = factory(
            ZaakType,
            generate_oas_component(
                "ztc",
                "schemas/ZaakType",
                uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                catalogus=catalog.url,
                identificatie="AAAA",
            ),
        )

        actual = list(
            ZaakTypeInformatieObjectTypeConfig.objects.filter_case_type(case_type)
        )
        self.assertEqual(actual, [a1])

    def test_queryset_filter_case_type_without_catalog(self):
        zaak_type_config = ZaakTypeConfigFactory(
            catalogus=None,
            identificatie="AAAA",
        )
        a1 = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url="https://example.com/v1/infoobject/a1",
            zaaktype_uuids=["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
        )
        a2 = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url="https://example.com/v1/infoobject/a2",
            zaaktype_uuids=[],
        )
        b = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url="https://example.com/v1/infoobject/bbb",
            zaaktype_uuids=["aaaaaaaa-aaaa-bbbb-aaaa-aaaaaaaaaaaa"],
        )
        c = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config__catalogus=None,
            zaaktype_config__identificatie="CCC",
            informatieobjecttype_url="https://example.com/v1/infoobject/bbb",
            zaaktype_uuids=["aaaaaaaa-aaaa-bbbb-aaaa-aaaaaaaaaaaa"],
        )
        case_type = factory(
            ZaakType,
            generate_oas_component(
                "ztc",
                "schemas/ZaakType",
                uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                catalogus=None,
                identificatie="AAAA",
            ),
        )

        actual = list(
            ZaakTypeInformatieObjectTypeConfig.objects.filter_case_type(case_type)
        )
        self.assertEqual(actual, [a1])


class UserCaseStatusNotificationTests(TestCase):
    def test_has_received_similar_notes_within(self):
        user = UserFactory()
        case_uuid = uuid4()
        other_case_uuid = uuid4()

        with freeze_time("2023-01-01 01:00:00"):
            # create unrelated note for different case
            UserCaseStatusNotificationFactory(user=user, case_uuid=other_case_uuid)

            # create our note
            note = UserCaseStatusNotificationFactory(user=user, case_uuid=case_uuid)
            # it doesn't see itself
            self.assertFalse(
                note.has_received_similar_notes_within(timedelta(minutes=10))
            )

        # advance half hour
        with freeze_time("2023-01-01 01:30:00"):
            note = UserCaseStatusNotificationFactory(user=user, case_uuid=case_uuid)
            # nothing is past 10 minutes
            self.assertFalse(
                note.has_received_similar_notes_within(timedelta(minutes=10))
            )
            # looking back an hour we see the earlier note
            self.assertTrue(
                note.has_received_similar_notes_within(timedelta(minutes=60))
            )
