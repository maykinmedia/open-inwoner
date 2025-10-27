from django.template import Context
from django.test import TestCase, override_settings

from cms.api import add_plugin
from cms.models import Placeholder
from cms.plugin_rendering import ContentRenderer
from cms.utils.plugins import get_plugins

from open_inwoner.cms.plugins.cms_plugins import CMSLinkPlugin, LinkPlugin
from open_inwoner.cms.tests import cms_tools


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CMSLinkPluginTest(TestCase):
    def test_cms_link_plugin(self):
        # Create the container plugin
        placeholder = Placeholder.objects.create(slot="test")
        container_plugin = add_plugin(
            placeholder,
            CMSLinkPlugin,
            "nl",
            title="Test link plugin",
        )

        # Add child Link plugins
        # Note: name is a ProsemirrorModelField, so we pass a document structure
        add_plugin(
            placeholder,
            LinkPlugin,
            "nl",
            target=container_plugin,  # Set parent plugin
            position="last-child",
            name={
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "First Link"}],
                    }
                ],
            },
            external_link="https://example.com/first",
            icon="arrow_forward",
        )
        add_plugin(
            placeholder,
            LinkPlugin,
            "nl",
            target=container_plugin,  # Set parent plugin
            position="last-child",
            name={
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Second Link"}],
                    }
                ],
            },
            external_link="https://example.com/second",
            icon="check",
        )

        request = cms_tools.get_request()

        # Get plugins - this loads the tree structure including child plugins
        plugins = list(get_plugins(request, placeholder, template=None, lang="nl"))

        # Render the first (container) plugin
        renderer = ContentRenderer(request=request)
        context = Context({"request": request})
        html = renderer.render_plugin(plugins[0], context)

        # Test output
        self.assertIn("Test link plugin", html)
        self.assertIn("First Link", html)
        self.assertIn("Second Link", html)
        self.assertIn("https://example.com/first", html)
        self.assertIn("https://example.com/second", html)
        self.assertIn("arrow_forward", html)
        self.assertIn("check", html)
