from django.test import TestCase, override_settings
from django.urls import reverse

from open_inwoner.healthchecks.checks import CheckResult


class HealthCheckViewTestCase(TestCase):
    def test_basic_health_check(self):
        """Test basic health endpoint always returns OK."""
        response = self.client.get(reverse("healthchecks:healthz"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")


class LivenessViewTestCase(TestCase):
    @override_settings(HEALTHCHECKS_LIVENESS_CHECKS=[])
    def test_liveness_no_checks(self):
        """Test liveness endpoint with no checks configured."""
        response = self.client.get(reverse("healthchecks:livez"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    @override_settings(
        HEALTHCHECKS_LIVENESS_CHECKS=[
            "open_inwoner.healthchecks.tests.test_views.mock_check_success"
        ]
    )
    def test_liveness_check_success(self):
        """Test liveness endpoint with successful check."""
        response = self.client.get(reverse("healthchecks:livez"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    @override_settings(
        HEALTHCHECKS_LIVENESS_CHECKS=[
            "open_inwoner.healthchecks.tests.test_views.mock_check_failure"
        ],
        HEALTHCHECKS_VERBOSE_RESPONSE=False,
    )
    def test_liveness_check_failure_non_verbose(self):
        """Test liveness endpoint with failed check (non-verbose)."""
        response = self.client.get(reverse("healthchecks:livez"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.content.decode(), "NOT OK")

    @override_settings(
        HEALTHCHECKS_LIVENESS_CHECKS=[
            "open_inwoner.healthchecks.tests.test_views.mock_check_failure"
        ],
        HEALTHCHECKS_VERBOSE_RESPONSE=True,
    )
    def test_liveness_check_failure_verbose(self):
        """Test liveness endpoint with failed check (verbose)."""
        response = self.client.get(reverse("healthchecks:livez"))
        self.assertEqual(response.status_code, 503)
        self.assertIn("test_service", response.content.decode())
        self.assertIn("error: test failed", response.content.decode())

    @override_settings(
        HEALTHCHECKS_LIVENESS_CHECKS=[
            "open_inwoner.healthchecks.tests.test_views.mock_check_failure"
        ],
        HEALTHCHECKS_VERBOSE_RESPONSE=True,
    )
    def test_liveness_check_json_response(self):
        """Test liveness endpoint with JSON format."""
        response = self.client.get(reverse("healthchecks:livez") + "?format=json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertIn("test_service", data["checks"])


class ReadinessViewTestCase(TestCase):
    @override_settings(
        HEALTHCHECKS_READINESS_CHECKS=[
            "open_inwoner.healthchecks.tests.test_views.mock_check_success"
        ]
    )
    def test_readiness_check_success(self):
        """Test readiness endpoint with successful check."""
        response = self.client.get(reverse("healthchecks:readyz"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    @override_settings(
        HEALTHCHECKS_READINESS_CHECKS=[
            "open_inwoner.healthchecks.tests.test_views.mock_check_failure"
        ],
        HEALTHCHECKS_VERBOSE_RESPONSE=False,
    )
    def test_readiness_check_failure_non_verbose(self):
        """Test readiness endpoint with failed check (non-verbose)."""
        response = self.client.get(reverse("healthchecks:readyz"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.content.decode(), "NOT OK")

    @override_settings(
        HEALTHCHECKS_READINESS_CHECKS=[
            "open_inwoner.healthchecks.tests.test_views.mock_check_success",
            "open_inwoner.healthchecks.tests.test_views.mock_check_failure",
        ],
        HEALTHCHECKS_VERBOSE_RESPONSE=True,
    )
    def test_readiness_multiple_checks_mixed(self):
        """Test readiness with multiple checks where one fails."""
        response = self.client.get(reverse("healthchecks:readyz"))
        self.assertEqual(response.status_code, 503)
        content = response.content.decode()
        self.assertIn("test_service", content)
        self.assertIn("good_service", content)


class StartupViewTestCase(TestCase):
    @override_settings(
        HEALTHCHECKS_STARTUP_CHECKS=[
            "open_inwoner.healthchecks.tests.test_views.mock_check_success"
        ]
    )
    def test_startup_check_success(self):
        """Test startup endpoint with successful check."""
        response = self.client.get(reverse("healthchecks:startupz"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    @override_settings(
        HEALTHCHECKS_STARTUP_CHECKS=[
            "open_inwoner.healthchecks.tests.test_views.mock_check_failure"
        ],
        HEALTHCHECKS_VERBOSE_RESPONSE=True,
    )
    def test_startup_check_failure_verbose(self):
        """Test startup endpoint with failed check (verbose)."""
        response = self.client.get(reverse("healthchecks:startupz"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.content.decode(), "Service Starting")

    @override_settings(
        HEALTHCHECKS_STARTUP_CHECKS=[
            "open_inwoner.healthchecks.tests.test_views.mock_check_success"
        ],
        HEALTHCHECKS_VERBOSE_RESPONSE=True,
    )
    def test_startup_check_json_response_success(self):
        """Test startup endpoint JSON response with correct status label."""
        response = self.client.get(reverse("healthchecks:startupz") + "?format=json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ready")

    @override_settings(
        HEALTHCHECKS_STARTUP_CHECKS=[
            "open_inwoner.healthchecks.tests.test_views.mock_check_failure"
        ],
        HEALTHCHECKS_VERBOSE_RESPONSE=True,
    )
    def test_startup_check_json_response_failure(self):
        """Test startup endpoint JSON response with correct failure status label."""
        response = self.client.get(reverse("healthchecks:startupz") + "?format=json")
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "not_ready")


class CheckImportErrorTestCase(TestCase):
    @override_settings(
        HEALTHCHECKS_READINESS_CHECKS=["non.existent.check.function"],
        HEALTHCHECKS_VERBOSE_RESPONSE=True,
    )
    def test_import_error_handling(self):
        """Test that import errors are handled gracefully."""
        response = self.client.get(reverse("healthchecks:readyz"))
        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.content.decode())


# Mock check functions for testing
def mock_check_success() -> CheckResult:
    """Mock check that always succeeds."""
    return CheckResult(name="good_service", success=True)


def mock_check_failure() -> CheckResult:
    """Mock check that always fails."""
    return CheckResult(name="test_service", success=False, message="error: test failed")
