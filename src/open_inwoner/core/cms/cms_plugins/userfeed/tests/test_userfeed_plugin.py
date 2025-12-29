import json

from django.test import TestCase

from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.core.cms.cms_plugins.userfeed.cms_plugins import UserFeedPlugin
from open_inwoner.core.cms.utils import cms_test_utils as cms_tools
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

        # make sure the action-list web component is present
        action_list = pyquery.find("action-list")
        self.assertEqual(len(action_list), 1)
        self.assertEqual(action_list.attr("actions-id"), "userfeed_data")

        # check the script tag contains the correct JSON data
        script = pyquery.find("script#userfeed_data")
        self.assertEqual(len(script), 1)
        self.assertEqual(script.attr("type"), "application/json")

        script_content = json.loads(script.text())
        self.assertEqual(len(script_content), 1)
        self.assertEqual(script_content[0]["title"], "Test message")
        self.assertEqual(script_content[0]["message"], "Hello")
        self.assertEqual(script_content[0]["action_url"], "http://foo.bar")

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

        # make sure the action-list web component is present
        action_list = pyquery.find("action-list")
        self.assertEqual(len(action_list), 1)
        self.assertEqual(action_list.attr("actions-id"), "userfeed_data")

        # check the script tag contains the correct JSON data for both items
        script = pyquery.find("script#userfeed_data")
        self.assertEqual(len(script), 1)
        self.assertEqual(script.attr("type"), "application/json")

        script_content = json.loads(script.text())
        self.assertEqual(len(script_content), 2)
        self.assertEqual(script_content[0]["title"], "My message")
        self.assertEqual(script_content[0]["message"], "Hi")
        self.assertEqual(script_content[0]["action_url"], "http://test.com")
        self.assertEqual(script_content[1]["title"], "TEST MESSAGE 2")
        self.assertEqual(script_content[1]["message"], "TEST")
        self.assertEqual(script_content[1]["action_url"], "http://example.com")
