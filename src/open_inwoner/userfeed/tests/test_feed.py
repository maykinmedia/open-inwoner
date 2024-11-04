from django.test import TestCase
from django.utils.html import strip_tags
from django.utils.translation import ngettext

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.constants import StatusIndicators
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.feed import get_feed
from open_inwoner.userfeed.hooks.common import simple_message
from open_inwoner.userfeed.models import FeedItemData
from open_inwoner.userfeed.tests.factories import FeedItemDataFactory


class FeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_get_feed__and__simple_message(self):
        # our record
        simple_message(self.user, "Hello", title="Test message", url="http://foo.bar")
        data = FeedItemData.objects.get()

        # extra data
        FeedItemDataFactory(user=UserFactory())

        feed = get_feed(self.user)
        self.assertEqual(feed.total_items, 1)
        self.assertEqual(feed.has_display(), True)
        self.assertEqual(len(feed.summary), 1)

        # check item
        item = feed.items[0]
        self.assertEqual(item.type, FeedItemType.message_simple)
        self.assertEqual(item.action_required, False)
        self.assertEqual(item.is_completed, False)
        self.assertEqual(item.message, "Hello")
        self.assertEqual(item.title, "Test message")
        self.assertEqual(item.action_url, "http://foo.bar")
        self.assertEqual(item.status_text, "")
        self.assertEqual(item.status_indicator, StatusIndicators.info)

        # check summary
        summary = feed.summary[0]
        expected = ngettext(
            "There is {count} message",
            "There are {count} messages",
            1,
        ).format(count=1)
        self.assertEqual(strip_tags(summary), expected)

        # mark as completed
        item.mark_completed()
        self.assertEqual(item.is_completed, True)

        # not visible anymore
        feed = get_feed(self.user)
        self.assertEqual(feed.total_items, 0)
