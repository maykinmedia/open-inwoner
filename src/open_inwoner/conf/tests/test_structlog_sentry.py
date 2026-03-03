import sys
from unittest.mock import MagicMock, Mock, patch

from django.test import TestCase

from open_inwoner.conf.structlog_sentry import SentryStructlogProcessor


@patch("open_inwoner.conf.structlog_sentry.sentry_sdk")
class SentryStructlogProcessorTests(TestCase):
    def setUp(self):
        self.processor = SentryStructlogProcessor()
        self.logger = Mock()
        self.method_name = "error"

    def test_events_without_exc_info_are_passed_through_unchanged(self, mock_sentry):
        event_dict = {"event": "Something happened", "level": "error"}

        result = self.processor(self.logger, self.method_name, event_dict)

        mock_sentry.capture_exception.assert_not_called()
        mock_sentry.capture_event.assert_not_called()
        self.assertEqual(result, event_dict)

    def test_sentry_skip_flag_prevents_capture_and_is_removed_from_result(
        self, mock_sentry
    ):
        exc_info = self._create_exception()
        event_dict = {
            "event": "Test error",
            "level": "error",
            "exc_info": exc_info,
            "sentry_skip": True,
        }

        result = self.processor(self.logger, self.method_name, event_dict)

        mock_sentry.capture_exception.assert_not_called()
        mock_sentry.capture_event.assert_not_called()
        self.assertNotIn("sentry_skip", result)

    def test_events_below_error_level_are_not_sent_to_sentry(self, mock_sentry):
        exc_info = self._create_exception()
        event_dict = {
            "event": "Test warning",
            "level": "warning",
            "exc_info": exc_info,
        }

        self.processor(self.logger, self.method_name, event_dict)

        mock_sentry.capture_exception.assert_not_called()
        mock_sentry.capture_event.assert_not_called()

    def test_event_message_becomes_sentry_title_with_context_as_extras(
        self, mock_sentry
    ):
        exc_info = self._create_exception()
        event_dict = {
            "event": "Invalid externe taak",
            "level": "error",
            "exc_info": exc_info,
            "object_type_uuid": "123-456",
            "request_id": "req-789",
        }

        mock_scope = MagicMock()
        mock_sentry.push_scope.return_value.__enter__.return_value = mock_scope
        mock_sentry.get_client.return_value.options = {}

        mock_event = {
            "exception": {"values": [{"value": "Original exception message"}]},
            "message": "Original message",
        }
        mock_sentry.utils.event_from_exception.return_value = (
            mock_event,
            {"exc_info": exc_info},
        )
        mock_sentry.capture_event.return_value = "event-id-123"

        result = self.processor(self.logger, self.method_name, event_dict)

        mock_sentry.push_scope.assert_called_once()
        mock_scope.set_extra.assert_any_call("object_type_uuid", "123-456")
        mock_scope.set_extra.assert_any_call("request_id", "req-789")
        mock_scope.set_tag.assert_called_once_with(
            "log_message", "Invalid externe taak"
        )
        self.assertEqual(mock_event["message"], "Invalid externe taak")
        self.assertEqual(
            mock_event["exception"]["values"][0]["value"],
            "Original exception message",
        )
        self.assertEqual(result["sentry_event_id"], "event-id-123")

    def test_exception_without_event_message_uses_capture_exception_directly(
        self, mock_sentry
    ):
        exc_info = self._create_exception()
        event_dict = {
            "level": "error",
            "exc_info": exc_info,
        }

        mock_scope = MagicMock()
        mock_sentry.push_scope.return_value.__enter__.return_value = mock_scope
        mock_sentry.capture_exception.return_value = "event-id-456"

        result = self.processor(self.logger, self.method_name, event_dict)

        mock_sentry.capture_exception.assert_called_once()
        mock_sentry.capture_event.assert_not_called()
        self.assertEqual(result["sentry_event_id"], "event-id-456")

    def test_exc_info_as_baseexception_instance_is_converted_to_tuple(
        self, mock_sentry
    ):
        try:
            raise ValueError("Test error")
        except ValueError as e:
            exc = e

        event_dict = {
            "event": "Test error",
            "level": "error",
            "exc_info": exc,
        }

        mock_scope = MagicMock()
        mock_sentry.push_scope.return_value.__enter__.return_value = mock_scope
        mock_sentry.get_client.return_value.options = {}
        mock_event = {
            "exception": {"values": [{"value": "Original"}]},
            "message": "Original",
        }
        mock_sentry.utils.event_from_exception.return_value = (
            mock_event,
            {"exc_info": exc},
        )
        mock_sentry.capture_event.return_value = "event-id-789"

        result = self.processor(self.logger, self.method_name, event_dict)

        mock_sentry.push_scope.assert_called_once()
        self.assertEqual(result["sentry_event_id"], "event-id-789")

    def test_exc_info_true_calls_sys_exc_info_to_get_current_exception(
        self, mock_sentry
    ):
        try:
            raise ValueError("Test error")
        except ValueError:
            event_dict = {
                "event": "Test error",
                "level": "error",
                "exc_info": True,
            }

            mock_scope = MagicMock()
            mock_sentry.push_scope.return_value.__enter__.return_value = mock_scope
            mock_sentry.get_client.return_value.options = {}
            mock_event = {
                "exception": {"values": [{"value": "Original"}]},
                "message": "Original",
            }
            mock_sentry.utils.event_from_exception.return_value = (
                mock_event,
                {},
            )
            mock_sentry.capture_event.return_value = "event-id-abc"

            result = self.processor(self.logger, self.method_name, event_dict)

            mock_sentry.push_scope.assert_called_once()
            self.assertEqual(result["sentry_event_id"], "event-id-abc")

    def test_before_send_allows_events_with_exceptions(self, _mock_sentry):
        event = {"exception": {"values": [{"type": "ValueError"}]}}
        hint = {}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertEqual(result, event)

    def test_before_send_filters_message_events_containing_sentry_event_id(
        self, _mock_sentry
    ):
        event = {
            "message": "Some log message with sentry_event_id='abc-123' in it",
        }
        hint = {}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertIsNone(result)

    def test_before_send_filters_log_records_with_exc_info(self, _mock_sentry):
        event = {"message": "Some message"}
        log_record = Mock()
        log_record.exc_info = (ValueError, ValueError("test"), None)
        hint = {"log_record": log_record}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertIsNone(result)

    def test_before_send_filters_log_records_with_sentry_event_id_in_message_attr(
        self, _mock_sentry
    ):
        event = {"message": "Some message"}
        log_record = Mock()
        log_record.exc_info = None
        log_record.message = "Log with sentry_event_id='xyz'"
        hint = {"log_record": log_record}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertIsNone(result)

    def test_before_send_filters_log_records_with_sentry_event_id_in_get_message(
        self, _mock_sentry
    ):
        event = {"message": "Some message"}
        log_record = Mock()
        log_record.exc_info = None
        log_record.message = "Clean message"
        log_record.getMessage.return_value = "Message with sentry_event_id='123'"
        hint = {"log_record": log_record}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertIsNone(result)

    def test_before_send_allows_normal_log_messages_without_markers(self, _mock_sentry):
        event = {"message": "A normal log message without any markers"}
        log_record = Mock()
        log_record.exc_info = None
        log_record.message = "Normal message"
        log_record.getMessage.return_value = "Normal message"
        hint = {"log_record": log_record}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertEqual(result, event)

    def _create_exception(self):
        """Helper to create a valid exception tuple."""
        try:
            raise ValueError("Test exception")
        except ValueError:
            return sys.exc_info()
