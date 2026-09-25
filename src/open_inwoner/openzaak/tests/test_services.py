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

# 1ms deadlines against a 50ms release were flaky under CI load - narrow
# enough to occasionally be swallowed entirely by OS scheduling jitter,
# regardless of the 50x ratio between them. These values match the ones
# proven reliable in open_inwoner.utils.tests.test_concurrency.
_TINY_TIMEOUT = 0.01
_RELEASE_DELAY = 0.1

_TINY_TIMEOUTS = {
    "get_raw_zaken": _TINY_TIMEOUT,
    "get_visible_zaken": _TINY_TIMEOUT,
    "fully_resolve_zaken": _TINY_TIMEOUT,
    "get_formulieren": _TINY_TIMEOUT,
}


class FormulierenClientFactoryTest(ClearCachesMixin, TestCase):
    def test_raises_for_a_group_without_a_form_service(self):
        group = ZGWApiGroupConfigFactory(form_service=None)

        with self.assertRaises(ValueError):
            ZGWService._formulieren_client_factory(group)


class ZgwClientConnectTimeoutTest(ClearCachesMixin, TestCase):
    """
    Every client `ZGWService` builds gets a connect-phase timeout tighter
    than its configured (read) timeout - see `_TightConnectServiceConfigAdapter`.

    `timeout` isn't a `requests.Session` attribute, so `ape_pie.APIClient`
    only ever stores it in this private per-request-defaults dict - there's
    no public getter for it.
    """

    def test_zaken_client_gets_a_tighter_connect_timeout(self):
        group = ZGWApiGroupConfigFactory(zrc_service__timeout=10)

        client = ZGWService._zaken_client_factory(group)

        self.assertEqual(client._request_kwargs["timeout"], (3.0, 10))

    def test_catalogi_client_gets_a_tighter_connect_timeout(self):
        group = ZGWApiGroupConfigFactory(ztc_service__timeout=10)

        client = ZGWService._catalogi_client_factory(group)

        self.assertEqual(client._request_kwargs["timeout"], (3.0, 10))

    def test_documenten_client_gets_a_tighter_connect_timeout(self):
        group = ZGWApiGroupConfigFactory(drc_service__timeout=10)

        client = ZGWService._documenten_client_factory(group)

        self.assertEqual(client._request_kwargs["timeout"], (3.0, 10))

    def test_formulieren_client_gets_a_tighter_connect_timeout(self):
        group = ZGWApiGroupConfigFactory(form_service__timeout=10)

        client = ZGWService._formulieren_client_factory(group)

        self.assertEqual(client._request_kwargs["timeout"], (3.0, 10))

    def test_connect_timeout_never_drops_below_the_floor(self):
        # 30% of 1s is 0.3s, well under the 2s floor.
        group = ZGWApiGroupConfigFactory(zrc_service__timeout=1)

        client = ZGWService._zaken_client_factory(group)

        self.assertEqual(client._request_kwargs["timeout"], (2, 1))


