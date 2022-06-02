from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory

from .factories import CategoryFactory


class TestCategoryContext(WebTest):
    def test_only_highlighted_categories_exist_in_context_when_they_exist(self):
        CategoryFactory(name="Should be first")
        highlighted_category = CategoryFactory(
            name="This should be second", highlighted=True
        )
        response = self.app.get(reverse("root"))
        self.assertEqual(
            list(response.context["categories"]),
            [highlighted_category],
        )

    def test_highlighted_categories_are_ordered_by_alphabetically(self):
        highlighted_category1 = CategoryFactory(
            name="should be first", highlighted=True
        )
        highlighted_category2 = CategoryFactory(
            name="should be second", highlighted=True
        )
        response = self.app.get(reverse("root"))

        self.assertEqual(
            list(response.context["categories"]),
            [highlighted_category1, highlighted_category2],
        )

    def test_all_categories_exist_in_context_when_logged_in(self):
        user = UserFactory()
        category = CategoryFactory(name="Should be first")
        highlighted_category = CategoryFactory(
            name="This should be second", highlighted=True
        )
        response = self.app.get(reverse("root"), user=user)
        self.assertEqual(
            list(response.context["categories"]),
            [category, highlighted_category],
        )
