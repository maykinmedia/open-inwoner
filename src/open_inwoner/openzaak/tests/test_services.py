import threading
from unittest.mock import Mock, patch

from django.test import TestCase

import requests_mock as requests_mock_module
from furl import furl
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)

from open_inwoner.accounts.user_identification import BSNIdentification
from open_inwoner.openzaak.api_models import Rol
from open_inwoner.openzaak.constants import TypeAanvraag, ZaakBetrokkeneRol
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.services import ZaakWithApiGroup, ZGWService
from open_inwoner.openzaak.tests.factories import (
    ZGWApiGroupConfigFactory,
    generate_rol,
)
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.openzaak.tests.shared import (
    ANOTHER_ZAKEN_ROOT,
    CATALOGI_ROOT,
    ZAKEN_ROOT,
)
from open_inwoner.utils.test import ClearCachesMixin, paginated_response

_USER_IDENTIFICATION = BSNIdentification(bsn="900222086")

_TINY_TIMEOUTS = {
    "get_raw_zaken": 0.001,
    "get_visible_zaken": 0.001,
    "fully_resolve_zaken": 0.001,
    "get_formulieren": 0.001,
}


class TimeoutHandlingTests(ClearCachesMixin, TestCase):
    """
    Verify that the timeout on as_completed() fires while futures are still
    pending (i.e. as_completed runs INSIDE the with parallel() block).

    With the old code structure, as_completed was called OUTSIDE the parallel
    block. parallel.__exit__ calls shutdown(wait=True), which drains all futures
    before as_completed ever runs. This means no natural TimeoutError could fire
    and the warning was never logged.

    Each test blocks a fetch with a threading.Event and sets a 1 ms timeout.
    A timer releases the event after 50 ms so shutdown(wait=True) does not hang.
    With the old code the timeout fires too late (all futures already done) and
    assertLogs finds no warning -> test fails.  With the new code the timeout
    fires after 1 ms while the future is still blocked → warning is logged ->
    test passes.
    """

    def setUp(self):
        self.api_group = ZGWApiGroupConfigFactory()
        self.service = ZGWService()

    def _make_blocking_fetch(self, release: threading.Event):
        def fetch(*args, **kwargs):
            release.wait(timeout=5)
            return []

        return fetch

    def test_get_raw_zaken_logs_timeout_warning(self):
        release = threading.Event()
        timer = threading.Timer(0.05, release.set)

        with (
            patch.object(
                self.service,
                "_get_raw_zaken_for_api_group",
                side_effect=self._make_blocking_fetch(release),
            ),
            patch.object(
                ZGWService, "_case_list_stage_timeouts", return_value=_TINY_TIMEOUTS
            ),
        ):
            timer.start()
            try:
                with self.assertLogs(
                    "open_inwoner.openzaak.services", level="WARNING"
                ) as cm:
                    result = self.service.get_raw_zaken(_USER_IDENTIFICATION)
            finally:
                release.set()
                timer.cancel()

        self.assertEqual(result, [])
        self.assertTrue(any("Timed out fetching raw zaken" in msg for msg in cm.output))

    def test_get_visible_zaken_logs_timeout_warning_on_raw_fetch(self):
        release = threading.Event()
        timer = threading.Timer(0.05, release.set)

        with (
            patch.object(
                self.service,
                "_get_raw_zaken_for_api_group",
                side_effect=self._make_blocking_fetch(release),
            ),
            patch.object(
                ZGWService, "_case_list_stage_timeouts", return_value=_TINY_TIMEOUTS
            ),
        ):
            timer.start()
            try:
                with self.assertLogs(
                    "open_inwoner.openzaak.services", level="WARNING"
                ) as cm:
                    result = self.service.get_visible_zaken(_USER_IDENTIFICATION)
            finally:
                release.set()
                timer.cancel()

        self.assertEqual(result.zaken, [])
        self.assertTrue(any("Timed out fetching raw zaken" in msg for msg in cm.output))

    def test_get_formulieren_logs_timeout_warning(self):
        release = threading.Event()
        timer = threading.Timer(0.05, release.set)

        with (
            patch.object(
                self.service,
                "_get_formulieren_for_api_group",
                side_effect=self._make_blocking_fetch(release),
            ),
            patch.object(
                ZGWService, "_case_list_stage_timeouts", return_value=_TINY_TIMEOUTS
            ),
        ):
            timer.start()
            try:
                with self.assertLogs(
                    "open_inwoner.openzaak.services", level="WARNING"
                ) as cm:
                    result = self.service.get_formulieren(_USER_IDENTIFICATION)
            finally:
                release.set()
                timer.cancel()

        self.assertEqual(result, [])
        self.assertTrue(
            any("Timeout while fetching formulieren" in msg for msg in cm.output)
        )


