import logging  # noqa: TID251
from unittest.mock import Mock, patch

from django.test import TestCase

import sentry_sdk

from open_inwoner.conf.structlog_sentry import SentryStructlogProcessor


class SentryStructlogProcessorTest(TestCase):
    def setUp(self):
        self.processor = SentryStructlogProcessor(level=logging.ERROR, active=True)
        self.call_processor = lambda event_dict: self.processor(
            Mock(), "error", event_dict
        )

    def test_disabled_processor_skips_capture_and_returns_event_unchanged(self):
        processor = SentryStructlogProcessor(active=False)
        call_disabled = lambda event_dict: processor(Mock(), "error", event_dict)
        event_dict = {
            "event": "test",
            "exc_info": (ValueError, ValueError("test"), None),
        }

        with patch.object(sentry_sdk, "capture_exception") as mock_capture:
            result = call_disabled(event_dict)

            mock_capture.assert_not_called()
            self.assertEqual(result, event_dict)

    def test_ignored_loggers_skip_capture(self):
        event_dict = {
            "event": "test",
            "logger": "log_outgoing_requests",
            "level": "error",
            "exc_info": (ValueError, ValueError("test"), None),
        }

        with patch.object(sentry_sdk, "capture_exception") as mock_capture:
            result = self.call_processor(event_dict)

            mock_capture.assert_not_called()
            self.assertNotIn("sentry_event_id", result)

    def test_warning_level_exceptions_not_captured_when_threshold_is_error(self):
        event_dict = {
            "event": "test",
            "level": "warning",
            "exc_info": (ValueError, ValueError("test"), None),
        }

        with patch.object(sentry_sdk, "capture_exception") as mock_capture:
            result = self.call_processor(event_dict)

            mock_capture.assert_not_called()
            self.assertNotIn("sentry_event_id", result)

    def test_events_without_exc_info_skip_capture(self):
        event_dict = {"event": "test", "level": "error"}

        with patch.object(sentry_sdk, "capture_exception") as mock_capture:
            result = self.call_processor(event_dict)

            mock_capture.assert_not_called()
            self.assertNotIn("sentry_event_id", result)

    def test_error_level_exception_captured_and_event_id_added(self):
        exc = ValueError("test error")
        exc_info = (type(exc), exc, exc.__traceback__)
        event_dict = {"event": "test", "level": "error", "exc_info": exc_info}

        with patch.object(
            sentry_sdk, "capture_exception", return_value="test-event-id"
        ):
            result = self.call_processor(event_dict)

            self.assertEqual(result["sentry_event_id"], "test-event-id")

    def test_exc_info_tuple_passes_exception_instance_to_sentry(self):
        exc = ValueError("test")
        exc_info = (type(exc), exc, exc.__traceback__)
        event_dict = {"event": "test", "level": "error", "exc_info": exc_info}

        with patch.object(
            sentry_sdk, "capture_exception", return_value="test-id"
        ) as mock_capture:
            self.call_processor(event_dict)

            mock_capture.assert_called_once()
            args = mock_capture.call_args[0]
            self.assertIsInstance(args[0], ValueError)

    def test_exc_info_exception_object_captured_to_sentry(self):
        exc = ValueError("test")
        event_dict = {"event": "test", "level": "error", "exc_info": exc}

        with patch.object(sentry_sdk, "capture_exception", return_value="test-id"):
            result = self.call_processor(event_dict)

            self.assertEqual(result["sentry_event_id"], "test-id")

    def test_exc_info_true_uses_sys_exc_info_to_capture_current_exception(self):
        try:
            raise ValueError("test")
        except ValueError:
            event_dict = {"event": "test", "level": "error", "exc_info": True}

            with patch.object(sentry_sdk, "capture_exception", return_value="test-id"):
                result = self.call_processor(event_dict)

                self.assertEqual(result["sentry_event_id"], "test-id")

    def test_invalid_exc_info_string_skips_capture(self):
        event_dict = {"event": "test", "level": "error", "exc_info": "invalid"}

        with patch.object(sentry_sdk, "capture_exception") as mock_capture:
            result = self.call_processor(event_dict)

            mock_capture.assert_not_called()
            self.assertNotIn("sentry_event_id", result)

    def test_empty_exc_info_tuple_skips_capture(self):
        event_dict = {"event": "test", "level": "error", "exc_info": (None, None, None)}

        with patch.object(sentry_sdk, "capture_exception") as mock_capture:
            result = self.call_processor(event_dict)

            mock_capture.assert_not_called()
            self.assertNotIn("sentry_event_id", result)

    def test_event_context_fields_added_to_sentry_scope_as_extras_and_tags(self):
        exc = ValueError("test")
        event_dict = {
            "event": "test error",
            "level": "error",
            "exc_info": (type(exc), exc, exc.__traceback__),
            "user_id": 123,
            "request_id": "abc-123",
        }

        mock_scope = Mock()
        with (
            patch.object(sentry_sdk, "push_scope") as mock_push_scope,
            patch.object(sentry_sdk, "capture_exception", return_value="test-id"),
        ):
            mock_push_scope.return_value.__enter__.return_value = mock_scope

            self.call_processor(event_dict)

            mock_scope.set_extra.assert_any_call("user_id", 123)
            mock_scope.set_extra.assert_any_call("request_id", "abc-123")
            mock_scope.set_tag.assert_called_once_with("log_message", "test error")


