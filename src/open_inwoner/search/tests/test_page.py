from django.test import override_settings, tag
from django.urls import reverse_lazy

from django_webtest import WebTest
from playwright.sync_api import expect

from open_inwoner.pdc.tests.factories import (
    CategoryFactory,
    OrganizationFactory,
    ProductFactory,
    TagFactory,
)

from ...cms.products.cms_apps import ProductsApphook
from ...cms.tests import cms_tools
from ...configurations.models import SiteConfiguration
from ...utils.tests.playwright import PlaywrightSyncLiveServerTestCase
from ..constants import FacetChoices
from .utils import ESMixin


@tag("elastic")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class SearchPageTests(ESMixin, WebTest):
    url = reverse_lazy("search:search")

    def setUp(self):
        super().setUp()

        self.product1 = ProductFactory.create(
            name="Name", summary="Some summary", content="Some content"
        )
        self.product2 = ProductFactory.create(
            name="Other", summary="other summary", content="other content"
        )
        self.tag = TagFactory.create()
        self.org = OrganizationFactory.create()
        self.category = CategoryFactory.create()

        self.product1.tags.add(self.tag)
        self.product1.organizations.add(self.org)
        self.product1.categories.add(self.category)

        self.update_index()

    def test_not_show_results_and_filter_without_search(self):
        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)
        # check that form has `query` field
        search_form = response.forms["search-form"]
        self.assertIn("query", search_form.fields)
        for facet in FacetChoices.values:
            # check that facet fields are not shown
            self.assertNotIn(facet, search_form.fields)

        results_div = response.html.find("div", {"class": "search-results__list"})
        self.assertIsNone(results_div)  # check that results are not shown

    def test_show_results_and_filter_with_search(self):
        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)

        form = response.forms["search-header"]
        form["query"] = "content"
        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.request.url, f"http://testserver{self.url}?query=content"
        )
        # check that form has `query` field
        search_form = response.forms["search-form"]
        self.assertIn("query", search_form.fields)
        # check that facet fields are shown
        for facet in FacetChoices.values:
            self.assertIn(facet, search_form.fields)

        results_div = response.html.find("div", {"class": "search-results"})
        self.assertIsNotNone(results_div)  # check that results are shown

        results = response.context["paginator"].object_list
        self.assertEqual(len(results), 2)

    def test_search_with_filter(self):
        response = self.app.get(self.url, {"query": "content"})

        self.assertEqual(response.status_code, 200)

        form = response.forms["search-form"]

        self.assertEqual(form["query"].value, "content")

        form["tags"] = [self.tag.slug]
        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.request.url,
            f"http://testserver{self.url}?query=content&tags={self.tag.slug}",
        )
        # check that form has `query` field
        search_form = response.forms["search-form"]
        self.assertIn("query", search_form.fields)
        # check that facet fields are shown
        for facet in FacetChoices.values:
            self.assertIn(facet, search_form.fields)

        results_div = response.html.find("div", {"class": "search-results"})
        self.assertIsNotNone(results_div)  # check that results are shown

        results = response.context["paginator"].object_list
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].slug, self.product1.slug)

    def test_pagination_links(self):
        products = ProductFactory.create_batch(20, content="content")
        self.tag.products.add(*products)
        self.update_index()

        response = self.app.get(self.url, {"query": "content", "tags": self.tag.slug})

        self.assertEqual(response.status_code, 200)

        results = response.context["paginator"].object_list
        self.assertEqual(len(results), 21)

        pagination_div = response.html.find("div", {"class": "pagination"})
        pagination_links = pagination_div.find_all("a")

        # check that all query params are appended
        for link in pagination_links:
            self.assertEqual(
                link["href"], f"?query=content&tags={self.tag.slug}&page=2"
            )


@tag("e2e")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class SearchPagePlaywrightTests(ESMixin, PlaywrightSyncLiveServerTestCase):
    def setUp(self):
        super().setUp()

        self.product1 = ProductFactory.create(
            name="Name", summary="Some summary", content="Some content"
        )
        self.product2 = ProductFactory.create(
            name="Other", summary="Other summary", content="Other content"
        )
        self.tag = TagFactory.create()
        self.org = OrganizationFactory.create()
        self.category = CategoryFactory.create()

        self.product1.tags.add(self.tag)
        self.product1.organizations.add(self.org)
        self.product1.categories.add(self.category)

        self.update_index()

        cms_tools.create_homepage()
        cms_tools.create_apphook_page(ProductsApphook)

    def test_search_form_delegates(self):
        # somehow this doesn't work with mock/patch
        config = SiteConfiguration.get_solo()
        config.cookie_info_text = ""
        config.hide_search_from_anonymous_users = False
        config.hide_categories_from_anonymous_users = False
        config.save()

        form_ids = [
            ("search-form-desktop", 1280, False),
            # ("search-form-mobile-closed", 480, False),
            # ("search-form-mobile-open", 480, True),
        ]
        for form_id, view_size, open_menu in form_ids:
            with self.subTest(form_id):
                context = self.browser.new_context(
                    viewport={"width": view_size, "height": 1024},
                )
                page = context.new_page()
                page.goto(self.live_reverse("products:category_list"))

                form = page.locator(f"#{form_id}")
                if open_menu:
                    page.locator(".header__menu .header__button").click()
                expect(form).to_be_visible()
                field = form.get_by_role("textbox")
                field.fill("Summary")
                field.press("Enter")

                page.wait_for_url(self.live_reverse("search:search", star=True))
                expect(page.locator(".search-results__item")).to_have_count(2)

                form = page.locator(f"#{form_id}")
                if open_menu:
                    page.locator(".header__menu .header__button").click()
                expect(form).to_be_visible()
                field = form.get_by_role("textbox")
                field.fill("Other")
                field.press("Enter")

                page.wait_for_url(self.live_reverse("search:search", star=True))
                expect(page.locator(".search-results__item")).to_have_count(1)

                page.close()
                context.close()
