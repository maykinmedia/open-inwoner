import threading
from datetime import date
from unittest.mock import Mock, patch

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

import requests_mock as requests_mock_module
from furl import furl
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)

from open_inwoner.accounts.user_identification import BSNIdentification
from open_inwoner.openzaak.api_models import Rol, Zaak, ZaakType
from open_inwoner.openzaak.constants import TypeAanvraag, ZaakBetrokkeneRol
from open_inwoner.openzaak.exceptions import ZgwAPIError
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.services import (
    FormulierenResult,
    SkippedZaak,
    SkipReason,
    ZaakResolutionError,
    ZaakWithApiGroup,
    ZaakWithApiGroupZaakTypeResolved,
    ZakenResult,
    ZGWService,
)
from open_inwoner.openzaak.tests.factories import (
    CatalogusConfigFactory,
    ZaakTypeConfigFactory,
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


class IncompleteZakenResultTest(ClearCachesMixin, TestCase):
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

        self.assertEqual(result.zaken, [])
        self.assertTrue(result.raw_fetch_incomplete)
        self.assertTrue(result.is_incomplete)
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
        self.assertTrue(result.raw_fetch_incomplete)
        self.assertTrue(result.is_incomplete)
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

        self.assertEqual(result.formulieren, [])
        self.assertTrue(result.timed_out)
        self.assertTrue(
            any("Timeout while fetching formulieren" in msg for msg in cm.output)
        )

    def test_search_zaken_propagates_raw_fetch_timeout(self):
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
                result = self.service.search_zaken(
                    _USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE
                )
            finally:
                release.set()
                timer.cancel()

        self.assertEqual(result.zaken, [])
        self.assertTrue(result.raw_fetch_incomplete)
        self.assertTrue(result.is_incomplete)

    def _make_zaak_with_group(self, uuid: str) -> ZaakWithApiGroup:
        zaak = factory(
            Zaak,
            generate_oas_component_cached(
                "zrc",
                "schemas/Zaak",
                url=f"{ZAKEN_ROOT}zaken/{uuid}",
                zaaktype=f"{CATALOGI_ROOT}zaaktypen/{uuid}",
                startdatum="2024-01-02",
                einddatum=None,
                status=f"{ZAKEN_ROOT}statussen/{uuid}",
                resultaat=None,
            ),
        )
        return ZaakWithApiGroup(
            zaak=zaak, api_group=self.api_group, type_aanvraag=TypeAanvraag.ZAAK
        )

    def test_get_visible_zaken_records_timeout_skips_for_zaaktype_stage(self):
        """The raw fetch succeeds, but resolving zaaktypen runs out of budget."""
        zaak_with_group = self._make_zaak_with_group(_ZAAK_UUID)
        release = threading.Event()
        timer = threading.Timer(0.05, release.set)

        timeouts = {**_TINY_TIMEOUTS, "get_raw_zaken": 5}

        with (
            patch.object(
                self.service,
                "_get_raw_zaken_for_api_group",
                return_value=[zaak_with_group],
            ),
            patch.object(
                self.service,
                "_resolve_zaak_type",
                side_effect=self._make_blocking_fetch(release),
            ),
            patch.object(
                ZGWService, "_case_list_stage_timeouts", return_value=timeouts
            ),
        ):
            timer.start()
            try:
                result = self.service.get_visible_zaken(_USER_IDENTIFICATION)
            finally:
                release.set()
                timer.cancel()

        self.assertEqual(result.zaken, [])
        self.assertFalse(result.raw_fetch_incomplete)
        self.assertEqual(
            [skipped.reasons for skipped in result.skipped],
            [frozenset({SkipReason.TIMEOUT})],
        )
        self.assertTrue(result.is_incomplete)

    def test_fully_resolve_zaken_records_timeout_skips(self):
        zaak_with_group = self._make_zaak_with_group(_ZAAK_UUID)
        release = threading.Event()
        timer = threading.Timer(0.05, release.set)

        with (
            patch.object(
                self.service,
                "_resolve_resultaat_and_resultaat_type",
                side_effect=self._make_blocking_fetch(release),
            ),
            patch.object(
                self.service,
                "_resolve_status_and_status_type",
                side_effect=self._make_blocking_fetch(release),
            ),
            patch.object(
                ZGWService, "_case_list_stage_timeouts", return_value=_TINY_TIMEOUTS
            ),
        ):
            timer.start()
            try:
                result = self.service.fully_resolve_zaken([zaak_with_group])
            finally:
                release.set()
                timer.cancel()

        self.assertEqual(result.zaken, [])
        self.assertEqual(
            [skipped.reasons for skipped in result.skipped],
            [frozenset({SkipReason.TIMEOUT})],
        )
        self.assertTrue(result.is_incomplete)

    def test_fully_resolve_zaken_keeps_failures_alongside_the_timeout(self):
        """A step that failed before the stage ran out of budget keeps its reason"""
        zaak_with_group = self._make_zaak_with_group(_ZAAK_UUID)
        release = threading.Event()
        timer = threading.Timer(0.05, release.set)

        with (
            patch.object(
                self.service,
                "_resolve_resultaat_and_resultaat_type",
                side_effect=ZaakResolutionError(
                    SkipReason.RESULTAAT_RESOLUTION_FAILED, "kapot"
                ),
            ),
            patch.object(
                self.service,
                "_resolve_status_and_status_type",
                side_effect=self._make_blocking_fetch(release),
            ),
            patch.object(
                ZGWService, "_case_list_stage_timeouts", return_value=_TINY_TIMEOUTS
            ),
        ):
            timer.start()
            try:
                result = self.service.fully_resolve_zaken([zaak_with_group])
            finally:
                release.set()
                timer.cancel()

        self.assertEqual(result.zaken, [])
        self.assertEqual(
            [skipped.reasons for skipped in result.skipped],
            [frozenset({SkipReason.TIMEOUT, SkipReason.RESULTAAT_RESOLUTION_FAILED})],
        )
        self.assertTrue(result.is_incomplete)

    def test_is_incomplete_is_false_for_legitimate_exclusions(self):
        """Permanent exclusions must not trigger the partial-results banner"""

        for reason in (
            SkipReason.NO_STATUS,
            SkipReason.NO_ZAAKTYPE,
            SkipReason.CONFIDENTIALITY_TOO_HIGH,
            SkipReason.INTERNAL_ZAAKTYPE,
            SkipReason.BEFORE_VISIBLE_FROM_DATE,
        ):
            with self.subTest(reason=reason):
                result = ZakenResult(
                    zaken=[],
                    skipped=[
                        SkippedZaak(
                            zaak_url=f"{ZAKEN_ROOT}zaken/{_ZAAK_UUID}",
                            reasons=frozenset({reason}),
                            api_group=self.api_group,
                        )
                    ],
                )
                self.assertFalse(result.is_incomplete)
                self.assertFalse(FormulierenResult(formulieren=[]).timed_out)

    def test_is_incomplete_is_true_for_transient_errors(self):
        """Resolution failures are counted as transient fetch errors"""

        self.assertEqual(
            SkipReason.transient_reasons(),
            SkipReason.resolution_failures() | {SkipReason.TIMEOUT},
        )

        for reason in SkipReason.transient_reasons():
            with self.subTest(reason=reason):
                result = ZakenResult(
                    zaken=[],
                    skipped=[
                        SkippedZaak(
                            zaak_url=f"{ZAKEN_ROOT}zaken/{_ZAAK_UUID}",
                            reasons=frozenset({reason}),
                            api_group=self.api_group,
                        )
                    ],
                )
                self.assertTrue(result.is_incomplete, msg=f"reason={reason}")


_ZAAK_UUID = "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"
_ZAAK_IDENTIFICATIE = "ZAAK-2022-0000000024"

_RESOLUTION_FAILURE_LOG = "Failed to resolve ZGW entity for zaak"
_UNEXPECTED_FAILURE_LOG = "Failed to resolve zaak for unexpected reason"


class ResolutionFailureTest(ClearCachesMixin, TestCase):
    """Every ZGW entity that fails to resolve is reported and logged on its own."""

    def setUp(self):
        super().setUp()
        self.api_group = ZGWApiGroupConfigFactory()
        self.service = ZGWService()
        self.zaken_client = Mock()
        self.catalogi_client = Mock()

    def _make_zaak(self, **overrides) -> ZaakWithApiGroupZaakTypeResolved:
        fields = {
            "url": f"{ZAKEN_ROOT}zaken/{_ZAAK_UUID}",
            "identificatie": _ZAAK_IDENTIFICATIE,
            "zaaktype": f"{CATALOGI_ROOT}zaaktypen/{_ZAAK_UUID}",
            "startdatum": "2024-01-02",
            "einddatum": None,
            "status": f"{ZAKEN_ROOT}statussen/{_ZAAK_UUID}",
            "resultaat": f"{ZAKEN_ROOT}resultaten/{_ZAAK_UUID}",
            **overrides,
        }
        zaak = factory(
            Zaak,
            generate_oas_component_cached("zrc", "schemas/Zaak", **fields),
        )
        return ZaakWithApiGroupZaakTypeResolved(
            zaak=zaak, api_group=self.api_group, type_aanvraag=TypeAanvraag.ZAAK
        )

    def _fully_resolve(self, zaak_with_group) -> ZakenResult:
        with (
            patch.object(
                self.service, "_zaken_client_factory", return_value=self.zaken_client
            ),
            patch.object(
                self.service,
                "_catalogi_client_factory",
                return_value=self.catalogi_client,
            ),
        ):
            return self.service.fully_resolve_zaken([zaak_with_group])

    def _assert_skipped_with_reasons(self, result: ZakenResult, *reasons: SkipReason):
        self.assertEqual(result.zaken, [])
        self.assertEqual(
            [skipped.reasons for skipped in result.skipped], [frozenset(reasons)]
        )
        self.assertTrue(result.is_incomplete)

    def test_status_fetch_failure_is_attributed_to_the_status(self):
        # only the status is resolved, so the resultaat cannot muddy the result
        zaak_with_group = self._make_zaak(resultaat=None)
        self.zaken_client.fetch_single_status.side_effect = ZgwAPIError("kapot")

        with self.assertLogs("open_inwoner.openzaak.services", level="ERROR") as cm:
            result = self._fully_resolve(zaak_with_group)

        self._assert_skipped_with_reasons(result, SkipReason.STATUS_RESOLUTION_FAILED)
        self.assertTrue(any(_RESOLUTION_FAILURE_LOG in msg for msg in cm.output))

    def test_statustype_fetch_failure_is_attributed_to_the_statustype(self):
        zaak_with_group = self._make_zaak(resultaat=None)
        self.catalogi_client.fetch_single_status_type.side_effect = ZgwAPIError("kapot")

        with self.assertLogs("open_inwoner.openzaak.services", level="ERROR") as cm:
            result = self._fully_resolve(zaak_with_group)

        self._assert_skipped_with_reasons(
            result, SkipReason.STATUSTYPE_RESOLUTION_FAILED
        )
        self.assertTrue(any(_RESOLUTION_FAILURE_LOG in msg for msg in cm.output))

    def test_resultaat_fetch_failure_is_attributed_to_the_resultaat(self):
        zaak_with_group = self._make_zaak(status=None)
        self.zaken_client.fetch_single_result.side_effect = ZgwAPIError("kapot")

        with self.assertLogs("open_inwoner.openzaak.services", level="ERROR") as cm:
            result = self._fully_resolve(zaak_with_group)

        self._assert_skipped_with_reasons(
            result, SkipReason.RESULTAAT_RESOLUTION_FAILED
        )
        self.assertTrue(any(_RESOLUTION_FAILURE_LOG in msg for msg in cm.output))

    def test_resultaattype_fetch_failure_is_attributed_to_the_resultaattype(self):
        zaak_with_group = self._make_zaak(status=None)
        self.catalogi_client.fetch_single_resultaat_type.side_effect = ZgwAPIError(
            "kapot"
        )

        with self.assertLogs("open_inwoner.openzaak.services", level="ERROR") as cm:
            result = self._fully_resolve(zaak_with_group)

        self._assert_skipped_with_reasons(
            result, SkipReason.RESULTAATTYPE_RESOLUTION_FAILED
        )
        self.assertTrue(any(_RESOLUTION_FAILURE_LOG in msg for msg in cm.output))

    def test_zaak_failing_several_steps_reports_every_reason(self):
        """A zaak is skipped once, but keeps the reason of every step that failed"""
        zaak_with_group = self._make_zaak()
        self.zaken_client.fetch_single_status.side_effect = ZgwAPIError("kapot")
        self.zaken_client.fetch_single_result.side_effect = ZgwAPIError("kapot")

        with self.assertLogs("open_inwoner.openzaak.services", level="ERROR"):
            result = self._fully_resolve(zaak_with_group)

        self._assert_skipped_with_reasons(
            result,
            SkipReason.STATUS_RESOLUTION_FAILED,
            SkipReason.RESULTAAT_RESOLUTION_FAILED,
        )

    def test_unexpected_failure_falls_back_to_the_generic_reason(self):
        zaak_with_group = self._make_zaak(resultaat=None)

        with (
            patch.object(
                self.service,
                "_resolve_status_and_status_type",
                side_effect=RuntimeError("kapot"),
            ),
            self.assertLogs("open_inwoner.openzaak.services", level="ERROR") as cm,
        ):
            result = self._fully_resolve(zaak_with_group)

        self._assert_skipped_with_reasons(result, SkipReason.RESOLUTION_FAILED)
        self.assertTrue(any(_UNEXPECTED_FAILURE_LOG in msg for msg in cm.output))

    def test_zaaktype_fetch_failure_is_attributed_to_the_zaaktype(self):
        zaak_with_group = self._make_zaak()
        self.catalogi_client.fetch_single_zaaktype.side_effect = ZgwAPIError("kapot")

        with (
            patch.object(
                self.service,
                "_get_raw_zaken_for_api_group",
                return_value=[zaak_with_group],
            ),
            patch.object(
                self.service,
                "_catalogi_client_factory",
                return_value=self.catalogi_client,
            ),
            self.assertLogs("open_inwoner.openzaak.services", level="ERROR") as cm,
        ):
            result = self.service.get_visible_zaken(_USER_IDENTIFICATION)

        self._assert_skipped_with_reasons(result, SkipReason.ZAAKTYPE_RESOLUTION_FAILED)
        self.assertTrue(any(_RESOLUTION_FAILURE_LOG in msg for msg in cm.output))

    def test_rol_fetch_failure_in_search_is_attributed_to_the_rol(self):
        """A match dropped because its rollen are unavailable makes results partial"""
        zaak_with_group = self._make_zaak()

        with (
            patch.object(
                self.service,
                "_get_raw_zaken_for_api_group",
                return_value=[zaak_with_group],
            ),
            patch.object(
                self.service,
                "_user_has_required_rol",
                side_effect=ZgwAPIError("kapot"),
            ),
            self.assertLogs("open_inwoner.openzaak.services", level="ERROR") as cm,
        ):
            result = self.service.search_zaken(
                _USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE
            )

        self._assert_skipped_with_reasons(result, SkipReason.ROL_RESOLUTION_FAILED)
        self.assertTrue(any(_RESOLUTION_FAILURE_LOG in msg for msg in cm.output))

    def test_search_result_without_rol_is_not_reported_as_skipped(self):
        """Permanent exclusions must not trigger the partial-results banner"""
        zaak_with_group = self._make_zaak()

        with (
            patch.object(
                self.service,
                "_get_raw_zaken_for_api_group",
                return_value=[zaak_with_group],
            ),
            patch.object(self.service, "_user_has_required_rol", return_value=False),
        ):
            result = self.service.search_zaken(
                _USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE
            )

        self.assertEqual(result.zaken, [])
        self.assertEqual(result.skipped, [])
        self.assertFalse(result.is_incomplete)


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


class ZaakVisibleFromDateTest(ClearCachesMixin, TestCase):
    """
    A zaaktype may configure a date before which its zaken are not shown to users.

    The check lives in `_is_zaak_visible`, the single gate used by the case list,
    search, the detail page and notifications.
    """

    def setUp(self):
        super().setUp()
        config = OpenZaakConfig.get_solo()
        config.show_cases_without_status = True
        config.save()

        self.catalogus = CatalogusConfigFactory(
            url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a"
        )
        self.zaaktype = factory(
            ZaakType,
            generate_oas_component_cached(
                "ztc",
                "schemas/ZaakType",
                url=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
                catalogus=self.catalogus.url,
                identificatie="ZAAKTYPE-001",
                indicatieInternOfExtern="extern",
            ),
        )

    def _zaak(self, startdatum: date) -> Zaak:
        zaak = factory(
            Zaak,
            generate_oas_component_cached(
                "zrc",
                "schemas/Zaak",
                url=f"{ZAKEN_ROOT}zaken/{_ZAAK_UUID}",
                zaaktype=self.zaaktype.url,
                identificatie=_ZAAK_IDENTIFICATIE,
                startdatum=startdatum.isoformat(),
                vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            ),
        )
        zaak.zaaktype = self.zaaktype
        zaak.startdatum = startdatum
        return zaak

    def test_visible_when_no_date_configured(self):
        ZaakTypeConfigFactory(
            catalogus=self.catalogus,
            identificatie=self.zaaktype.identificatie,
            zaken_visible_from=None,
        )

        result = ZGWService()._is_zaak_visible(self._zaak(date(2020, 1, 1)))

        self.assertEqual(result, (True, None))

    def test_visible_when_no_zaaktype_config_exists(self):
        result = ZGWService()._is_zaak_visible(self._zaak(date(2020, 1, 1)))

        self.assertEqual(result, (True, None))

    def test_visible_when_startdatum_on_or_after_configured_date(self):
        ZaakTypeConfigFactory(
            catalogus=self.catalogus,
            identificatie=self.zaaktype.identificatie,
            zaken_visible_from=date(2026, 5, 1),
        )

        for startdatum in (date(2026, 5, 1), date(2026, 5, 2), date(2027, 1, 1)):
            with self.subTest(startdatum=startdatum):
                result = ZGWService()._is_zaak_visible(self._zaak(startdatum))

                self.assertEqual(result, (True, None))

    def test_invisible_when_startdatum_before_configured_date(self):
        ZaakTypeConfigFactory(
            catalogus=self.catalogus,
            identificatie=self.zaaktype.identificatie,
            zaken_visible_from=date(2026, 5, 1),
        )

        for startdatum in (date(2026, 4, 30), date(2020, 1, 1)):
            with self.subTest(startdatum=startdatum):
                result = ZGWService()._is_zaak_visible(self._zaak(startdatum))

                self.assertEqual(result, (False, SkipReason.BEFORE_VISIBLE_FROM_DATE))

    def test_date_of_other_zaaktype_does_not_apply(self):
        ZaakTypeConfigFactory(
            catalogus=self.catalogus,
            identificatie="SOME-OTHER-ZAAKTYPE",
            zaken_visible_from=date(2026, 5, 1),
        )

        result = ZGWService()._is_zaak_visible(self._zaak(date(2020, 1, 1)))

        self.assertEqual(result, (True, None))

    def test_date_of_same_identificatie_in_other_catalogus_does_not_apply(self):
        """Zaaktype identificaties are only unique within a catalogus."""
        ZaakTypeConfigFactory(
            catalogus=CatalogusConfigFactory(
                url=f"{CATALOGI_ROOT}catalogussen/8a4b1a2c-0000-0000-0000-000000000000"
            ),
            identificatie=self.zaaktype.identificatie,
            zaken_visible_from=date(2026, 5, 1),
        )

        result = ZGWService()._is_zaak_visible(self._zaak(date(2020, 1, 1)))

        self.assertEqual(result, (True, None))

    def test_reads_configuration_only_once_per_service_instance(self):
        """The case list checks every zaak, so the lookup must not be an N+1."""
        ZaakTypeConfigFactory(
            catalogus=self.catalogus,
            identificatie=self.zaaktype.identificatie,
            zaken_visible_from=date(2026, 5, 1),
        )
        service = ZGWService()
        zaken = [self._zaak(date(2020, 1, 1)) for _ in range(5)]

        with CaptureQueriesContext(connection) as ctx:
            for zaak in zaken:
                service._is_zaak_visible(zaak)

        zaaktype_config_queries = [
            query
            for query in ctx.captured_queries
            if "openzaak_zaaktypeconfig" in query["sql"]
        ]
        self.assertEqual(len(zaaktype_config_queries), 1)


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

        results = self.service.search_zaken(
            _USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE
        ).zaken

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].zaak.identificatie, _ZAAK_IDENTIFICATIE)
        self.assertEqual(results[0].api_group, self.api_group)

    def test_excludes_zaak_when_user_has_no_rol(self, m):
        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        self._mock_rollen(m, [])

        results = self.service.search_zaken(
            _USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE
        ).zaken

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
                ).zaken

                self.assertEqual(results, [])

    def test_returns_zaak_for_any_rol_when_no_limit_configured(self, m):
        """Guard against over-filtering when the config is left blank."""
        self.config.limit_user_visible_cases_to_role = ""
        self.config.save()

        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        self._mock_rollen(m, [self._rol_component(RolOmschrijving.belanghebbende)])

        results = self.service.search_zaken(
            _USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE
        ).zaken

        self.assertEqual(len(results), 1)

    def test_excludes_zaak_without_any_rol_when_no_limit_configured(self, m):
        """Matches the `check_zaak_access` gate: some rol is always required."""
        self.config.limit_user_visible_cases_to_role = ""
        self.config.save()

        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        self._mock_rollen(m, [])

        results = self.service.search_zaken(
            _USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE
        ).zaken

        self.assertEqual(results, [])

    def test_excludes_zaak_when_rollen_fetch_fails(self, m):
        """Fail closed: an indeterminate authorization answer must deny."""
        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}", status_code=500)

        with self.assertLogs("open_inwoner.openzaak.services", level="ERROR") as cm:
            result = self.service.search_zaken(
                _USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE
            )

        self.assertEqual(result.zaken, [])
        self.assertEqual(
            [skipped.reasons for skipped in result.skipped],
            [frozenset({SkipReason.ROL_RESOLUTION_FAILED})],
        )
        # the user searched for a zaak that exists, so tell them results are partial
        self.assertTrue(result.is_incomplete)
        self.assertTrue(any(_RESOLUTION_FAILURE_LOG in msg for msg in cm.output))

    def test_does_not_resolve_zaaktype_when_rol_check_fails(self, m):
        """No metadata is resolved for a zaak the user has no claim to."""
        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        self._mock_rollen(m, [self._rol_component(RolOmschrijving.belanghebbende)])

        self.service.search_zaken(_USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE)

        requested = [req.url for req in m.request_history]
        self.assertNotIn(self.zaaktype["url"], requested)

    def _configure_visible_from(self, visible_from: date):
        return ZaakTypeConfigFactory(
            catalogus=CatalogusConfigFactory(url=self.zaaktype["catalogus"]),
            identificatie=self.zaaktype["identificatie"],
            zaken_visible_from=visible_from,
        )

    def test_excludes_zaak_older_than_zaaktype_visible_from_date(self, m):
        """Searching on an exact zaaknummer must not bypass the visibility date."""
        self._configure_visible_from(date(2026, 5, 1))
        self.zaak["startdatum"] = "2026-04-30"

        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        self._mock_rollen(m, [self._rol_component(RolOmschrijving.initiator)])

        results = self.service.search_zaken(
            _USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE
        ).zaken

        self.assertEqual(results, [])

    def test_returns_zaak_on_or_after_zaaktype_visible_from_date(self, m):
        self._configure_visible_from(date(2026, 5, 1))
        self.zaak["startdatum"] = "2026-05-01"

        self._mock_zaken_search(m, [self.zaak])
        m.get(self.zaaktype["url"], json=self.zaaktype)
        self._mock_rollen(m, [self._rol_component(RolOmschrijving.initiator)])

        results = self.service.search_zaken(
            _USER_IDENTIFICATION, _ZAAK_IDENTIFICATIE
        ).zaken

        self.assertEqual(len(results), 1)
