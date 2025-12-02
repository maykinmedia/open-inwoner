from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import RequestFactory, TestCase

from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    UserFactory,
    eHerkenningUserFactory,
    eHerkenningVestigingUserFactory,
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
        cls.vestiging_user = eHerkenningVestigingUserFactory.create()

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
        cls.subcategory = CategoryFactory.build(
            name="foo",
            visible_for_anonymous=True,
            visible_for_citizens=True,
            visible_for_companies=True,
        )
        # Subcategories should not show up
        cls.published1.add_child(instance=cls.subcategory)

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

    @patch("open_inwoner.kvk.middleware.KvKLoginMiddleware.requires_redirect")
    def test_categories_visibility_for_eherkenning_users(self, mock_kvk_redirect):
        mock_kvk_redirect.return_value = False

        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        self.client.force_login(self.vestiging_user)

        response = self.client.get("/", user=self.vestiging_user)

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

        search_forms = [
            form
            for form in doc.find("form").items()
            if form.find("button[title='Zoeken']")
        ]

        self.assertEqual(
            len(search_forms), 0, "Search form should be hidden for anonymous users."
        )

    def test_search_bar_not_hidden_from_anonymous_users(self):
        config = SiteConfiguration.get_solo()
        config.hide_search_from_anonymous_users = False
        config.save()

        response = self.client.get("/")
        doc = PyQuery(response.content)

        search_forms = [
            form
            for form in doc.find("form").items()
            if form.find("button[title='Zoeken']")
        ]

        self.assertGreater(
            len(search_forms), 0, "Search form should be visible for anonymous users."
        )

        # Check each search form for the expected input element
        for search_form in search_forms:
            search_input = search_form.find("input[type='text'][name='query']")
            self.assertEqual(
                len(search_input),
                1,
                "Each search form should have a single text input named 'query'.",
            )


class DisplaySearchTemplateTagTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.template = Template(
            "{% load header_tags %}{% display_search_for_user as result %}{{ result }}"
        )

    def _should_display_search(self, context):
        """
        Helper method to evaluate whether search should be displayed.

        Returns:
            bool: True if the `display_search` template tag indicates search should be shown
        """
        result = self.template.render(context)
        return result.strip() == "True"

    # Tests for global `search_enabled` setting

    def test_search_disabled_globally_for_authenticated_user(self):
        config = SiteConfiguration.get_solo()
        config.search_enabled = False
        config.save()

        request = self.factory.get("/")
        request.user = UserFactory()
        context = Context({"request": request})

        self.assertFalse(
            self._should_display_search(context),
            "Search should be hidden when search_enabled is False, even for authenticated users",
        )

    def test_search_disabled_globally_for_anonymous_user(self):
        """
        Search is hidden when search_enabled is False, even if anonymous
        users are normally allowed
        """
        config = SiteConfiguration.get_solo()
        config.search_enabled = False
        config.hide_search_from_anonymous_users = False
        config.save()

        request = self.factory.get("/")
        request.user = AnonymousUser()
        context = Context({"request": request})

        self.assertFalse(
            self._should_display_search(context),
            "Search should be hidden when search_enabled is False, regardless of other settings",
        )

    # Tests for authenticated users

    def test_authenticated_user_always_sees_search_when_enabled(self):
        config = SiteConfiguration.get_solo()
        config.search_enabled = True
        config.save()

        request = self.factory.get("/")
        request.user = UserFactory()
        context = Context({"request": request})

        self.assertTrue(
            self._should_display_search(context),
            "Authenticated users should always see search when search_enabled is True",
        )

    def test_authenticated_user_sees_search_regardless_of_anonymous_setting(self):
        config = SiteConfiguration.get_solo()
        config.search_enabled = True
        config.hide_search_from_anonymous_users = True
        config.save()

        request = self.factory.get("/")
        request.user = UserFactory()
        context = Context({"request": request})

        self.assertTrue(
            self._should_display_search(context),
            "Authenticated users should see search even when hide_search_from_anonymous_users is True",
        )

    # Tests for anonymous users

    def test_anonymous_user_sees_search_when_not_hidden(self):
        config = SiteConfiguration.get_solo()
        config.search_enabled = True
        config.hide_search_from_anonymous_users = False
        config.save()

        request = self.factory.get("/")
        request.user = AnonymousUser()
        context = Context({"request": request})

        self.assertTrue(
            self._should_display_search(context),
            "Anonymous users should see search when hide_search_from_anonymous_users is False",
        )

    def test_anonymous_user_search_hidden(self):
        config = SiteConfiguration.get_solo()
        config.search_enabled = True
        config.hide_search_from_anonymous_users = True
        config.save()

        request = self.factory.get("/")
        request.user = AnonymousUser()
        context = Context({"request": request})

        self.assertFalse(
            self._should_display_search(context),
            "Anonymous users should not see search when hide_search_from_anonymous_users is True",
        )
