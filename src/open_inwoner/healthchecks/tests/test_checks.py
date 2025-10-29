from unittest.mock import Mock, patch

from django.test import TestCase

from open_inwoner.healthchecks.checks import (
    CheckResult,
    check_cache,
    check_celery,
    check_database,
)


class CheckResultTestCase(TestCase):
    def test_check_result_success(self):
        result = CheckResult(name="test", success=True)
        self.assertEqual(result.name, "test")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "ok")

    def test_check_result_failure(self):
        result = CheckResult(name="test", success=False, message="error: test failed")
        self.assertEqual(result.name, "test")
        self.assertFalse(result.success)
        self.assertEqual(result.message, "error: test failed")


class CheckDatabaseTestCase(TestCase):
    def test_database_check_success(self):
        result = check_database()
        self.assertEqual(result.name, "database")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "ok")

    @patch("open_inwoner.healthchecks.checks.connection")
    def test_database_check_failure(self, mock_connection):
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Connection failed")
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        result = check_database()
        self.assertEqual(result.name, "database")
        self.assertFalse(result.success)
        self.assertIn("Connection failed", result.message)


class CheckCacheTestCase(TestCase):
    def test_cache_check_success(self):
        result = check_cache()
        self.assertEqual(result.name, "cache")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "ok")

    @patch("open_inwoner.healthchecks.checks.cache")
    def test_cache_check_failure_read(self, mock_cache):
        mock_cache.set.return_value = None
        mock_cache.get.return_value = None  # Cache read failed

        result = check_cache()
        self.assertEqual(result.name, "cache")
        self.assertFalse(result.success)
        self.assertIn("cache read failed", result.message)

    @patch("open_inwoner.healthchecks.checks.cache")
    def test_cache_check_failure_exception(self, mock_cache):
        mock_cache.set.side_effect = Exception("Cache unavailable")

        result = check_cache()
        self.assertEqual(result.name, "cache")
        self.assertFalse(result.success)
        self.assertIn("Cache unavailable", result.message)


class CheckCeleryTestCase(TestCase):
    @patch("open_inwoner.healthchecks.checks.current_app")
    def test_celery_check_success(self, mock_app):
        mock_app.control.ping.return_value = [{"worker1": {"ok": "pong"}}]

        result = check_celery()
        self.assertEqual(result.name, "celery")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "ok")

    @patch("open_inwoner.healthchecks.checks.current_app")
    def test_celery_check_no_workers(self, mock_app):
        mock_app.control.ping.return_value = []

        result = check_celery()
        self.assertEqual(result.name, "celery")
        self.assertFalse(result.success)
        self.assertIn("no workers available", result.message)

    @patch("open_inwoner.healthchecks.checks.current_app")
    def test_celery_check_failure(self, mock_app):
        mock_app.control.ping.side_effect = Exception("Broker unreachable")

        result = check_celery()
        self.assertEqual(result.name, "celery")
        self.assertFalse(result.success)
        self.assertIn("Broker unreachable", result.message)
