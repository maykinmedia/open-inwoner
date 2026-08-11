from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.test import RequestFactory, TestCase, override_settings

import requests_mock as requests_mock_module
from zgw_consumers.api_models.base import factory as zgw_factory
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.accounts.user_identification import BSNIdentification
from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.constants import TypeAanvraag
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.services import ZaakWithApiGroup, ZakenResult, ZGWService
from open_inwoner.openzaak.tasks import _warm_single_zaak, warm_cache_for_user
from open_inwoner.utils.test import ClearCachesMixin, paginated_response

from .factories import ZGWApiGroupConfigFactory
from .helpers import generate_oas_component_cached
from .shared import CATALOGI_ROOT, ZAKEN_ROOT

BSN = "900222086"
IDENTIFICATION = BSNIdentification(bsn=BSN)

ZAAK_UUID = "a8c8bc90-defa-4cf4-9c9a-1b3b8af8f0d1"
ZAAK_URL = f"{ZAKEN_ROOT}zaken/{ZAAK_UUID}"
STATUS_URL = f"{ZAKEN_ROOT}statussen/1e5e8af8-8f0d-4cf4-9c9a-a8c8bc90defa"
ZAAKTYPE_URL = f"{CATALOGI_ROOT}zaaktypen/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
STATUSTYPE_URL = f"{CATALOGI_ROOT}statustypen/11111111-2222-3333-4444-555555555555"

ZAAK_UUID_2 = "b9d9cd91-efab-5d07-ad0b-c2c9cf001e2f"
ZAAK_URL_2 = f"{ZAKEN_ROOT}zaken/{ZAAK_UUID_2}"
STATUS_URL_2 = f"{ZAKEN_ROOT}statussen/2f6f9bf9-9f1e-5df5-0d0b-b9d9cd91efab"


def _make_zaak_dict(zaak_url, zaak_uuid, status_url):
    return generate_oas_component_cached(
        "zrc",
        "schemas/Zaak",
        url=zaak_url,
        uuid=zaak_uuid,
        zaaktype=ZAAKTYPE_URL,
        status=status_url,
        resultaat=None,
        einddatum=None,
        vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
    )


def _make_status_dict(status_url, zaak_url):
    return generate_oas_component_cached(
        "zrc",
        "schemas/Status",
        url=status_url,
        zaak=zaak_url,
        statustype=STATUSTYPE_URL,
        datumStatusGezet="2024-01-01",
    )


def _register_zaak_resources(m, zaak_dict, status_dict):
    zaaktype = generate_oas_component_cached(
        "ztc", "schemas/ZaakType", url=ZAAKTYPE_URL
    )
    statustype = generate_oas_component_cached(
        "ztc", "schemas/StatusType", url=STATUSTYPE_URL, zaaktype=ZAAKTYPE_URL
    )
    m.get(ZAAKTYPE_URL, json=zaaktype)
    m.get(STATUSTYPE_URL, json=statustype)
    m.get(zaak_dict["status"], json=status_dict)
    m.get(zaak_dict["url"], json=zaak_dict)
    m.get(f"{ZAKEN_ROOT}rollen?zaak={zaak_dict['url']}", json=paginated_response([]))
    m.get(
        f"{ZAKEN_ROOT}statussen?zaak={zaak_dict['url']}",
        json={"results": [status_dict]},
    )


