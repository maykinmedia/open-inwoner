from datetime import timedelta
from uuid import uuid4

from django.test import TestCase

from freezegun import freeze_time
from zgw_consumers.api_models.base import factory
from zgw_consumers.test import generate_oas_component

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.api_models import ZaakType
from open_inwoner.openzaak.models import (
    CatalogusConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeResultaatTypeConfig,
    ZaakTypeStatusTypeConfig,
)
from open_inwoner.openzaak.tests.factories import (
    CatalogusConfigFactory,
    UserCaseInfoObjectNotificationFactory,
    UserCaseStatusNotificationFactory,
    ZaakTypeConfigFactory,
    ZaakTypeInformatieObjectTypeConfigFactory,
    ZaakTypeResultaatTypeConfigFactory,
    ZaakTypeStatusTypeConfigFactory,
)
from open_inwoner.openzaak.tests.shared import CATALOGI_ROOT


class CatalogusConfigManagerTestCase(TestCase):
    def test_get_by_natural_key_returns_expected_instance(self):
        config = CatalogusConfigFactory()

        self.assertEqual(
            CatalogusConfig.objects.get_by_natural_key(*config.natural_key()),
            config,
        )

    def test_get_by_natural_key_not_found(self):
        with self.assertRaises(CatalogusConfig.DoesNotExist):
            CatalogusConfig.objects.get_by_natural_key(domein="test", rsin="1234")


class ZaakTypeConfigModelTestCase(TestCase):
    def test_get_by_natural_key_returns_expected_instance(self):
        zaak_type_config = ZaakTypeConfigFactory(
            identificatie="AAAA",
        )

        self.assertEqual(
            ZaakTypeConfig.objects.get_by_natural_key(*zaak_type_config.natural_key()),
            zaak_type_config,
        )

    def test_get_by_natural_key_not_found(self):
        unused_catalogus = CatalogusConfig()
        with self.assertRaises(ZaakTypeConfig.DoesNotExist):
            ZaakTypeConfig.objects.get(
                identificatie="AAAA",
                catalogus__domein="bogus",
                catalogus__rsin="bogus",
            )

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


class ZaakTypeStatusTypeConfigModelTestCase(TestCase):
    def test_get_by_natural_key_returns_expected_instance(self):
        zt = ZaakTypeConfigFactory()
        zt_status_type_config = ZaakTypeStatusTypeConfigFactory(
            zaaktype_config=zt,
            omschrijving="test",
        )

        self.assertEqual(
            ZaakTypeStatusTypeConfig.objects.get_by_natural_key(
                omschrijving="test",
                zaaktype_config_identificatie=zt.identificatie,
                catalogus_domein=zt.catalogus.domein,
                catalogus_rsin=zt.catalogus.rsin,
            ),
            zt_status_type_config,
        )

    def test_get_by_natural_key_not_found(self):
        unused_zt = ZaakTypeConfigFactory()
        with self.assertRaises(ZaakTypeStatusTypeConfig.DoesNotExist):
            ZaakTypeStatusTypeConfig.objects.get_by_natural_key(
                omschrijving="test",
                zaaktype_config_identificatie=unused_zt.identificatie,
                catalogus_domein=unused_zt.catalogus.domein,
                catalogus_rsin=unused_zt.catalogus.rsin,
            )


class ZaakTypeResultaatTypeConfigModelTestCase(TestCase):
    def test_get_by_natural_key_returns_expected_instance(self):
        zt = ZaakTypeConfigFactory()
        zt_status_type_config = ZaakTypeResultaatTypeConfigFactory(
            zaaktype_config=zt,
            omschrijving="test",
        )

        self.assertEqual(
            ZaakTypeResultaatTypeConfig.objects.get_by_natural_key(
                omschrijving="test",
                zaaktype_config_identificatie=zt.identificatie,
                catalogus_domein=zt.catalogus.domein,
                catalogus_rsin=zt.catalogus.rsin,
            ),
            zt_status_type_config,
        )

    def test_get_by_natural_key_not_found(self):
        zt = ZaakTypeConfigFactory()
        with self.assertRaises(ZaakTypeResultaatTypeConfig.DoesNotExist):
            ZaakTypeResultaatTypeConfig.objects.get_by_natural_key(
                omschrijving="bogus",
                zaaktype_config_identificatie=zt.identificatie,
                catalogus_domein=zt.catalogus.domein,
                catalogus_rsin=zt.catalogus.rsin,
            )


