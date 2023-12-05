import os

from django.test import TestCase

from open_inwoner.cms.tests import cms_tools
from open_inwoner.utils.test import temp_media_root
from open_inwoner.utils.tests.factories import FilerImageFactory

from ..cms_plugins import BannerImagePlugin, BannerTextPlugin


@temp_media_root()
class TestBannerImage(TestCase):
    def test_banner_image_is_rendered_in_plugin(self):
        image = FilerImageFactory()
        html, context = cms_tools.render_plugin(
            BannerImagePlugin, plugin_data={"image": image}
        )
        self.assertIn(os.path.basename(image.file.name), html)
        self.assertIn('<aside class="banner"', html)

    def test_banner_image_with_specific_height(self):
        image = FilerImageFactory()
        image_height = 40
        html, context = cms_tools.render_plugin(
            BannerImagePlugin,
            plugin_data={"image": image, "image_height": image_height},
        )

        self.assertIn(os.path.basename(image.file.name), html)
        self.assertIn(f'height="{image_height}"', html)
        self.assertIn('<aside class="banner"', html)


class TestBannerText(TestCase):
    def test_banner_text_is_rendered_in_plugin(self):
        title = "A title for the banner"
        html, context = cms_tools.render_plugin(
            BannerTextPlugin, plugin_data={"title": title}
        )

        self.assertIn(f"<h1>{title} </h1>", html)

    def test_banner_text_with_description_is_rendered_in_plugin(self):
        title = "A title for the banner"
        description = "Text for description"
        html, context = cms_tools.render_plugin(
            BannerTextPlugin, plugin_data={"title": title, "description": description}
        )

        self.assertIn(f"<h1>{title} </h1>", html)
        self.assertIn(f'<p class="p">{description}</p>', html)