class ZgwCachingUnitTest(ClearCachesMixin, TestCase):
    """
    Tests for _warm_single_zaak called synchronously (no threading).

    Verifies that all per-zaak resources are fetched via HTTP on the first call,
    and that a second call for the same zaak makes no further HTTP requests
    because all results are now cached.
    """

    def setUp(self):
        super().setUp()
        self.api_group = ZGWApiGroupConfigFactory(
            zrc_service__api_root=ZAKEN_ROOT,
            ztc_service__api_root=CATALOGI_ROOT,
        )
        config = OpenZaakConfig.get_solo()
        config.zaak_max_confidentiality = VertrouwelijkheidsAanduidingen.openbaar
        config.save()
        self.zaken_client = ZGWService._zaken_client_factory(self.api_group)
        self.catalogi_client = ZGWService._catalogi_client_factory(self.api_group)
        self.use_rsin = self.api_group.fetch_eherkenning_zaken_with_rsin

    def _warm(self, zaak_dict):
        zaak = zgw_factory(Zaak, zaak_dict)
        _warm_single_zaak(
            zaak,
            self.zaken_client,
            self.catalogi_client,
            self.use_rsin,
            IDENTIFICATION,
        )

    @requests_mock_module.Mocker()
    def test_per_zaak_resources_are_cached_after_warm(self, m):
        zaak_dict = _make_zaak_dict(ZAAK_URL, ZAAK_UUID, STATUS_URL)
        status_dict = _make_status_dict(STATUS_URL, ZAAK_URL)
        _register_zaak_resources(m, zaak_dict, status_dict)

        self._warm(zaak_dict)

        calls_after_warmup = len(m.request_history)
        self.assertGreater(calls_after_warmup, 0)

        # Second call must make zero new HTTP requests: everything is cached
        self._warm(zaak_dict)

        self.assertEqual(len(m.request_history), calls_after_warmup)

    @requests_mock_module.Mocker()
    def test_shared_zaaktype_fetched_once_for_two_zaken(self, m):
        zaak1_dict = _make_zaak_dict(ZAAK_URL, ZAAK_UUID, STATUS_URL)
        zaak2_dict = _make_zaak_dict(ZAAK_URL_2, ZAAK_UUID_2, STATUS_URL_2)
        status1_dict = _make_status_dict(STATUS_URL, ZAAK_URL)
        status2_dict = _make_status_dict(STATUS_URL_2, ZAAK_URL_2)
        _register_zaak_resources(m, zaak1_dict, status1_dict)
        _register_zaak_resources(m, zaak2_dict, status2_dict)

        self._warm(zaak1_dict)
        self._warm(zaak2_dict)

        zaaktype_calls = [r for r in m.request_history if r.url == ZAAKTYPE_URL]
        self.assertEqual(
            len(zaaktype_calls), 1, "zaaktype should be fetched once and cached"
        )

    @requests_mock_module.Mocker()
    def test_zaken_list_cached_with_correct_key(self, m):
        """
        Verify that a second fetch_zaken_by_bsn with the same arguments makes no new
        HTTP requests. The pagination bound is client state rather than an argument,
        so there is nothing a caller could pass that would move it to another key.
        """
        zaak_dict = _make_zaak_dict(ZAAK_URL, ZAAK_UUID, STATUS_URL)
        m.get(
            f"{ZAKEN_ROOT}zaken"
            f"?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn={BSN}"
            f"&maximaleVertrouwelijkheidaanduiding={OpenZaakConfig.get_solo().zaak_max_confidentiality}",
            json=paginated_response([zaak_dict]),
        )

        zaken_client = ZGWService._zaken_client_factory(self.api_group)
        zaken_client.fetch_zaken_by_bsn(BSN)

        calls_after_first = len(m.request_history)
        self.assertGreater(calls_after_first, 0)

        zaken_client.fetch_zaken_by_bsn(BSN)

        self.assertEqual(len(m.request_history), calls_after_first)

    @requests_mock_module.Mocker()
    def test_pagination_bound_is_part_of_the_zaken_cache_key(self, m):
        """Raising the bound must not serve a listing collected under the old one.

        The cached listing is only as complete as the bound it was collected with, so
        an operator raising `ZGW_MAX_REQUESTS` has to get a deeper listing rather than
        the truncated entry that is already there.
        """
        shallow = ZGWService._zaken_client_factory(self.api_group)
        with override_settings(ZGW_MAX_REQUESTS=settings.ZGW_MAX_REQUESTS + 1):
            deeper = ZGWService._zaken_client_factory(self.api_group)

        self.assertNotEqual(
            shallow.fetch_zaken_by_bsn.cache_key(shallow, BSN),
            deeper.fetch_zaken_by_bsn.cache_key(deeper, BSN),
        )

    @requests_mock_module.Mocker()
    def test_openzaak_120_params_are_part_of_the_company_cache_key(self, m):
        """Switching parameter style must not serve entries from the other style.

        `use_openzaak_120_params` decides which rol query parameters are sent, so the
        two styles are different questions and can return different zaken.
        """
        self.api_group.fetch_eherkenning_zaken_with_openzaak_120_params = False
        self.api_group.save()
        legacy = ZGWService._zaken_client_factory(self.api_group)

        self.api_group.fetch_eherkenning_zaken_with_openzaak_120_params = True
        self.api_group.save()
        current = ZGWService._zaken_client_factory(self.api_group)

        self.assertNotEqual(
            legacy.fetch_zaken_for_company.cache_key(legacy, kvk_or_rsin="12345678"),
            current.fetch_zaken_for_company.cache_key(current, kvk_or_rsin="12345678"),
        )