class IncompleteZakenResultTest(ClearCachesMixin, TestCase):
    """
    Verify that a still-in-flight fetch is correctly reflected in the
    result, whether it's genuinely abandoned or merely running late.

    TimedParallel distinguishes two outcomes once a per-stage timeout
    elapses: a task that hasn't started yet is cancelled outright and will
    never produce a result, while a task that's already running is still
    awaited - shutdown(wait=True) blocks for it regardless, so its actual
    outcome is used instead of being discarded. A single submitted task is
    therefore *not* a reliable way to exercise "genuinely timed out" (it
    almost always ends up already running by the time the tiny timeout
    below elapses): tests use a single worker with two work items instead,
    so at least one is always genuinely abandoned regardless of which of
    the two happens to start first.

    Each test blocks a fetch with a threading.Event and sets a tiny
    (`_TINY_TIMEOUT`) deadline. A timer releases the event after
    `_RELEASE_DELAY` so shutdown(wait=True) doesn't hang waiting for the
    one that's still running.
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
        # A second API group + a single worker guarantees at least one
        # group's fetch is still queued (never started) when the timeout
        # elapses, regardless of which of the two the sole worker picks up.
        ZGWApiGroupConfigFactory()
        self.service._max_workers = 1
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

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
        self.assertTrue(
            any("Cancelled pending raw zaken fetches" in msg for msg in cm.output)
        )

    def test_get_visible_zaken_logs_timeout_warning_on_raw_fetch(self):
        ZGWApiGroupConfigFactory()
        self.service._max_workers = 1
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

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
        self.assertTrue(
            any(
                "Cancelled pending raw zaken fetches for group" in msg
                for msg in cm.output
            )
        )

    def test_get_formulieren_logs_timeout_warning(self):
        ZGWApiGroupConfigFactory()
        self.service._max_workers = 1
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

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
            any("Cancelled pending formulieren fetches" in msg for msg in cm.output)
        )

    def test_search_zaken_propagates_raw_fetch_timeout(self):
        ZGWApiGroupConfigFactory()
        self.service._max_workers = 1
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

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
        """
        The raw fetch succeeds, but resolving zaaktypen runs out of budget.

        With a single worker and two zaken to resolve, one is always still
        queued (never started) when the deadline hits and is genuinely
        abandoned -> SkipReason.TIMEOUT. The other is already running and
        is awaited instead of discarded; it's made to fail once it does
        complete (rather than succeed) so the outcome doesn't depend on
        which of the two "wins" the race for the single worker.
        """
        zaak_a = self._make_zaak_with_group(_ZAAK_UUID)
        zaak_b = self._make_zaak_with_group(_ANOTHER_ZAAK_UUID)
        self.service._max_workers = 1
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

        def blocking_then_failing_with_reason(*args, **kwargs):
            release.wait(timeout=5)
            raise ZaakResolutionError(SkipReason.ZAAKTYPE_RESOLUTION_FAILED, "kapot")

        timeouts = {**_TINY_TIMEOUTS, "get_raw_zaken": 5}

        with (
            patch.object(
                self.service,
                "_get_raw_zaken_for_api_group",
                return_value=[zaak_a, zaak_b],
            ),
            patch.object(
                self.service,
                "_resolve_zaak_type",
                side_effect=blocking_then_failing_with_reason,
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
            sorted(
                reason.value for skipped in result.skipped for reason in skipped.reasons
            ),
            sorted(
                [SkipReason.TIMEOUT.value, SkipReason.ZAAKTYPE_RESOLUTION_FAILED.value]
            ),
        )
        self.assertTrue(result.is_incomplete)

    def test_fully_resolve_zaken_records_timeout_skips(self):
        """
        With a single worker and two zaken (each needing two resolution
        calls), at most one resolution call can be running when the
        deadline hits - so every zaak has at least one call that's still
        queued and genuinely abandoned, and both end up skipped as timed
        out regardless of which call happens to be the one running.
        """
        zaak_a = self._make_zaak_with_group(_ZAAK_UUID)
        zaak_b = self._make_zaak_with_group(_ANOTHER_ZAAK_UUID)
        self.service._max_workers = 1
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

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
                result = self.service.fully_resolve_zaken([zaak_a, zaak_b])
            finally:
                release.set()
                timer.cancel()

        self.assertEqual(result.zaken, [])
        self.assertEqual(
            [skipped.reasons for skipped in result.skipped],
            [frozenset({SkipReason.TIMEOUT}), frozenset({SkipReason.TIMEOUT})],
        )
        self.assertTrue(result.is_incomplete)

    def test_fully_resolve_zaken_keeps_failures_alongside_the_timeout(self):
        """
        A step that's already running when the stage runs out of budget is
        awaited and its real (here: failing) outcome is used; a step that
        never got a worker at all is genuinely abandoned. When both apply
        to the same zaak, it keeps both reasons.

        A single worker guarantees the deterministic split: the resultaat
        step is always the one submitted first, so it's the one that
        starts running (and fails once released); the status step is
        submitted right behind it and can only ever be genuinely queued,
        since the sole worker stays busy with the resultaat step for the
        entire 50ms until release fires - long past the 1ms deadline.
        """
        zaak_with_group = self._make_zaak_with_group(_ZAAK_UUID)
        self.service._max_workers = 1
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

        def blocking_then_failing_with_reason(*args, **kwargs):
            release.wait(timeout=5)
            raise ZaakResolutionError(SkipReason.RESULTAAT_RESOLUTION_FAILED, "kapot")

        with (
            patch.object(
                self.service,
                "_resolve_resultaat_and_resultaat_type",
                side_effect=blocking_then_failing_with_reason,
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
_ANOTHER_ZAAK_UUID = "5e3d0f4c-6b21-4b4e-9c47-3a3d9d7e5b2f"
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
        """
        With a single worker, two configured API groups guarantee at least
        one group's fetch is still queued (never started) when the
        deadline hits, regardless of which of the two the sole worker
        picks up. The one that does get to run is made to fail once
        released rather than "succeed" with a meaningless value, so the
        overall result is None either way.
        """
        self.service._max_workers = 1
        release = threading.Event()
        timer = threading.Timer(_RELEASE_DELAY, release.set)

        def blocking_then_failing(*args, **kwargs):
            release.wait(timeout=5)
            raise RuntimeError("boom")

        mock_client = Mock()
        mock_client.fetch_single_zaak.side_effect = blocking_then_failing

        with (
            patch.object(
                self.service, "_zaken_client_factory", return_value=mock_client
            ),
            patch(
                "open_inwoner.openzaak.services.OpenZaakConfig.get_solo",
                return_value=Mock(case_list_fetch_timeout=_TINY_TIMEOUT),
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
            any("cancelled pending zaak-by-uuid fetches" in msg for msg in cm.output)
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
