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
from ...utils.test import ClearCachesMixin
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

        form = response.forms["search-form"]
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
            # NOTE: WebTest doesn't understand the form-attribute on input elements so let's use PyQuery instead
            # self.assertIn(facet, search_form.fields)
            controls = response.pyquery(f"input[form='search-form'][name='{facet}']")
            self.assertGreater(len(controls), 0, f"missing control for facet '{facet}'")

        results_div = response.html.find("div", {"class": "search-results"})
        self.assertIsNotNone(results_div)

        results = response.context["paginator"].object_list
        self.assertEqual(len(results), 2)

    def test_search_with_filter(self):
        response = self.app.get(self.url, {"query": "content", "tags": self.tag.slug})

        search_form = response.forms["search-form"]
        self.assertIn("query", search_form.fields)

        # check that facet fields are shown
        for facet in FacetChoices.values:
            # NOTE: WebTest doesn't understand the form-attribute on input elements so let's use PyQuery instead
            # self.assertIn(facet, search_form.fields)
            controls = response.pyquery(f"input[form='search-form'][name='{facet}']")
            self.assertGreater(len(controls), 0, f"missing control for facet '{facet}'")

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
@tag("elastic")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class SearchPagePlaywrightTests(
    ClearCachesMixin, ESMixin, PlaywrightSyncLiveServerTestCase
):
    # the search forms in the header/menu that are connected to the hidden search-form
    form_delegates = [
        ("search-form-desktop", 1280, False),
        ("search-form-mobile-closed", 480, False),
        ("search-form-mobile-open", 480, True),
    ]

    def iter_delegate_ids(self):
        return (name for name, size, open_menu in self.form_delegates)

    def setUp(self):
        super().setUp()

        self.product1 = ProductFactory.create(
            name="Some name", summary="Some summary", content="Some content"
        )
        self.product2 = ProductFactory.create(
            name="Other name", summary="Other summary", content="Other content"
        )
        self.tag1 = TagFactory.create(name="Tag 1")
        self.tag2 = TagFactory.create(name="Tag 2")
        self.org1 = OrganizationFactory.create(name="Organization 1")
        self.org2 = OrganizationFactory.create(name="Organization 2")
        self.category1 = CategoryFactory.create(name="Category 1")
        self.category2 = CategoryFactory.create(name="Category 2")

        self.product1.tags.add(self.tag1)
        self.product1.organizations.add(self.org1)
        self.product1.categories.add(self.category1)

        self.product2.tags.add(self.tag2)
        self.product2.organizations.add(self.org2)
        self.product2.categories.add(self.category2)

        self.update_index()

        cms_tools.create_apphook_page(ProductsApphook)

        # somehow this doesn't work with mock/patch
        config = SiteConfiguration.get_solo()
        config.cookie_info_text = ""
        config.save()

    def test_basic_search(self):
        context = self.browser.new_context()
        page = context.new_page()

        # search to find both products
        page.goto(self.live_reverse("search:search", params={"query": "summary"}))
        page.wait_for_url(self.live_reverse("search:search", star=True))
        expect(page.locator(".search-results__item")).to_have_count(2)

    def test_search_form_delegates_copy_query_value(self):
        context = self.browser.new_context()
        page = context.new_page()
        page.goto(self.live_reverse("search:search", params={"query": "summary"}))

        # check if hidden form has our query
        form = page.locator("#search-form")
        expect(form).not_to_be_visible()
        elem = form.locator("input[name='query']")
        expect(elem).to_have_value("summary")

        # check if every delegate has our query
        for form_id in self.iter_delegate_ids():
            form = page.locator(f"#{form_id}")
            elem = form.locator("input[name='query']")
            expect(elem).to_have_value("summary")

    def test_search_form_delegates_do_search(self):
        def _do_search(query, form_id, open_menu):
            form = page.locator(f"#{form_id}")
            if open_menu:
                page.locator(".header__menu .header__button").click()
            expect(form).to_be_visible()
            field = form.get_by_role("textbox")
            field.fill(query)
            field.press("Enter")
            page.wait_for_url(self.live_reverse("search:search", star=True))

        for form_id, view_size, open_menu in self.form_delegates:
            with self.subTest(form_id):
                context = self.browser.new_context(
                    viewport={"width": view_size, "height": 1024},
                )
                page = context.new_page()
                page.goto(self.live_reverse("products:category_list"))

                # search from this page
                _do_search("summary", form_id, open_menu)
                expect(page.locator(".search-results__item")).to_have_count(2)

                # perform another search from the search results page
                _do_search("other", form_id, open_menu)
                expect(page.locator(".search-results__item")).to_have_count(1)

                page.close()
                context.close()

    def test_search_with_filters(self):
        context = self.browser.new_context()
        page = context.new_page()

        # search to find both products
        page.goto(self.live_reverse("search:search", params={"query": "summary"}))
        page.wait_for_url(self.live_reverse("search:search", star=True))
        expect(page.locator(".search-results__item")).to_have_count(2)

        # check if we see all checkboxes
        for facet in FacetChoices.values:
            # tags, organizations, categories
            controls = page.locator(f"input[form='search-form'][name='{facet}']")
            expect(controls).to_have_count(2)
            for checkbox in controls.all():
                # the input elements are hidden for styling so just test for enabled
                expect(checkbox).to_be_enabled()
                expect(checkbox).not_to_be_checked()

        def _click_checkbox_for_name(name):
            # our checkbox widget hides the <input> element and styles the <label> and a pseudo-element
            # this a problem for playwright accessibility, so we find the label for the checkbox and click on the label like a user would
            page.locator(".checkbox").filter(
                has=page.get_by_role("checkbox", name=name)
            ).locator("label").click()

        def _test_search(checkbox_name, expected_text):
            page.goto(self.live_reverse("search:search", params={"query": "summary"}))
            _click_checkbox_for_name(checkbox_name)
            page.wait_for_timeout(250)  # wait for debounce JS
            page.wait_for_url(self.live_reverse("search:search", star=True))
            # is our box checked in response
            expect(page.get_by_role("checkbox", name=checkbox_name)).to_be_checked()
            # implies one exact result
            expect(page.locator(".search-results__item h3")).to_have_text(expected_text)

        _test_search("Tag 1", self.product1.name)
        _test_search("Tag 2", self.product2.name)
        _test_search("Organization 1", self.product1.name)
        _test_search("Organization 2", self.product2.name)
        _test_search("Category 1", self.product1.name)
        _test_search("Category 2", self.product2.name)

    def test_search_with_filter_combinations(self):
        # NOTE it isn't great to generate query-strings outside the form but we test the form above
        context = self.browser.new_context()
        page = context.new_page()

        tests = [
            (
                {"query": "summary", "tags": self.tag1.slug},
                self.product1.name,
            ),
            (
                {"query": "summary", "tags": self.tag2.slug},
                [self.product2.name],
            ),
            (
                {"query": "summary", "organizations": self.org2.slug},
                self.product2.name,
            ),
            (
                {"query": "summary", "categories": self.category1.slug},
                self.product1.name,
            ),
            (
                {
                    "query": "summary",
                    "tags": self.tag1.slug,
                    "organizations": self.org1.slug,
                    "categories": self.category1.slug,
                },
                self.product1.name,
            ),
        ]
        for query_params, result_text in tests:
            with self.subTest(str(query_params)):
                page.goto(self.live_reverse("search:search", params=query_params))
                # implies one exact result
                expect(page.locator(".search-results__item h3")).to_have_text(
                    result_text
                )
