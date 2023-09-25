from django.test import TestCase

from .factories import VideoFactory


class VideoTests(TestCase):
    def test_str(self):
        video = VideoFactory.build(link_id="123", title="Anne")
        self.assertEqual(str(video), "Anne (vimeo: 123, nl)")

    def test_str_no_title(self):
        video = VideoFactory.build(link_id="123", title="")
        self.assertEqual(str(video), "123")

    def test_youtube(self):
        video = VideoFactory.build(link_id="123", title="", player_type="youtube")
        self.assertEqual(
            video.player_url,
            "https://www.youtube.com/embed/123?enablejsapi=1&modestbranding=1",
        )

    def test_external_url(self):
        video = VideoFactory.build()
        self.assertEqual(video.external_url, "https://vimeo.com/" + video.link_id)

    def test_player_url(self):
        video = VideoFactory.build()
        self.assertEqual(
            video.player_url, "https://player.vimeo.com/video/" + video.link_id
        )