_ZAAK_UUID = "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"
_ZAAK_IDENTIFICATIE = "ZAAK-2022-0000000024"


@requests_mock_module.Mocker()
class GetZaakByUuidTests(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.api_group_1 = ZGWApiGroupConfigFactory(
            zrc_service__api_root=ZAKEN_ROOT, form_service=None
        )
        self.api_group_2 = ZGWApiGroupConfigFactory(
            zrc_service__api_root=ANOTHER_ZAKEN_ROOT, form_service=None
        )
        self.service = ZGWService()
        self.zaak_data = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/{_ZAAK_UUID}",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Test zaak",
            startdatum="2022-01-02",
            einddatum=None,
        )

    def test_returns_zaak_when_found_in_one_group(self, m):
        m.get(f"{ZAKEN_ROOT}zaken/{_ZAAK_UUID}", json=self.zaak_data)
        m.get(f"{ANOTHER_ZAKEN_ROOT}zaken/{_ZAAK_UUID}", status_code=404)

        result = self.service.get_zaak_by_uuid(_ZAAK_UUID)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, ZaakWithApiGroup)
        self.assertEqual(result.api_group, self.api_group_1)
        self.assertEqual(result.type_aanvraag, TypeAanvraag.ZAAK)

    def test_returns_none_when_all_groups_return_404(self, m):
        m.get(f"{ZAKEN_ROOT}zaken/{_ZAAK_UUID}", status_code=404)
        m.get(f"{ANOTHER_ZAKEN_ROOT}zaken/{_ZAAK_UUID}", status_code=404)

        with self.assertNoLogs("open_inwoner.openzaak.services", level="WARNING"):
            result = self.service.get_zaak_by_uuid(_ZAAK_UUID)

        self.assertIsNone(result)

    def test_logs_warning_for_non_404_client_error(self, m):
        m.get(f"{ZAKEN_ROOT}zaken/{_ZAAK_UUID}", status_code=403)
        m.get(f"{ANOTHER_ZAKEN_ROOT}zaken/{_ZAAK_UUID}", status_code=404)

        with self.assertLogs("open_inwoner.openzaak.services", level="WARNING") as cm:
            result = self.service.get_zaak_by_uuid(_ZAAK_UUID)

        self.assertIsNone(result)
        self.assertTrue(any("error fetching zaak by uuid" in msg for msg in cm.output))

    def test_logs_warning_for_server_error(self, m):
        m.get(f"{ZAKEN_ROOT}zaken/{_ZAAK_UUID}", status_code=500)
        m.get(f"{ANOTHER_ZAKEN_ROOT}zaken/{_ZAAK_UUID}", status_code=404)

        with self.assertLogs("open_inwoner.openzaak.services", level="WARNING") as cm:
            result = self.service.get_zaak_by_uuid(_ZAAK_UUID)

        self.assertIsNone(result)
        self.assertTrue(any("error fetching zaak by uuid" in msg for msg in cm.output))

    def test_logs_warning_and_returns_first_when_found_in_multiple_groups(self, m):
        zaak_data_2 = {
            **self.zaak_data,
            "url": f"{ANOTHER_ZAKEN_ROOT}zaken/{_ZAAK_UUID}",
        }
        m.get(f"{ZAKEN_ROOT}zaken/{_ZAAK_UUID}", json=self.zaak_data)
        m.get(f"{ANOTHER_ZAKEN_ROOT}zaken/{_ZAAK_UUID}", json=zaak_data_2)

        with self.assertLogs("open_inwoner.openzaak.services", level="WARNING") as cm:
            result = self.service.get_zaak_by_uuid(_ZAAK_UUID)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, ZaakWithApiGroup)
        self.assertTrue(
            any("zaak found in multiple API groups" in msg for msg in cm.output)
        )

    def test_logs_warning_on_timeout(self, m):
        release = threading.Event()
        timer = threading.Timer(0.05, release.set)

        mock_client = Mock()
        mock_client.fetch_single_zaak.side_effect = lambda *a, **kw: release.wait(
            timeout=5
        )

        with (
            patch.object(
                self.service, "_zaken_client_factory", return_value=mock_client
            ),
            patch(
                "open_inwoner.openzaak.services.OpenZaakConfig.get_solo",
                return_value=Mock(case_list_fetch_timeout=0.001),
            ),
        ):
            timer.start()
            try:
                with self.assertLogs(
                    "open_inwoner.openzaak.services", level="WARNING"
                ) as cm:
                    result = self.service.get_zaak_by_uuid(_ZAAK_UUID)
            finally:
                release.set()
                timer.cancel()

        self.assertIsNone(result)
        self.assertTrue(
            any("timed out fetching zaak by uuid" in msg for msg in cm.output)
        )