class MakeSafeForSentryTest(TestCase):
    def setUp(self):
        self.processor = SentryStructlogProcessor()

    def test_primitives_passed_through_and_collections_recursed_and_objects_replaced_with_placeholders(
        self,
    ):
        mock_obj = Mock(__class__=Mock(__name__="CustomClass"))

        test_cases = [
            # (input, expected_output, description)
            (None, None, "None passthrough"),
            (True, True, "bool passthrough"),
            (42, 42, "int passthrough"),
            (3.14, 3.14, "float passthrough"),
            ("test", "test", "str passthrough"),
            (
                {"key": "value", "nested": {"inner": 123}},
                {"key": "value", "nested": {"inner": 123}},
                "dict recursion",
            ),
            ([1, "two", {"three": 3}], [1, "two", {"three": 3}], "list recursion"),
            ((1, 2, 3), [1, 2, 3], "tuple to list conversion"),
            (mock_obj, "<Mock>", "object placeholder"),
            (
                {"user": mock_obj, "items": [1, mock_obj]},
                {"user": "<Mock>", "items": [1, "<Mock>"]},
                "nested with objects",
            ),
        ]

        for input_val, expected, description in test_cases:
            with self.subTest(description):
                result = self.processor._make_safe_for_sentry(input_val)
                self.assertEqual(result, expected, f"Failed: {description}")

        # Sets converted to lists - check sorted since set order is non-deterministic
        set_result = self.processor._make_safe_for_sentry({1, 2, 3})
        self.assertEqual(sorted(set_result), [1, 2, 3])  # type: ignore

    def test_deeply_nested_structures_stop_at_max_depth_to_prevent_recursion_errors(
        self,
    ):
        deep_dict = {"level": 0}
        current = deep_dict
        for i in range(15):
            current["nested"] = {"level": i + 1}
            current = current["nested"]

        result = self.processor._make_safe_for_sentry(deep_dict, max_depth=5)

        self.assertIn("<max_depth_exceeded>", str(result))


class BeforeSendTest(TestCase):
    def test_events_with_exceptions_pass_through(self):
        event = {"exception": {"values": [{"type": "ValueError"}]}, "message": "test"}
        hint = {}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertEqual(result, event)

    def test_duplicate_messages_containing_sentry_event_id_filtered_out(self):
        event = {"message": "Error occurred sentry_event_id='abc-123'"}
        hint = {}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertIsNone(result)

    def test_log_records_with_sentry_event_id_in_message_filtered_as_duplicates(self):
        mock_log_record = Mock()
        mock_log_record.name = "test.logger"
        mock_log_record.message = "Error sentry_event_id='abc-123'"
        mock_log_record.getMessage.return_value = "Error sentry_event_id='abc-123'"
        mock_log_record.exc_info = None

        event = {"message": "test"}
        hint = {"log_record": mock_log_record}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertIsNone(result)

    def test_ignored_loggers_filtered_out(self):
        mock_log_record = Mock()
        mock_log_record.name = "log_outgoing_requests"

        event = {"message": "test"}
        hint = {"log_record": mock_log_record}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertIsNone(result)

    def test_log_records_with_exc_info_filtered_because_already_captured_by_processor(
        self,
    ):
        mock_log_record = Mock()
        mock_log_record.name = "test.logger"
        mock_log_record.exc_info = (ValueError, ValueError("test"), None)
        mock_log_record.message = "test"
        mock_log_record.getMessage.return_value = "test"

        event = {"message": "test"}
        hint = {"log_record": mock_log_record}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertIsNone(result)

    def test_regular_log_messages_without_duplicates_pass_through(self):
        mock_log_record = Mock()
        mock_log_record.name = "test.logger"
        mock_log_record.message = "Regular error message"
        mock_log_record.getMessage.return_value = "Regular error message"
        mock_log_record.exc_info = None

        event = {"message": "Regular error message"}
        hint = {"log_record": mock_log_record}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertEqual(result, event)

    def test_log_records_with_sentry_event_id_in_formatted_message_filtered_as_duplicates(
        self,
    ):
        mock_log_record = Mock()
        mock_log_record.name = "test.logger"
        mock_log_record.message = "Error occurred"
        mock_log_record.getMessage.return_value = (
            "Error occurred sentry_event_id='abc-123'"
        )
        mock_log_record.exc_info = None

        event = {"message": "test"}
        hint = {"log_record": mock_log_record}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertIsNone(result)

    def test_exceptions_in_get_message_handled_gracefully_without_raising(self):
        mock_log_record = Mock()
        mock_log_record.name = "test.logger"
        mock_log_record.message = "test"
        mock_log_record.getMessage.side_effect = TypeError("Format error")
        mock_log_record.exc_info = None

        event = {"message": "test"}
        hint = {"log_record": mock_log_record}

        result = SentryStructlogProcessor.before_send(event, hint)

        self.assertEqual(result, event)
