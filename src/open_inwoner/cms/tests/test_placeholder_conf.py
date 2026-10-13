from django.conf import settings
from django.test import TestCase

from cms.plugin_pool import plugin_pool


class PlaceholderConfTests(TestCase):
    def test_allowed_plugins_are_offered_in_plugin_picker(self):
        # The "add plugin" picker of every placeholder is built from
        # `registered_plugins`, before narrowing it down to the plugins allowed
        # in that placeholder, so a plugin missing here can't be added anywhere.
        registered = {plugin.__name__ for plugin in plugin_pool.registered_plugins}

        missing = {
            slot: sorted(set(conf["plugins"]) - registered)
            for slot, conf in settings.CMS_PLACEHOLDER_CONF.items()
            if "plugins" in conf
        }

        self.assertEqual(
            missing,
            {slot: [] for slot in missing},
        )
