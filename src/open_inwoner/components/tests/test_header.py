from django.test import TestCase

from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.products.cms_apps import ProductsApphook
from open_inwoner.cms.tests import cms_tools
from open_inwoner.cms.tests.cms_tools import create_apphook_page
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.pdc.tests.factories import CategoryFactory


class HeaderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user.set_password("12345")
        cls.user.email = "test@email.com"
        cls.user.save()

        cms_tools.create_homepage()

        # PrimaryNavigation.html requires apphook + categories
        create_apphook_page(ProductsApphook)
        cls.published1 = CategoryFactory(
            path="0001", name="First one", slug="first-one"
        )
        cls.published2 = CategoryFactory(
            path="0002", name="Second one", slug="second-one"
        )

    def test_categories_hidden_from_anonymous_users(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = True
        config.save()

        response = self.client.get("/")

        doc = PyQuery(response.content)

        categories = doc.find("[title='Onderwerpen']")
        self.assertEqual(len(categories), 0)

    def test_categories_not_hidden_from_anonymous_users(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        response = self.client.get("/")

        doc = PyQuery(response.content)

        categories = doc.find("[title='Onderwerpen']")
        self.assertEqual(len(categories), 2)
        self.assertEqual(categories[0].tag, "a")
        self.assertEqual(categories[1].tag, "button")
