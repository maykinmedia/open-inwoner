import json
from contextlib import contextmanager
from unittest.mock import call, patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse_lazy

from structlog.testing import capture_logs

from open_inwoner.reporting_api.metrics import (
    permissions_policy_violations,
    rejected_reports,
)


@contextmanager
def capture_violation_logs():
    # capture_logs() also picks up the request logs of django-structlog
    violation_logs = []
    with capture_logs() as logs:
        yield violation_logs
    violation_logs.extend(
        log
        for log in logs
        if log["event"]
        in ("permissions_policy_violation", "permissions_policy_violations_not_logged")
    )


def make_report(type="permissions-policy-violation", **body) -> dict:
    # as sent by Chrome
    return {
        "age": 1,
        "body": {
            "columnNumber": 34,
            "disposition": "report",
            "lineNumber": 12,
            "message": "Permissions policy violation: Geolocation access has been blocked",
            "policyId": "geolocation",
            "sourceFile": "https://testserver/static/bundles/main.js",
            **body,
        },
        "type": type,
        "url": "https://testserver/zaken/?bsn=123456782#top",
        "user_agent": "Mozilla/5.0",
    }


# independent of local configuration, which might allow any host
@override_settings(ALLOWED_HOSTS=["testserver"])
@patch.object(permissions_policy_violations, "add")
class ReportingApiViewTests(TestCase):
    url = reverse_lazy("api:reporting_api")

    def post(self, data):
        return self.client.post(
            self.url,
            data=json.dumps(data),
            content_type="application/reports+json",
        )

    def test_logs_violations_and_emits_metrics(self, mock_add):
        with capture_violation_logs() as logs:
            response = self.post(
                [
                    make_report(),
                    make_report(
                        type="potential-permissions-policy-violation",
                        policyId="fullscreen",
                        disposition="enforce",
                        sourceFile=None,
                        lineNumber=None,
                        columnNumber=None,
                    ),
                ]
            )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            logs,
            [
                {
                    "event": "permissions_policy_violation",
                    "log_level": "warning",
                    "type": "permissions-policy-violation",
                    "feature": "geolocation",
                    "disposition": "report",
                    "url": "https://testserver/zaken/",
                    "source_file": "https://testserver/static/bundles/main.js",
                    "line_number": 12,
                    "column_number": 34,
                    "user_agent": "Mozilla/5.0",
                },
                {
                    "event": "permissions_policy_violation",
                    "log_level": "warning",
                    "type": "potential-permissions-policy-violation",
                    "feature": "fullscreen",
                    "disposition": "enforce",
                    "url": "https://testserver/zaken/",
                    "source_file": None,
                    "line_number": None,
                    "column_number": None,
                    "user_agent": "Mozilla/5.0",
                },
            ],
        )
        self.assertEqual(
            mock_add.call_args_list,
            [
                call(
                    1,
                    {
                        "type": "permissions-policy-violation",
                        "feature": "geolocation",
                        "disposition": "report",
                        "source": "self",
                    },
                ),
                call(
                    1,
                    {
                        "type": "potential-permissions-policy-violation",
                        "feature": "fullscreen",
                        "disposition": "enforce",
                        "source": "unknown",
                    },
                ),
            ],
        )

    def test_accepts_feature_id_from_spec(self, mock_add):
        report = make_report()
        report["body"]["featureId"] = report["body"].pop("policyId")

        with capture_violation_logs() as logs:
            response = self.post([report])

        self.assertEqual(response.status_code, 204)
        self.assertEqual(logs[0]["feature"], "geolocation")
        mock_add.assert_called_once_with(
            1,
            {
                "type": "permissions-policy-violation",
                "feature": "geolocation",
                "disposition": "report",
                "source": "self",
            },
        )

    @override_settings(REPORTING_API_METRICS_ENABLED=False)
    def test_metrics_can_be_disabled(self, mock_add):
        with capture_violation_logs() as logs:
            response = self.post([make_report()])

        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(logs), 1)
        mock_add.assert_not_called()

    @override_settings(REPORTING_API_LOGGING_ENABLED=False)
    def test_logging_can_be_disabled(self, mock_add):
        with capture_violation_logs() as logs:
            response = self.post(
                [make_report()]
                * (settings.REPORTING_API_MAX_LOGGED_VIOLATIONS_PER_REQUEST + 1)
            )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(logs, [])
        self.assertEqual(
            mock_add.call_count,
            settings.REPORTING_API_MAX_LOGGED_VIOLATIONS_PER_REQUEST + 1,
        )

    def test_skips_other_and_invalid_reports(self, mock_add):
        cases = [
            make_report(type="deprecation"),
            make_report(policyId=None),
            make_report(lineNumber="twelve"),
            make_report(disposition="ignore"),
            make_report(policyId="x" * 65),
            make_report(sourceFile="https://testserver/" + "x" * 4096),
            make_report(sourceFile="http://[invalid/"),
            {**make_report(), "url": "https://testserver/" + "x" * 4096},
            {**make_report(), "url": "http://[invalid/"},
            {**make_report(), "body": "garbage"},
            "garbage",
        ]
        for report in cases:
            with self.subTest(report=report):
                with capture_violation_logs() as logs:
                    response = self.post([report])

                self.assertEqual(response.status_code, 204)
                self.assertEqual(logs, [])
                mock_add.assert_not_called()

    @patch.object(rejected_reports, "add")
    def test_skips_reports_about_other_sites(self, mock_rejected_add, mock_add):
        with capture_violation_logs() as logs:
            response = self.post(
                [{**make_report(), "url": "https://example.com/zaken/"}]
            )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(logs, [])
        mock_add.assert_not_called()
        mock_rejected_add.assert_called_once_with(1, {"reason": "unknown_host"})

    @override_settings(REPORTING_API_METRICS_ENABLED=False)
    @patch.object(rejected_reports, "add")
    def test_rejected_reports_not_counted_when_metrics_disabled(
        self, mock_rejected_add, mock_add
    ):
        self.post([{**make_report(), "url": "https://example.com/zaken/"}])

        mock_rejected_add.assert_not_called()

    def test_external_scripts_are_marked_in_metric(self, mock_add):
        self.post([make_report(sourceFile="https://widget.example.com/chat.js")])

        mock_add.assert_called_once_with(
            1,
            {
                "type": "permissions-policy-violation",
                "feature": "geolocation",
                "disposition": "report",
                "source": "external",
            },
        )

    def test_unknown_features_are_grouped_in_metric(self, mock_add):
        with capture_violation_logs() as logs:
            self.post([make_report(policyId="made-up-feature")])

        self.assertEqual(logs[0]["feature"], "made-up-feature")
        mock_add.assert_called_once_with(
            1,
            {
                "type": "permissions-policy-violation",
                "feature": "other",
                "disposition": "report",
                "source": "self",
            },
        )

    def test_limits_logged_violations_but_counts_all(self, mock_add):
        with capture_violation_logs() as logs:
            self.post(
                [make_report()]
                * (settings.REPORTING_API_MAX_LOGGED_VIOLATIONS_PER_REQUEST + 3)
            )

        self.assertEqual(
            [log["event"] for log in logs],
            ["permissions_policy_violation"]
            * settings.REPORTING_API_MAX_LOGGED_VIOLATIONS_PER_REQUEST
            + ["permissions_policy_violations_not_logged"],
        )
        self.assertEqual(
            logs[-1],
            {
                "event": "permissions_policy_violations_not_logged",
                "log_level": "warning",
                "count": 3,
            },
        )
        self.assertEqual(
            mock_add.call_count,
            settings.REPORTING_API_MAX_LOGGED_VIOLATIONS_PER_REQUEST + 3,
        )

    def test_ignored_reports_do_not_use_up_log_limit(self, mock_add):
        with capture_violation_logs() as logs:
            self.post(
                [make_report(type="deprecation")] * 10
                + [make_report(policyId="camera")]
            )

        self.assertEqual([log["feature"] for log in logs], ["camera"])

    @override_settings(REPORTING_API_MAX_REPORTS_PER_REQUEST=3)
    def test_limits_reports_per_request(self, mock_add):
        self.post([make_report()] * 5)

        self.assertEqual(mock_add.call_count, 3)

    def test_rejects_non_list_payload(self, mock_add):
        response = self.post(make_report())

        self.assertEqual(response.status_code, 400)

    def test_rejects_invalid_json(self, mock_add):
        response = self.client.post(
            self.url, data="not json", content_type="application/reports+json"
        )

        self.assertEqual(response.status_code, 400)

    def test_rejects_deeply_nested_json(self, mock_add):
        response = self.client.post(
            self.url,
            data="[" * 100_000 + "]" * 100_000,
            content_type="application/reports+json",
        )

        self.assertEqual(response.status_code, 400)

    def test_rejects_other_content_types(self, mock_add):
        response = self.client.post(
            self.url, data=json.dumps([make_report()]), content_type="application/json"
        )

        self.assertEqual(response.status_code, 415)

    @override_settings(REPORTING_API_ENABLED=False)
    def test_unavailable_when_disabled(self, mock_add):
        with capture_violation_logs() as logs:
            response = self.post([make_report()])

        self.assertEqual(response.status_code, 404)
        self.assertEqual(logs, [])
        mock_add.assert_not_called()

    def test_rejects_other_methods(self, mock_add):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
