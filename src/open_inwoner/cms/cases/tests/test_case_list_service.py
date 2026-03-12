import re
from unittest.mock import Mock

from django.test import RequestFactory, TestCase, override_settings

import requests_mock
from requests_mock import ANY
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.cases.views.services import (
    CaseListService,
    SkipReason,
    ZakenResult,
)
from open_inwoner.openzaak.constants import StatusIndicators
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.factories import (
    CatalogusConfigFactory,
    ZaakTypeConfigFactory,
    ZaakTypeStatusTypeConfigFactory,
    ZGWApiGroupConfigFactory,
)
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.openzaak.tests.shared import CATALOGI_ROOT, ZAKEN_ROOT
from open_inwoner.utils.test import ClearCachesMixin, paginated_response


@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls",
    ZGW_CASE_LIST_NUM_WORKERS=1,  # Force single-threaded for tests
    ZGW_CASE_LIST_FETCH_TIMEOUT=5,  # Short timeout for tests
)
class CaseListServiceTests(ClearCachesMixin, TestCase):
    """Tests for CaseListService focusing on skip tracking functionality."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory(bsn="900222086")
        self.factory = RequestFactory()

        # Set up OpenZaak config
        self.oz_config = OpenZaakConfig.get_solo()
        self.oz_config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.oz_config.save()

        # Set up API group
        self.api_group = ZGWApiGroupConfigFactory(
            ztc_service__api_root=CATALOGI_ROOT,
            zrc_service__api_root=ZAKEN_ROOT,
        )

        # Set up catalogus and zaaktype configs
        self.catalogus_config = CatalogusConfigFactory(
            url=f"{CATALOGI_ROOT}catalogussen/1234",
            service=self.api_group.ztc_service,
        )

        self.zaaktype = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/1",
            omschrijving="Test zaaktype",
            catalogus=self.catalogus_config.url,
            identificatie="ZAAK-TYPE-1",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )

        self.zaaktype_config = ZaakTypeConfigFactory(
            catalogus=self.catalogus_config,
            identificatie="ZAAK-TYPE-1",
            urls=[self.zaaktype["url"]],
        )

        self.statustype = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/1",
            zaaktype=self.zaaktype["url"],
            omschrijving="Test status",
            volgnummer=1,
        )

        self.zaaktype_statustype_config = ZaakTypeStatusTypeConfigFactory(
            zaaktype_config=self.zaaktype_config,
            statustype_url=self.statustype["url"],
            status_indicator=StatusIndicators.info,
        )

    def _create_request(self, user=None):
        """Helper to create a mock request with the given user."""
        if user is None:
            user = self.user
        request = self.factory.get("/")
        request.user = user
        return request

    @requests_mock.Mocker()
    def test_get_zaken_returns_zakenresult_with_empty_lists_when_no_zaken(self, m):
        """Test that get_zaken returns ZakenResult with empty lists when no zaken exist."""
        # Mock any GET request to zaken endpoint
        m.get(ANY, json=paginated_response([]))

        request = self._create_request()
        service = CaseListService.from_request(request)
        result = service.get_zaken()

        self.assertIsInstance(result, ZakenResult)
        self.assertEqual(len(result.zaken), 0)
        self.assertEqual(len(result.skipped), 0)
        self.assertEqual(result.total_fetched, 0)

    @requests_mock.Mocker()
    def test_get_zaken_returns_visible_zaak_in_zaken_list(self, m):
        """Test that visible zaken are included in the zaken list."""
        zaak = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/1",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-001",
            omschrijving="Test zaak",
            startdatum="2024-01-01",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )

        status = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/1",
            zaak=zaak["url"],
            statustype=self.statustype["url"],
        )

        # Mock API responses
        m.get(
            re.compile(re.escape(f"{ZAKEN_ROOT}zaken")),
            json=paginated_response([zaak]),
        )
        m.get(f"{CATALOGI_ROOT}zaaktypen/1", json=self.zaaktype)
        m.get(f"{CATALOGI_ROOT}statustypen/1", json=self.statustype)
        m.get(f"{ZAKEN_ROOT}statussen?zaak={zaak['url']}", json=[status])
        m.get(f"{ZAKEN_ROOT}zaken/1/rollen", json=[])
        m.get(f"{ZAKEN_ROOT}resultaten?zaak={zaak['url']}", json=[])

        request = self._create_request()
        service = CaseListService.from_request(request)
        result = service.get_zaken()

        self.assertIsInstance(result, ZakenResult)
        self.assertEqual(len(result.zaken), 1)
        self.assertEqual(len(result.skipped), 0)
        self.assertEqual(result.total_fetched, 1)
        self.assertEqual(result.zaken[0].identification, "ZAAK-001")

    @requests_mock.Mocker()
    def test_get_zaken_skips_zaak_with_high_confidentiality(self, m):
        """Test that zaken with confidentiality above max are skipped with NOT_VISIBLE reason."""
        zaak = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/1",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-SECRET",
            omschrijving="Secret zaak",
            startdatum="2024-01-01",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.vertrouwelijk,
        )

        status = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/1",
            zaak=zaak["url"],
            statustype=self.statustype["url"],
        )

        # Mock API responses
        m.get(
            re.compile(re.escape(f"{ZAKEN_ROOT}zaken")),
            json=paginated_response([zaak]),
        )
        m.get(f"{CATALOGI_ROOT}zaaktypen/1", json=self.zaaktype)
        m.get(f"{CATALOGI_ROOT}statustypen/1", json=self.statustype)
        m.get(f"{ZAKEN_ROOT}statussen?zaak={zaak['url']}", json=[status])
        m.get(f"{ZAKEN_ROOT}zaken/1/rollen", json=[])
        m.get(f"{ZAKEN_ROOT}resultaten?zaak={zaak['url']}", json=[])

        request = self._create_request()
        service = CaseListService.from_request(request)
        result = service.get_zaken()

        # Zaak should be skipped due to confidentiality
        self.assertEqual(len(result.zaken), 0)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.total_fetched, 1)

        skipped = result.skipped[0]
        self.assertEqual(skipped.reason, SkipReason.NOT_VISIBLE)
        self.assertIn("vertrouwelijk", skipped.details.lower())
        self.assertEqual(skipped.zaak.identification, "ZAAK-SECRET")

    @requests_mock.Mocker()
    def test_get_zaken_skips_zaak_with_resolution_failure(self, m):
        """Test that zaken with resolution failures are skipped with RESOLUTION_FAILED reason."""
        zaak = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/1",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-BROKEN",
            omschrijving="Broken zaak",
            startdatum="2024-01-01",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )

        # Mock API responses - zaaktype fetch fails
        m.get(
            re.compile(re.escape(f"{ZAKEN_ROOT}zaken")),
            json=paginated_response([zaak]),
        )
        m.get(f"{CATALOGI_ROOT}zaaktypen/1", status_code=500)  # Simulate failure

        request = self._create_request()
        service = CaseListService.from_request(request)
        result = service.get_zaken()

        # Zaak should be skipped due to resolution failure
        self.assertEqual(len(result.zaken), 0)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.total_fetched, 1)

        skipped = result.skipped[0]
        self.assertEqual(skipped.reason, SkipReason.RESOLUTION_FAILED)
        self.assertIsNotNone(skipped.details)
        self.assertEqual(skipped.zaak.identification, "ZAAK-BROKEN")

    @requests_mock.Mocker()
    def test_get_zaken_returns_mix_of_visible_and_skipped(self, m):
        """Test that both visible and skipped zaken are correctly categorized."""
        visible_zaak = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/1",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-VISIBLE",
            omschrijving="Visible zaak",
            startdatum="2024-01-01",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )

        secret_zaak = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/2",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-SECRET",
            omschrijving="Secret zaak",
            startdatum="2024-01-02",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.geheim,
        )

        status1 = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/1",
            zaak=visible_zaak["url"],
            statustype=self.statustype["url"],
        )

        status2 = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/2",
            zaak=secret_zaak["url"],
            statustype=self.statustype["url"],
        )

        # Mock API responses
        m.get(
            re.compile(re.escape(f"{ZAKEN_ROOT}zaken")),
            json=paginated_response([visible_zaak, secret_zaak]),
        )
        m.get(f"{CATALOGI_ROOT}zaaktypen/1", json=self.zaaktype)
        m.get(f"{CATALOGI_ROOT}statustypen/1", json=self.statustype)
        m.get(f"{ZAKEN_ROOT}statussen?zaak={visible_zaak['url']}", json=[status1])
        m.get(f"{ZAKEN_ROOT}statussen?zaak={secret_zaak['url']}", json=[status2])
        m.get(f"{ZAKEN_ROOT}zaken/1/rollen", json=[])
        m.get(f"{ZAKEN_ROOT}zaken/2/rollen", json=[])
        m.get(f"{ZAKEN_ROOT}resultaten?zaak={visible_zaak['url']}", json=[])
        m.get(f"{ZAKEN_ROOT}resultaten?zaak={secret_zaak['url']}", json=[])

        request = self._create_request()
        service = CaseListService.from_request(request)
        result = service.get_zaken()

        # Should have 1 visible and 1 skipped
        self.assertEqual(len(result.zaken), 1)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.total_fetched, 2)

        # Check visible zaak
        self.assertEqual(result.zaken[0].identification, "ZAAK-VISIBLE")

        # Check skipped zaak
        skipped = result.skipped[0]
        self.assertEqual(skipped.reason, SkipReason.NOT_VISIBLE)
        self.assertEqual(skipped.zaak.identification, "ZAAK-SECRET")

    def test_zakenresult_get_skip_statistics(self):
        """Test that ZakenResult.get_skip_statistics correctly counts skip reasons."""
        from open_inwoner.cms.cases.views.services import (
            SkippedZaak,
            ZaakWithApiGroup,
        )
        from open_inwoner.openzaak.constants import TypeAanvraag

        # Create mock skipped zaken
        mock_zaak1 = Mock()
        mock_zaak1.identificatie = "ZAAK-1"

        mock_zaak2 = Mock()
        mock_zaak2.identificatie = "ZAAK-2"

        mock_zaak3 = Mock()
        mock_zaak3.identificatie = "ZAAK-3"

        zaak_with_group1 = ZaakWithApiGroup(
            zaak=mock_zaak1,
            api_group=self.api_group,
            type_aanvraag=TypeAanvraag.ZAAK,
        )
        zaak_with_group2 = ZaakWithApiGroup(
            zaak=mock_zaak2,
            api_group=self.api_group,
            type_aanvraag=TypeAanvraag.ZAAK,
        )
        zaak_with_group3 = ZaakWithApiGroup(
            zaak=mock_zaak3,
            api_group=self.api_group,
            type_aanvraag=TypeAanvraag.ZAAK,
        )

        skipped = [
            SkippedZaak(
                zaak=zaak_with_group1,
                reason=SkipReason.NOT_VISIBLE,
                details="Test 1",
            ),
            SkippedZaak(
                zaak=zaak_with_group2,
                reason=SkipReason.NOT_VISIBLE,
                details="Test 2",
            ),
            SkippedZaak(
                zaak=zaak_with_group3,
                reason=SkipReason.RESOLUTION_FAILED,
                details="Test 3",
            ),
        ]

        result = ZakenResult(zaken=[], skipped=skipped)
        stats = result.get_skip_statistics()

        # Check statistics
        self.assertEqual(stats[SkipReason.NOT_VISIBLE], 2)
        self.assertEqual(stats[SkipReason.RESOLUTION_FAILED], 1)
        self.assertEqual(stats[SkipReason.TIMEOUT], 0)

    def test_zakenresult_total_fetched_property(self):
        """Test that ZakenResult.total_fetched correctly sums visible and skipped."""
        from open_inwoner.cms.cases.views.services import (
            SkippedZaak,
            ZaakWithApiGroup,
        )
        from open_inwoner.openzaak.constants import TypeAanvraag

        mock_zaak1 = Mock()
        mock_zaak2 = Mock()
        mock_zaak3 = Mock()

        zaak_with_group1 = ZaakWithApiGroup(
            zaak=mock_zaak1,
            api_group=self.api_group,
            type_aanvraag=TypeAanvraag.ZAAK,
        )
        zaak_with_group2 = ZaakWithApiGroup(
            zaak=mock_zaak2,
            api_group=self.api_group,
            type_aanvraag=TypeAanvraag.ZAAK,
        )

        skipped_zaak = SkippedZaak(
            zaak=zaak_with_group1,
            reason=SkipReason.NOT_VISIBLE,
        )

        result = ZakenResult(
            zaken=[zaak_with_group2, zaak_with_group1],
            skipped=[skipped_zaak],
        )

        self.assertEqual(result.total_fetched, 3)
        self.assertEqual(len(result.zaken), 2)
        self.assertEqual(len(result.skipped), 1)