class UserHasRequiredRolTest(TestCase):
    """
    Unit tests for the shared rol predicate used by both `search_zaken` and
    `check_zaak_access`.
    """

    def setUp(self):
        super().setUp()
        self.zaak_url = f"{ZAKEN_ROOT}zaken/{_ZAAK_UUID}"

    @staticmethod
    def _client_returning(rollen: list[Rol]) -> Mock:
        client = Mock()
        client.fetch_rollen_for_user.return_value = rollen
        return client

    @staticmethod
    def _rol(description: str) -> Rol:
        return generate_rol(
            RolTypes.natuurlijk_persoon,
            {"inpBsn": _USER_IDENTIFICATION.bsn},
            description=description,
        )

    def test_denies_when_user_has_no_rollen(self):
        result = ZGWService._user_has_required_rol(
            self.zaak_url,
            _USER_IDENTIFICATION,
            self._client_returning([]),
            use_rsin=False,
            limit_access_to_role=RolOmschrijving.initiator,
        )

        self.assertFalse(result)

    def test_denies_when_user_has_no_rollen_and_no_limit_configured(self):
        result = ZGWService._user_has_required_rol(
            self.zaak_url,
            _USER_IDENTIFICATION,
            self._client_returning([]),
            use_rsin=False,
            limit_access_to_role="",
        )

        self.assertFalse(result)

    def test_allows_any_rol_when_no_limit_configured(self):
        for description in RolOmschrijving.values:
            with self.subTest(rol_omschrijving=description):
                result = ZGWService._user_has_required_rol(
                    self.zaak_url,
                    _USER_IDENTIFICATION,
                    self._client_returning([self._rol(description)]),
                    use_rsin=False,
                    limit_access_to_role="",
                )

                self.assertTrue(result)

    def test_denies_when_rol_does_not_match_limit(self):
        non_initiator_rollen = [
            rol
            for rol in RolOmschrijving.values
            if rol != RolOmschrijving.initiator.value
        ]

        for description in non_initiator_rollen:
            with self.subTest(rol_omschrijving=description):
                result = ZGWService._user_has_required_rol(
                    self.zaak_url,
                    _USER_IDENTIFICATION,
                    self._client_returning([self._rol(description)]),
                    use_rsin=False,
                    limit_access_to_role=RolOmschrijving.initiator,
                )

                self.assertFalse(result)

    def test_allows_when_one_of_multiple_rollen_matches_limit(self):
        rollen = [
            self._rol(RolOmschrijving.behandelaar),
            self._rol(RolOmschrijving.initiator),
        ]

        result = ZGWService._user_has_required_rol(
            self.zaak_url,
            _USER_IDENTIFICATION,
            self._client_returning(rollen),
            use_rsin=False,
            limit_access_to_role=RolOmschrijving.initiator,
        )

        self.assertTrue(result)

    def test_use_rsin_is_passed_to_client(self):
        client = self._client_returning([self._rol(RolOmschrijving.initiator)])

        ZGWService._user_has_required_rol(
            self.zaak_url,
            _USER_IDENTIFICATION,
            client,
            use_rsin=True,
            limit_access_to_role="",
        )

        client.fetch_rollen_for_user.assert_called_once_with(
            self.zaak_url, _USER_IDENTIFICATION, use_rsin=True
        )

    def test_does_not_log_user_identification(self):
        with self.assertLogs("open_inwoner.openzaak.services", level="INFO") as cm:
            ZGWService._user_has_required_rol(
                self.zaak_url,
                _USER_IDENTIFICATION,
                self._client_returning([]),
                use_rsin=False,
                limit_access_to_role="",
            )

        self.assertFalse(any(_USER_IDENTIFICATION.bsn in msg for msg in cm.output))


