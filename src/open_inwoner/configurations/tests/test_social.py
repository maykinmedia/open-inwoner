from django.test import Client, TestCase, override_settings
from django.urls import reverse

from pyquery import PyQuery

from ...pdc.tests.factories import ProductFactory
from ..models import SiteConfiguration


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class SocialMediaButtonsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()
        cls.client = Client()

    def test_social_media_buttons_enabled(self):
        config = SiteConfiguration.get_solo()
        config.display_social = True
        config.save()

        url = reverse("products:product_detail", kwargs={"slug": self.product.slug})
        response = self.client.get(url)
        page_url = f"http://testserver{response.request['PATH_INFO']}"

        doc = PyQuery(response.content)
        social = doc.find(".sharing-list")

        facebook = social.find(".facebook-share-button")
        self.assertTrue(facebook.is_("a"))
        self.assertEqual(
            facebook.attr["href"],
            f"https://www.facebook.com/share.php?u={page_url}",
        )

        twitter = social.find(".x-twitter-share-button")
        self.assertTrue(twitter.is_("a"))
        self.assertEqual(
            twitter.attr["href"],
            f"https://twitter.com/intent/tweet?url={page_url}",
        )

        whatsapp = social.find(".whatsapp-share-button")
        self.assertTrue(whatsapp.is_("a"))
        self.assertEqual(
            whatsapp.attr["href"],
            f"https://api.whatsapp.com/send?text={page_url}",
        )

        linkedin = social.find(".linkedin-share-button")
        self.assertTrue(linkedin.is_("a"))
        self.assertEqual(
            linkedin.attr["href"],
            f"https://www.linkedin.com/shareArticle?mini=true&url={page_url}",
        )

    def test_social_media_buttons_disabled(self):
        config = SiteConfiguration.get_solo()
        config.display_social = False
        config.save()

        url = reverse("products:product_detail", kwargs={"slug": self.product.slug})
        response = self.client.get(url)

        doc = PyQuery(response.content)

        social = doc.find(".sharing-list")
        self.assertEqual(social, [])
