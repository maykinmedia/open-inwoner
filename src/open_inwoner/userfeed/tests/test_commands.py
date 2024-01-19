from datetime import datetime
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import make_aware

from freezegun import freeze_time

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.feed import get_feed
from open_inwoner.userfeed.management.commands.process_feed_updates import (
    auto_expire_items,
)
from open_inwoner.userfeed.tests.factories import FeedItemDataFactory


class CommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_command_process_feed_updates(self):
        """
        check if all processors are called but do the actual testing individually
        """
        with patch(
            "open_inwoner.userfeed.management.commands.process_feed_updates.auto_expire_items"
        ) as mock_auto_expire_items:
            call_command("process_feed_updates")

            mock_auto_expire_items.assert_called_once()

    @freeze_time("2000-01-01")
    def test_auto_expire(self):
        user = UserFactory()

        d = make_aware(datetime(2001, 1, 1))
        item_do_expire = FeedItemDataFactory(user=user, auto_expire_at=d)
        item_not_expire = FeedItemDataFactory(user=user)

        auto_expire_items()

        item_do_expire.refresh_from_db()
        item_not_expire.refresh_from_db()

        # no changes
        self.assertEqual(item_do_expire.is_completed, False)
        self.assertEqual(item_not_expire.is_completed, False)

        # move past expiry
        with freeze_time("2002-01-01"):
            auto_expire_items()

            item_do_expire.refresh_from_db()
            item_not_expire.refresh_from_db()

            # expiring item expired
            self.assertEqual(item_do_expire.is_completed, True)
            self.assertEqual(item_not_expire.is_completed, False)

    def test_command_add_feed_message_test(self):
        # sanity check
        call_command(
            "add_feed_message",
            "--user",
            self.user.id,
            "--message",
            "Hello",
            "--title",
            "World",
            "--url",
            "http://foo.bar",
        )
        feed = get_feed(self.user)
        self.assertEqual(feed.total_items, 1)

        item = feed.items[0]
        self.assertEqual(item.type, FeedItemType.message_simple)
        self.assertEqual(item.message, "Hello")
        self.assertEqual(item.title, "World")
        self.assertEqual(item.action_url, "http://foo.bar")