@requests_mock_module.Mocker()
class SearchZakenAccessTest(ClearCachesMixin, TestCase):
    """
    `search_zaken` must not disclose zaken the user has no (sufficient) rol on.

    Regression tests for the metadata leak found during triage of #2659: searching on
    an exact zaaknummer bypassed the rol check that the case detail page does enforce.
    """

    maxDiff = None

    def setUp(self):
        super().setUp()
        self.api_group = ZGWApiGroupConfigFactory(
            zrc_service__api_root=ZAKEN_ROOT,
            ztc_service__api_root=CATALOGI_ROOT,
            form_service=None,
            fetch_eherkenning_zaken_with_rsin=False,
        )
        self.service = ZGWService()

        self.config = OpenZaakConfig.get_solo()
        self.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.limit_user_visible_cases_to_role = ZaakBetrokkeneRol.initiator
        self.config.save()

        self.zaaktype = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/0caa29d4-b7ec-4d0b-93f6-b6c0dc1c1b53",
            indicatieInternOfExtern="extern",
        )
        self.zaak = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/{_ZAAK_UUID}",
            zaaktype=self.zaaktype["url"],
            identificatie=_ZAAK_IDENTIFICATIE,
            omschrijving="Geheime omschrijving",
            status=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )

    def _mock_zaken_search(self, m, zaken: list[dict], zaken_root: str = ZAKEN_ROOT):
        params = {
            "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": (
                _USER_IDENTIFICATION.bsn
            ),
            "maximaleVertrouwelijkheidaanduiding": (
                VertrouwelijkheidsAanduidingen.beperkt_openbaar
            ),
            "identificatie": _ZAAK_IDENTIFICATIE,
        }
        # the client only sends the rol filter when the config is set, so the mock
        # must match that exactly, otherwise a test can pass vacuously on a
        # non-matching URL
        if self.config.limit_user_visible_cases_to_role:
            params["rol__omschrijvingGeneriek"] = (
                self.config.limit_user_visible_cases_to_role
            )

        m.get(
            furl(f"{zaken_root}zaken").add(params).url,
            json=paginated_response(zaken),
        )

    def _mock_rollen(self, m, rollen: list[dict], zaken_root: str = ZAKEN_ROOT):
        m.get(
            f"{zaken_root}rollen?zaak={self.zaak['url']}",
            json=paginated_response(rollen),
        )

    def _rol_component(self, description: str) -> dict:
        return generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/bb353aa-ad2c-4a07-ae75-15add5823",
            omschrijvingGeneriek=description,
            betrokkeneType=RolTypes.natuurlijk_persoon,
            betrokkeneIdentificatie={"inpBsn": _USER_IDENTIFICATION.bsn},
        )

    def test_returns_zaak_when_user_has_matching_rol(self, m):
        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        self._mock_rollen(m, [self._rol_component(RolOmschrijving.initiator)])

        results = self.service.search_zaken(_USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].zaak.identificatie, _ZAAK_IDENTIFICATIE)
        self.assertEqual(results[0].api_group, self.api_group)

    def test_excludes_zaak_when_user_has_no_rol(self, m):
        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        self._mock_rollen(m, [])

        results = self.service.search_zaken(_USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE)

        self.assertEqual(results, [])

    def test_excludes_zaak_when_rol_does_not_match_configured_limit(self, m):
        non_initiator_rollen = [
            rol
            for rol in RolOmschrijving.values
            if rol != RolOmschrijving.initiator.value
        ] + [""]

        for description in non_initiator_rollen:
            with self.subTest(rol_omschrijving=description):
                self.clear_caches()
                m.reset_mock()
                self._mock_zaken_search(m, [self.zaak])
                m.get(self.zaaktype["url"], json=self.zaaktype)
                self._mock_rollen(m, [self._rol_component(description)])

                results = self.service.search_zaken(
                    _USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE
                )

                self.assertEqual(results, [])

    def test_returns_zaak_for_any_rol_when_no_limit_configured(self, m):
        """Guard against over-filtering when the config is left blank."""
        self.config.limit_user_visible_cases_to_role = ""
        self.config.save()

        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        self._mock_rollen(m, [self._rol_component(RolOmschrijving.belanghebbende)])

        results = self.service.search_zaken(_USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE)

        self.assertEqual(len(results), 1)

    def test_excludes_zaak_without_any_rol_when_no_limit_configured(self, m):
        """Matches the `check_zaak_access` gate: some rol is always required."""
        self.config.limit_user_visible_cases_to_role = ""
        self.config.save()

        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        self._mock_rollen(m, [])

        results = self.service.search_zaken(_USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE)

        self.assertEqual(results, [])

    def test_excludes_zaak_when_rollen_fetch_fails(self, m):
        """Fail closed: an indeterminate authorization answer must deny."""
        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}", status_code=500)

        with self.assertLogs("open_inwoner.openzaak.services", level="WARNING") as cm:
            results = self.service.search_zaken(
                _USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE
            )

        self.assertEqual(results, [])
        self.assertTrue(
            any("Unable to fetch rollen for search result" in msg for msg in cm.output)
        )

    def test_does_not_resolve_zaaktype_when_rol_check_fails(self, m):
        """No metadata is resolved for a zaak the user has no claim to."""
        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        self._mock_rollen(m, [self._rol_component(RolOmschrijving.belanghebbende)])

        self.service.search_zaken(_USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE)

        requested = [req.url for req in m.request_history]
        self.assertNotIn(self.zaaktype["url"], requested)
