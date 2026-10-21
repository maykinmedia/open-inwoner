from django.test import TestCase, override_settings

import factory
from easy_thumbnails.alias import aliases
from easy_thumbnails.templatetags.thumbnail import thumbnail_url
from PIL import Image

from open_inwoner.utils.test import temp_media_root
from open_inwoner.utils.tests.factories import FilerImageFactory


@temp_media_root()
@override_settings(THUMBNAIL_DEBUG=True)  # raise thumbnailing errors, don't swallow
class ThumbnailTests(TestCase):
    def test_thumbnail_aliases_render_for_uploaded_images(self):
        # Regression test for Pillow/easy-thumbnails upgrades: covers the image
        # formats editors can upload, which each use a different Pillow codec.
        # The card-image alias is our main public-facing use of Pillow (product
        # cards on category, location and questionnaire pages).
        #
        # Inspect the generated file to guard against Pillow writing a format
        # or size we don't expect: sources without transparency are
        # thumbnailed to JPEG, transparent ones to PNG.
        for image_format, palette, expected_format in (
            ("JPEG", "RGB", "JPEG"),
            ("PNG", "RGB", "JPEG"),
            ("PNG", "RGBA", "PNG"),
            ("WEBP", "RGB", "JPEG"),
            ("GIF", "RGB", "JPEG"),
        ):
            with self.subTest(image_format=image_format, palette=palette):
                image = FilerImageFactory(
                    file=factory.django.ImageField(
                        width=800, height=1000, format=image_format, palette=palette
                    )
                )
                self.addCleanup(image.file.delete_thumbnails)

                url = thumbnail_url(image, "card-image")

                thumbnail = image.file.get_thumbnail(
                    aliases.get("card-image"), generate=False
                )
                self.assertEqual(url, thumbnail.url)
                with Image.open(thumbnail.path) as thumbnail_image:
                    self.assertEqual(
                        (thumbnail_image.format, thumbnail_image.size),
                        (expected_format, (256, 320)),
                    )