class ZaakTypeInformatieObjectTypeConfigFactoryModelTestCase(TestCase):
    def test_get_by_natural_key_returns_expected_instance(self):
        zt = ZaakTypeConfigFactory()
        zt_io_type = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zt, omschrijving="test"
        )

        self.assertEqual(
            ZaakTypeInformatieObjectTypeConfig.objects.get_by_natural_key(
                omschrijving="test",
                zaaktype_config_identificatie=zt.identificatie,
                catalogus_domein=zt.catalogus.domein,
                catalogus_rsin=zt.catalogus.rsin,
            ),
            zt_io_type,
        )

    def test_get_by_natural_key_not_found(self):
        zt = ZaakTypeConfigFactory()
        with self.assertRaises(ZaakTypeInformatieObjectTypeConfig.DoesNotExist):
            ZaakTypeInformatieObjectTypeConfig.objects.get_by_natural_key(
                omschrijving="bogus",
                zaaktype_config_identificatie=zt.identificatie,
                catalogus_domein=zt.catalogus.domein,
                catalogus_rsin=zt.catalogus.rsin,
            )

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


class UserCaseStatusNotificationTests(TestCase):
    def test_status_has_received_similar_notes_within(self):
        user = UserFactory()
        case_uuid = uuid4()
        other_case_uuid = uuid4()

        with freeze_time("2023-01-01 01:00:00"):
            # create unrelated sent note for different case
            UserCaseStatusNotificationFactory(
                user=user, case_uuid=other_case_uuid, is_sent=True
            )
            # create a related note we didn't send
            UserCaseStatusNotificationFactory(
                user=user,
                case_uuid=case_uuid,
                is_sent=False,
                collision_key="case_status_notification",
            )
            # create our note
            note = UserCaseStatusNotificationFactory(
                user=user,
                case_uuid=case_uuid,
                is_sent=True,
                collision_key="case_status_notification",
            )
            # it doesn't see any of the above
            self.assertFalse(
                note.has_received_similar_notes_within(
                    timedelta(minutes=10), "case_status_notification"
                )
            )

        # advance half hour
        with freeze_time("2023-01-01 01:30:00"):
            note = UserCaseStatusNotificationFactory(
                user=user, case_uuid=case_uuid, is_sent=True
            )
            # nothing is past 10 minutes
            self.assertFalse(
                note.has_received_similar_notes_within(
                    timedelta(minutes=10), "case_status_notification"
                )
            )
            # looking back an hour we see the earlier note
            self.assertTrue(
                note.has_received_similar_notes_within(
                    timedelta(minutes=60), "case_status_notification"
                )
            )

    def test_case_info_has_received_similar_notes_within(self):
        user = UserFactory()
        case_uuid = uuid4()
        other_case_uuid = uuid4()

        with freeze_time("2023-01-01 01:00:00"):
            # create unrelated sent note for different case
            UserCaseInfoObjectNotificationFactory(
                user=user,
                case_uuid=other_case_uuid,
                is_sent=True,
                collision_key="case_document_notification",
            )
            # create a related note we didn't send
            UserCaseInfoObjectNotificationFactory(
                user=user,
                case_uuid=case_uuid,
                is_sent=False,
                collision_key="case_document_notification",
            )
            # create our note
            note = UserCaseInfoObjectNotificationFactory(
                user=user,
                case_uuid=case_uuid,
                is_sent=True,
                collision_key="case_document_notification",
            )
            # it doesn't see any of the above
            self.assertFalse(
                note.has_received_similar_notes_within(
                    timedelta(minutes=10), "case_document_notification"
                )
            )

        # advance half hour
        with freeze_time("2023-01-01 01:30:00"):
            note = UserCaseInfoObjectNotificationFactory(
                user=user,
                case_uuid=case_uuid,
                is_sent=True,
                collision_key="case_document_notification",
            )
            # nothing is past 10 minutes
            self.assertFalse(
                note.has_received_similar_notes_within(
                    timedelta(minutes=10), "case_document_notification"
                )
            )
            # looking back an hour we see the earlier note
            self.assertTrue(
                note.has_received_similar_notes_within(
                    timedelta(minutes=60), "case_document_notification"
                )
            )