class ZgwCachingIntegrationTest(ClearCachesMixin, TestCase):
    """
    Integration test covering the full signal -> task -> cache chain.

    warm_cache_for_user.delay is patched to call the underlying run() directly,
    bypassing QueueOnce (which requires Redis) while still exercising the full
    task body. Threads spawned by parallel() make no DB queries (clients are
    pre-built in the main thread), so TestCase is sufficient.
    """

    def setUp(self):
        super().setUp()
        self.api_group = ZGWApiGroupConfigFactory(
            zrc_service__api_root=ZAKEN_ROOT,
            ztc_service__api_root=CATALOGI_ROOT,
        )
        config = OpenZaakConfig.get_solo()
        config.zaak_max_confidentiality = VertrouwelijkheidsAanduidingen.openbaar
        config.save()

    @requests_mock_module.Mocker()
    def test_login_seeds_zgw_cache_for_bsn_user(self, m):
        zaak_dict = _make_zaak_dict(ZAAK_URL, ZAAK_UUID, STATUS_URL)
        status_dict = _make_status_dict(STATUS_URL, ZAAK_URL)
        _register_zaak_resources(m, zaak_dict, status_dict)
        m.get(
            f"{ZAKEN_ROOT}zaken"
            f"?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn={BSN}"
            f"&maximaleVertrouwelijkheidaanduiding={OpenZaakConfig.get_solo().zaak_max_confidentiality}",
            json=paginated_response([zaak_dict]),
        )

        user = DigidUserFactory(bsn=BSN)
        request = RequestFactory().get("/")
        request.user = user

        with patch.object(
            warm_cache_for_user,
            "apply_async",
            side_effect=lambda *args, **kwargs: warm_cache_for_user.run(
                **kwargs["kwargs"]
            ),
        ):
            user_logged_in.send(sender=None, request=request, user=user)

        calls_after_login = len(m.request_history)
        self.assertGreater(calls_after_login, 0, "no HTTP calls made during warm-up")

        # Client calls that the case list view makes must now be served from cache
        zaken_client = ZGWService._zaken_client_factory(self.api_group)
        catalogi_client = ZGWService._catalogi_client_factory(self.api_group)

        zaken_client.fetch_zaken_by_bsn(BSN)
        status = zaken_client.fetch_single_status(STATUS_URL)
        catalogi_client.fetch_single_zaaktype(ZAAKTYPE_URL)
        catalogi_client.fetch_single_status_type(status.statustype)

        self.assertEqual(
            len(m.request_history),
            calls_after_login,
            "client methods made HTTP requests that should have been cached after login",
        )


class WarmCacheForUserIncompleteFetchLoggingTests(ClearCachesMixin, TestCase):
    """
    A raw fetch that timed out or errored for some/all groups must be visible
    in the logs: silently proceeding as if nothing was wrong would hide the
    exact kind of failure #2735 was about.
    """

    def setUp(self):
        super().setUp()
        self.api_group = ZGWApiGroupConfigFactory(
            zrc_service__api_root=ZAKEN_ROOT,
            ztc_service__api_root=CATALOGI_ROOT,
        )

    def test_warns_when_incomplete_raw_fetch_finds_no_zaken(self):
        with (
            patch.object(
                ZGWService,
                "get_raw_zaken",
                return_value=ZakenResult(
                    zaken=[], skipped=[], raw_fetch_incomplete=True
                ),
            ),
            self.assertLogs("open_inwoner.openzaak.tasks", level="WARNING") as cm,
        ):
            warm_cache_for_user.run(user_bsn=BSN)

        self.assertTrue(
            any("unable to determine whether zaken exist" in msg for msg in cm.output)
        )

    def test_logs_info_when_complete_raw_fetch_finds_no_zaken(self):
        with (
            patch.object(
                ZGWService,
                "get_raw_zaken",
                return_value=ZakenResult(zaken=[], skipped=[]),
            ),
            self.assertLogs("open_inwoner.openzaak.tasks", level="INFO") as cm,
        ):
            warm_cache_for_user.run(user_bsn=BSN)

        self.assertTrue(any("no zaken found" in msg for msg in cm.output))
        self.assertFalse(any(msg.startswith("WARNING") for msg in cm.output))

    @requests_mock_module.Mocker()
    def test_warns_but_still_warms_cache_when_raw_fetch_is_partially_incomplete(
        self, m
    ):
        """
        Zaken that WERE fetched must not be discarded just because some
        other group in the same fetch timed out or errored.
        """
        zaak_dict = _make_zaak_dict(ZAAK_URL, ZAAK_UUID, STATUS_URL)
        status_dict = _make_status_dict(STATUS_URL, ZAAK_URL)
        _register_zaak_resources(m, zaak_dict, status_dict)

        zaak = zgw_factory(Zaak, zaak_dict)
        zaak_with_group = ZaakWithApiGroup(
            zaak=zaak, api_group=self.api_group, type_aanvraag=TypeAanvraag.ZAAK
        )

        with (
            patch.object(
                ZGWService,
                "get_raw_zaken",
                return_value=ZakenResult(
                    zaken=[zaak_with_group], skipped=[], raw_fetch_incomplete=True
                ),
            ),
            self.assertLogs("open_inwoner.openzaak.tasks", level="WARNING") as cm,
        ):
            warm_cache_for_user.run(user_bsn=BSN)

        self.assertTrue(
            any("some zaken may not have been found" in msg for msg in cm.output)
        )
        self.assertGreater(
            len(m.request_history),
            0,
            "the zaak that was fetched should still have been warmed",
        )
