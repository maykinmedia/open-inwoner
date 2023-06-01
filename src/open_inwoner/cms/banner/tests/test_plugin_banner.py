import os

from django.conf import settings
from django.core.files import File
from django.test import TestCase

from filer.models.imagemodels import Image as FilerImage
from PIL import Image

from open_inwoner.cms.tests import cms_tools
from open_inwoner.utils.test import temp_media_root

from ..cms_plugins import BannerImagePlugin, BannerTextPlugin


@temp_media_root()
class TestBannerImage(TestCase):
    def test_banner_image_is_rendered_in_plugin(self):
        pil_image = Image.new("RGB", (10, 10))
        tmp_file_path = "{}/{}".format(settings.MEDIA_ROOT, "tmp.jpg")
        pil_image.save(tmp_file_path, "JPEG")

        tmp_image_file = open(tmp_file_path, "rb")
        file_obj = File(tmp_image_file)
        instance = FilerImage()
        instance.file.save("image.jpg", file_obj)

        html, context = cms_tools.render_plugin(
            BannerImagePlugin, plugin_data={"image": instance}
        )

        self.assertIn(os.path.basename(instance.file.name), html)
        self.assertIn('<aside class="banner"', html)

    def test_banner_image_with_specific_height(self):
        pil_image = Image.new("RGB", (10, 10))
        tmp_file_path = "{}/{}".format(settings.MEDIA_ROOT, "tmp.jpg")
        pil_image.save(tmp_file_path, "JPEG")

        tmp_image_file = open(tmp_file_path, "rb")
        file_obj = File(tmp_image_file)
        instance = FilerImage()
        instance.file.save("image.jpg", file_obj)

        image_height = 40

        html, context = cms_tools.render_plugin(
            BannerImagePlugin,
            plugin_data={"image": instance, "image_height": image_height},
        )

        self.assertIn(os.path.basename(instance.file.name), html)
        self.assertIn(f'height="{image_height}"', html)
        self.assertIn('<aside class="banner"', html)


class TestBannerText(TestCase):
    def test_banner_text_is_rendered_in_plugin(self):
        title = "A title for the banner"

        html, context = cms_tools.render_plugin(
            BannerTextPlugin, plugin_data={"title": title}
        )

        self.assertIn(f'<h1 class="h1">{title} </h1>', html)

    def test_banner_text_with_description_is_rendered_in_plugin(self):
        title = "A title for the banner"
        description = "Text for description"

        html, context = cms_tools.render_plugin(
            BannerTextPlugin, plugin_data={"title": title, "description": description}
        )

        self.assertIn(f'<h1 class="h1">{title} </h1>', html)
        self.assertIn(f'<p class="p">{description}</p>', html)
