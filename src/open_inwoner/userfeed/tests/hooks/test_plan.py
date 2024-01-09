from datetime import date
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import ugettext as _

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.plans.tests.factories import PlanFactory
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.feed import get_feed
from open_inwoner.userfeed.hooks.plan import plan_completed, plan_expiring


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class FeedHookTest(TestCase):
    @patch(
        "open_inwoner.userfeed.feed.get_active_app_names", return_value=["collaborate"]
    )
    def test_plan_expires(self, mock_get_active_app_names: Mock):
        user = UserFactory()
        plan = PlanFactory(end_date=date.today())

        plan_expiring(user, plan)

        # check feed
        feed = get_feed(user)
        self.assertEqual(feed.total_items, 1)
        self.assertEqual(len(feed.summary), 1)

        # check item
        item = feed.items[0]
        self.assertEqual(item.type, FeedItemType.plan_expiring)
        self.assertEqual(item.action_required, True)
        self.assertEqual(item.is_completed, False)
        self.assertEqual(
            item.message,
            _("Plan deadline expires at {expire}").format(
                expire=plan.end_date.strftime("%x")
            ),
        )
        self.assertEqual(item.title, plan.title)
        self.assertEqual(
            item.action_url,
            reverse("collaborate:plan_detail", kwargs={"uuid": plan.uuid}),
        )

        # send duplicate notification
        plan_expiring(user, plan)

        feed = get_feed(user)

        # still only one item
        self.assertEqual(feed.total_items, 1)

        # mark as seen
        plan_completed(user, plan)

        # removed from feed
        self.assertEqual(get_feed(user).total_items, 0)

        # doesn't break on repeat
        plan_completed(user, plan)
        self.assertEqual(get_feed(user).total_items, 0)

        # plan got reactivated
        plan_expiring(user, plan)
        self.assertEqual(get_feed(user).total_items, 1)
