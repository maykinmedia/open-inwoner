from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.questionnaire.tests.factories import QuestionnaireStepFactory

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


class TestHighlightedQuestionnaire(WebTest):
    def setUp(self):
        self.category = CategoryFactory()
        self.questionnaire = QuestionnaireStepFactory(
            path="0001", category=self.category
        )
        self.highlighted_questionnaire_1 = QuestionnaireStepFactory(
            path="0003", category=self.category, highlighted=True
        )
        self.highlighted_questionnaire_2 = QuestionnaireStepFactory(
            path="0004", category=self.category, highlighted=True
        )
        self.highlighted_questionnaire_3 = QuestionnaireStepFactory(
            path="0005", category=self.category, highlighted=True
        )

    def test_only_highlighted_questionnaires_are_shown_on_anonymous_home_page(self):
        response = self.app.get(reverse("root"))
        self.assertEqual(
            list(response.context["questionnaire_roots"]),
            [
                self.highlighted_questionnaire_1,
                self.highlighted_questionnaire_2,
                self.highlighted_questionnaire_3,
            ],
        )

    def test_only_highlighted_questionnaires_are_shown_on_user_home_page(self):
        user = UserFactory()
        response = self.app.get(reverse("root"), user=user)
        self.assertEqual(
            list(response.context["questionnaire_roots"]),
            [
                self.highlighted_questionnaire_1,
                self.highlighted_questionnaire_2,
                self.highlighted_questionnaire_3,
            ],
        )

    def test_all_questionnaires_are_shown_on_anonymous_category_detailed_page(self):
        response = self.app.get(
            reverse("pdc:category_detail", kwargs={"slug": self.category.slug})
        )
        self.assertEqual(
            list(response.context["questionnaire_roots"]),
            [
                self.questionnaire,
                self.highlighted_questionnaire_1,
                self.highlighted_questionnaire_2,
                self.highlighted_questionnaire_3,
            ],
        )

    def test_all_questionnaires_are_shown_on_user_category_detailed_page(self):
        user = UserFactory()
        response = self.app.get(
            reverse("pdc:category_detail", kwargs={"slug": self.category.slug}),
            user=user,
        )
        self.assertEqual(
            list(response.context["questionnaire_roots"]),
            [
                self.questionnaire,
                self.highlighted_questionnaire_1,
                self.highlighted_questionnaire_2,
                self.highlighted_questionnaire_3,
            ],
        )
