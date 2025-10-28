import json

from django.test import TestCase

from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.plugins.cms_plugins import UserFeedPlugin
from open_inwoner.cms.tests import cms_tools
from open_inwoner.userfeed.hooks.common import simple_message


class TestUserFeedPlugin(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_plugin(self):
        simple_message(self.user, "Hello", title="Test message", url="http://foo.bar")
        html, context = cms_tools.render_plugin(
            UserFeedPlugin, plugin_data={}, user=self.user
        )

        feed_json = context["userfeed_item_list_json"]
        feed = json.loads(feed_json)
        self.assertEqual(len(feed), 1)

        self.assertIn("Hello", html)
        self.assertIn("Test message", html)
        self.assertIn("http://foo.bar", html)

        pyquery = PyQuery(html)

        # make sure the json script has the correct content
        items = pyquery.find("action-list").attr("actions")
        self.assertEqual(
            items,
            '[{"title": "Test message", "message": "Hello", "action_text": "", "action_url": "http://foo.bar"}]',
        )

    def test_multiple_plugin(self):
        simple_message(self.user, "Hi", title="My message", url="http://test.com")
        simple_message(
            self.user, "TEST", title="TEST MESSAGE 2", url="http://example.com"
        )

        html, context = cms_tools.render_plugin(
            UserFeedPlugin, plugin_data={}, user=self.user
        )
        feed_json = context["userfeed_item_list_json"]
        feed = json.loads(feed_json)
        self.assertEqual(len(feed), 2)  # two items

        self.assertIn("Hi", html)
        self.assertIn("My message", html)
        self.assertIn("http://test.com", html)

        self.assertIn("TEST", html)
        self.assertIn("TEST MESSAGE 2", html)
        self.assertIn("http://example.com", html)

        pyquery = PyQuery(html)

        # make sure the json script has the correct content
        items = pyquery.find("action-list").attr("actions")
        self.assertEqual(
            items,
            '[{"title": "My message", "message": "Hi", "action_text": "", "action_url": "http://test.com"}, {"title": "TEST MESSAGE 2", "message": "TEST", "action_text": "", "action_url": "http://example.com"}]',
        )
