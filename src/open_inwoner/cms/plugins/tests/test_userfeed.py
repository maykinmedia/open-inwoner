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
        self.assertEqual(len(feed_json), 1)

        self.assertIn("Hello", html)
        self.assertIn("Test message", html)
        self.assertIn("http://foo.bar", html)

        pyquery = PyQuery(html)

        # make sure the oip-action-list web component is present
        action_list = pyquery.find("oip-action-list")
        self.assertEqual(len(action_list), 1)

        # validate actions length
        actions = pyquery.find("oip-action")
        self.assertEqual(len(actions), 1)

        # validate actions attrs
        self.assertEqual(actions.attr("title"), "Test message")
        self.assertEqual(actions.attr("message"), "Hello")
        self.assertEqual(actions.attr("action-url"), "http://foo.bar")

    def test_multiple_plugin(self):
        simple_message(self.user, "Hi", title="My message", url="http://test.com")
        simple_message(
            self.user, "TEST", title="TEST MESSAGE 2", url="http://example.com"
        )

        html, context = cms_tools.render_plugin(
            UserFeedPlugin, plugin_data={}, user=self.user
        )
        feed = context["userfeed_item_list_json"]
        self.assertEqual(len(feed), 2)  # two items

        self.assertIn("Hi", html)
        self.assertIn("My message", html)
        self.assertIn("http://test.com", html)

        self.assertIn("TEST", html)
        self.assertIn("TEST MESSAGE 2", html)
        self.assertIn("http://example.com", html)

        pyquery = PyQuery(html)

        # make sure the oip-action-list web component is present
        action_list = pyquery.find("oip-action-list")
        self.assertEqual(len(action_list), 1)

        # validate actions length
        actions = pyquery.find("oip-action")
        self.assertEqual(len(actions), 2)

        # validate actions attrs
        first_action = actions.eq(0)
        self.assertEqual(first_action.attr("title"), "My message")
        self.assertEqual(first_action.attr("message"), "Hi")
        self.assertEqual(first_action.attr("action-url"), "http://test.com")

        last_action = actions.eq(1)
        self.assertEqual(last_action.attr("title"), "TEST MESSAGE 2")
        self.assertEqual(last_action.attr("message"), "TEST")
        self.assertEqual(last_action.attr("action-url"), "http://example.com")
