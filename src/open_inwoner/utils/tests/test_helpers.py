import logging

from django.test import TestCase

from timeline_logger.models import TimelineLog

from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin, Lookups


class AssertTimelineLogMixinTest(AssertTimelineLogMixin, TestCase):
    def test_assertTimelineLog(self):
        TimelineLog.objects.create(
            extra_data={"message": "foo bar", "log_level": logging.ERROR}
        )
        TimelineLog.objects.create(
            extra_data={"message": "bazz buzz", "log_level": logging.ERROR}
        )
        TimelineLog.objects.create(
            extra_data={"message": "bazz buzz", "log_level": logging.WARNING}
        )
        with self.subTest("basic"):
            self.assertTimelineLog("foo bar")
            self.assertTimelineLog("foo bar", level=logging.ERROR)
            self.assertTimelineLog("bazz buzz", level=logging.WARNING)

        with self.subTest("with lookup"):
            self.assertTimelineLog("bar", lookup=Lookups.endswith)
            self.assertTimelineLog("bar", lookup=Lookups.endswith, level=logging.ERROR)

        with self.subTest("not found"):
            with self.assertRaisesRegex(
                AssertionError, r"^cannot find TimelineLog with"
            ):
                self.assertTimelineLog("foo bar", level=logging.INFO)

        with self.subTest("multiple"):
            with self.assertRaisesRegex(AssertionError, r"^found 2 TimelineLogs with"):
                self.assertTimelineLog("bazz buzz")
