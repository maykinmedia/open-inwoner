import threading
from unittest.mock import patch

from django.test import TestCase

from open_inwoner.accounts.user_identification import BSNIdentification
from open_inwoner.openzaak.services import ZGWService
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory
from open_inwoner.utils.test import ClearCachesMixin

_USER_IDENTIFICATION = BSNIdentification(bsn="900222086")


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

        with patch.object(
            self.service,
            "_get_raw_zaken_for_api_group",
            side_effect=self._make_blocking_fetch(release),
        ):
            self.service._timeouts["fetch_raw_zaken"] = 0.001
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

        with patch.object(
            self.service,
            "_get_raw_zaken_for_api_group",
            side_effect=self._make_blocking_fetch(release),
        ):
            self.service._timeouts["fetch_raw_zaken"] = 0.001
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

        with patch.object(
            self.service,
            "_get_formulieren_for_api_group",
            side_effect=self._make_blocking_fetch(release),
        ):
            self.service._timeouts["fetch_formulieren"] = 0.001
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
