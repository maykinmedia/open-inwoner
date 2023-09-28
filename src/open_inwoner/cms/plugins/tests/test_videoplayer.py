from django.test import TestCase

from open_inwoner.cms.tests import cms_tools
from open_inwoner.media.tests.factories import VideoFactory

from ..cms_plugins import VideoPlayerPlugin


class TestVideoPlayerPlugin(TestCase):
    def test_plugin(self):
        video = VideoFactory()
        html, context = cms_tools.render_plugin(
            VideoPlayerPlugin, plugin_data={"video": video}
        )
        self.assertIn(video.player_url, html)
        self.assertIn("<iframe ", html)
