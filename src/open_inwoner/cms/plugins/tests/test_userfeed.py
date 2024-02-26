from django.test import TestCase
from django.utils.html import strip_tags
from django.utils.translation import ngettext

from pyquery import PyQuery as PQ

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.tests import cms_tools
from open_inwoner.userfeed.hooks.common import simple_message

from ..cms_plugins import UserFeedPlugin


class TestUserFeedPlugin(TestCase):
    def test_plugin(self):
        user = UserFactory()
        simple_message(user, "Hello", title="Test message", url="http://foo.bar")

        html, context = cms_tools.render_plugin(
            UserFeedPlugin, plugin_data={}, user=user
        )

        feed = context["userfeed"]
        self.assertEqual(feed.total_items, 1)

        self.assertIn("Test message", html)
        self.assertIn("Hello", html)

        pyquery = PQ(html)

        # test summary
        summaries = pyquery.find(".userfeed__summary .userfeed__list-item")
        self.assertEqual(len(summaries), 1)

        summary = summaries.text()
        expected = ngettext(
            "There is {count} message",
            "There are {count} messages",
            1,
        ).format(count=1)
        self.assertEqual(strip_tags(summary), expected)

        # test item
        items = pyquery.find(".card-container .card")
        self.assertEqual(len(items), 1)

        title = items.find("p.tabled__value").text()
        self.assertEqual(title, "Test message")

        message = items.find(".userfeed__heading").text()
        self.assertEqual(message, "Hello")

        action_url = items[0].attrib["href"]
        self.assertEqual(action_url, "http://foo.bar")
