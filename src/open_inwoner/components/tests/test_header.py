from django.test import TestCase

from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    UserFactory,
    eHerkenningUserFactory,
)
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

        cls.digid_user = DigidUserFactory.create()
        cls.eherkenning_user = eHerkenningUserFactory.create()

        cms_tools.create_homepage()

        # PrimaryNavigation.html requires apphook + categories
        create_apphook_page(ProductsApphook)
        cls.published1 = CategoryFactory(
            path="0001",
            name="First one",
            slug="first-one",
            visible_for_anonymous=True,
            visible_for_citizens=False,
            visible_for_companies=False,
        )
        cls.published2 = CategoryFactory(
            path="0002",
            name="Second one",
            slug="second-one",
            visible_for_anonymous=True,
            visible_for_citizens=True,
            visible_for_companies=False,
        )
        cls.published3 = CategoryFactory(
            path="0003",
            name="Third one",
            slug="third-one",
            visible_for_anonymous=False,
            visible_for_citizens=False,
            visible_for_companies=True,
        )
        cls.published4 = CategoryFactory(
            path="0004",
            name="Fourth one",
            slug="fourth-one",
            visible_for_anonymous=False,
            visible_for_citizens=True,
            visible_for_companies=True,
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

        links = [x for x in doc.find("[title='Onderwerpen'] + ul li a").items()]
        self.assertEqual(len(links), 4)
        self.assertEqual(links[0].attr("href"), self.published1.get_absolute_url())
        self.assertEqual(links[1].attr("href"), self.published2.get_absolute_url())
        self.assertEqual(links[2].attr("href"), self.published1.get_absolute_url())
        self.assertEqual(links[3].attr("href"), self.published2.get_absolute_url())

    def test_categories_visibility_for_digid_users(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        self.client.force_login(self.digid_user)

        response = self.client.get("/", user=self.digid_user)

        doc = PyQuery(response.content)

        categories = doc.find("[title='Onderwerpen']")

        self.assertEqual(len(categories), 2)
        self.assertEqual(categories[0].tag, "a")
        self.assertEqual(categories[1].tag, "button")

        links = [x for x in doc.find("[title='Onderwerpen'] + ul li a").items()]

        self.assertEqual(len(links), 4)
        self.assertEqual(links[0].attr("href"), self.published2.get_absolute_url())
        self.assertEqual(links[1].attr("href"), self.published4.get_absolute_url())
        self.assertEqual(links[2].attr("href"), self.published2.get_absolute_url())
        self.assertEqual(links[3].attr("href"), self.published4.get_absolute_url())

    def test_categories_visibility_for_eherkenning_users(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        self.client.force_login(self.eherkenning_user)

        response = self.client.get("/", user=self.eherkenning_user)

        doc = PyQuery(response.content)

        categories = doc.find("[title='Onderwerpen']")

        self.assertEqual(len(categories), 2)
        self.assertEqual(categories[0].tag, "a")
        self.assertEqual(categories[1].tag, "button")

        links = [x for x in doc.find("[title='Onderwerpen'] + ul li a").items()]
        self.assertEqual(len(links), 4)

        self.assertEqual(links[0].attr("href"), self.published3.get_absolute_url())
        self.assertEqual(links[1].attr("href"), self.published4.get_absolute_url())
        self.assertEqual(links[2].attr("href"), self.published3.get_absolute_url())
        self.assertEqual(links[3].attr("href"), self.published4.get_absolute_url())

    def test_search_bar_hidden_from_anonymous_users(self):
        config = SiteConfiguration.get_solo()
        config.hide_search_from_anonymous_users = True
        config.save()

        response = self.client.get("/")

        doc = PyQuery(response.content)

        search_buttons = doc.find("[title='Zoeken']")

        self.assertEqual(len(search_buttons), 0)

    def test_search_bar_not_hidden_from_anonymous_users(self):
        config = SiteConfiguration.get_solo()
        config.hide_search_from_anonymous_users = False
        config.save()

        response = self.client.get("/")

        doc = PyQuery(response.content)

        search_buttons = doc.find("[title='Zoeken']")

        for button in search_buttons:
            self.assertEqual(button.tag, "button")
