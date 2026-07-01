import threading
from unittest.mock import Mock, patch

from django.test import TestCase

import requests_mock as requests_mock_module

from open_inwoner.accounts.user_identification import BSNIdentification
from open_inwoner.openzaak.constants import TypeAanvraag
from open_inwoner.openzaak.services import ZaakWithApiGroup, ZGWService
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.openzaak.tests.shared import ANOTHER_ZAKEN_ROOT, ZAKEN_ROOT
from open_inwoner.utils.test import ClearCachesMixin

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
