from django.test import TestCase

from open_inwoner.core.cms.cms_plugins.videoplayer.cms_plugins import (
    VideoPlayerPlugin,
)
from open_inwoner.core.cms.utils import cms_test_utils as cms_tools
from open_inwoner.media.tests.factories import VideoFactory


class TestVideoPlayerPlugin(TestCase):
    def test_plugin(self):
        video = VideoFactory()
        html, context = cms_tools.render_plugin(
            VideoPlayerPlugin, plugin_data={"video": video}
        )
        self.assertIn(video.player_url, html)
        self.assertIn("<iframe ", html)
