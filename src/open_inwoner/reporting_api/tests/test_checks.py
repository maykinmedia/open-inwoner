from django.core.checks import Warning
from django.test import SimpleTestCase, override_settings

from open_inwoner.reporting_api.checks import check_reports_are_used


class CheckReportsAreUsedTests(SimpleTestCase):
    @override_settings(
        REPORTING_API_LOGGING_ENABLED=False, REPORTING_API_METRICS_ENABLED=False
    )
    def test_warns_when_reports_are_discarded(self):
        self.assertEqual(
            check_reports_are_used(None),
            [
                Warning(
                    "Reporting API logging and metrics are both disabled, received "
                    "reports are discarded.",
                    hint=(
                        "Enable REPORTING_API_LOGGING_ENABLED and/or "
                        "REPORTING_API_METRICS_ENABLED, or disable "
                        "REPORTING_API_ENABLED so browsers stop sending reports."
                    ),
                    id="reporting_api.W001",
                )
            ],
        )

    @override_settings(
        REPORTING_API_ENABLED=False,
        REPORTING_API_LOGGING_ENABLED=False,
        REPORTING_API_METRICS_ENABLED=False,
    )
    def test_no_warning_when_reporting_is_disabled(self):
        self.assertEqual(check_reports_are_used(None), [])

    @override_settings(
        REPORTING_API_LOGGING_ENABLED=False, REPORTING_API_METRICS_ENABLED=True
    )
    def test_no_warning_when_metrics_are_enabled(self):
        self.assertEqual(check_reports_are_used(None), [])

    @override_settings(
        REPORTING_API_LOGGING_ENABLED=True, REPORTING_API_METRICS_ENABLED=False
    )
    def test_no_warning_when_logging_is_enabled(self):
        self.assertEqual(check_reports_are_used(None), [])
