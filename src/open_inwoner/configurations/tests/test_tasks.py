from unittest.mock import patch

from django.test import TestCase

from open_inwoner.configurations.models import TimelineLogConfig
from open_inwoner.configurations.tasks import prune_timeline_logs
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin


class TestPruneTimelineLogsTask(AssertTimelineLogMixin, TestCase):
    def setUp(self):
        self.config = TimelineLogConfig.get_solo()
        self.config.automatically_prune_logs = True
        self.config.keep_days = 42
        self.config.save()

    def test_prune_timeline_logs_disabled(self):
        config = TimelineLogConfig.get_solo()
        config.automatically_prune_logs = False
        config.save()

        result = prune_timeline_logs()

        self.assertTimelineLog("aborted timeline log prune because flag is disabled")
        self.assertIsNone(result)

    @patch("open_inwoner.configurations.tasks.call_command")
    def test_prune_timeline_logs_enabled(self, mock_call_command):
        mock_call_command.return_value = None

        result = prune_timeline_logs()

        mock_call_command.assert_called_once()
        call_args = mock_call_command.call_args
        self.assertEqual(call_args[0][0], "prune_timeline_logs")
        self.assertEqual(call_args[1]["keep_days"], self.config.keep_days)

        self.assertTimelineLog("pruned timeline logs")
        self.assertIsInstance(result, str)

    def test_prune_timeline_logs_command_smoke_test(self):
        result = (
            prune_timeline_logs()
        )  # Assert we can actually run the managemant command
        self.assertTimelineLog("pruned timeline logs")

        self.assertEqual(
            result, "STDOUT:\nSuccessfully deleted 0 timeline logs.\n\nSTDERR:"
        )
