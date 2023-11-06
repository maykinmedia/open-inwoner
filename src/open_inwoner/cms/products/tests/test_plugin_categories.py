from django.test import TestCase, override_settings

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.products.cms_apps import ProductsApphook
from open_inwoner.pdc.tests.factories import CategoryFactory

from ...tests import cms_tools
from ..cms_plugins import CategoriesPlugin


class TestPluginBasics(TestCase):
    def test_no_output_generated_without_apphook(self):
        html, context = cms_tools.render_plugin(CategoriesPlugin)
        self.assertEqual("", html)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestHighlightedCategories(WebTest):
    def setUp(self):
        cms_tools.create_apphook_page(ProductsApphook)

    def test_only_highlighted_categories_exist_in_context_when_they_exist(self):
        CategoryFactory(name="Should be first")
        highlighted_category1 = CategoryFactory(
            name="This should be second",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_authenticated=True,
        )
        highlighted_category2 = CategoryFactory(
            path="0002",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_authenticated=False,
        )
        highlighted_category3 = CategoryFactory(
            path="0003",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_authenticated=True,
        )
        highlighted_category4 = CategoryFactory(
            path="0004",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_authenticated=False,
        )

        html, context = cms_tools.render_plugin(CategoriesPlugin)
        self.assertEqual(
            list(context["categories"]),
            [highlighted_category1, highlighted_category2],
        )

    def test_highlighted_categories_are_ordered_by_alphabetically(self):
        highlighted_category1 = CategoryFactory(
            name="should be first", highlighted=True
        )
        highlighted_category2 = CategoryFactory(
            name="should be second", highlighted=True
        )
        html, context = cms_tools.render_plugin(CategoriesPlugin)
        self.assertEqual(
            list(context["categories"]),
            [highlighted_category1, highlighted_category2],
        )

    def test_only_highlighted_categories_are_shown_when_they_exist(self):
        user = UserFactory()
        category = CategoryFactory(name="Should be first")
        highlighted_category1 = CategoryFactory(
            name="This should be second",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_authenticated=True,
        )
        highlighted_category2 = CategoryFactory(
            path="0002",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_authenticated=False,
        )
        highlighted_category3 = CategoryFactory(
            path="0003",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_authenticated=True,
        )
        highlighted_category4 = CategoryFactory(
            path="0004",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_authenticated=False,
        )

        html, context = cms_tools.render_plugin(CategoriesPlugin, user=user)

        self.assertEqual(
            list(context["categories"]),
            [highlighted_category1, highlighted_category3],
        )

    def test_category_selected(self):
        user = UserFactory()
        category = CategoryFactory(name="Should be first")
        highlighted_category = CategoryFactory(
            name="This should be second", highlighted=True
        )
        selected_category = CategoryFactory(name="This should the only one")
        user.selected_categories.add(selected_category)

        html, context = cms_tools.render_plugin(CategoriesPlugin, user=user)
        self.assertEqual(
            list(context["categories"]),
            [selected_category],
        )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestPublishedCategories(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.published1 = CategoryFactory(
            path="0001", name="First one", slug="first-one"
        )
        self.published2 = CategoryFactory(
            path="0002", name="Second one", slug="second-one"
        )
        self.draft1 = CategoryFactory(
            path="0003", name="Third one", slug="third-one", published=False
        )
        self.draft2 = CategoryFactory(
            path="0004", name="Wourth one", slug="wourth-one", published=False
        )
        cms_tools.create_apphook_page(ProductsApphook)

    def test_only_published_categories_exist_in_home_page_when_anonymous(self):
        html, context = cms_tools.render_plugin(CategoriesPlugin)
        self.assertEqual(
            list(context["categories"]), [self.published1, self.published2]
        )

    def test_only_published_categories_exist_in_home_page_when_logged_in(self):
        html, context = cms_tools.render_plugin(CategoriesPlugin, user=self.user)
        self.assertEqual(
            list(context["categories"]), [self.published1, self.published2]
        )
