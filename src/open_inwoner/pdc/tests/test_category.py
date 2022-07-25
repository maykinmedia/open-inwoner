from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.questionnaire.tests.factories import QuestionnaireStepFactory

from .factories import CategoryFactory


class TestHighlightedCategories(WebTest):
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

    def test_only_highlighted_categories_are_shown_when_they_exist(self):
        user = UserFactory()
        category = CategoryFactory(name="Should be first")
        highlighted_category = CategoryFactory(
            name="This should be second", highlighted=True
        )
        response = self.app.get(reverse("root"), user=user)
        self.assertEqual(
            list(response.context["categories"]),
            [highlighted_category],
        )

    def test_category_selected(self):
        user = UserFactory()
        category = CategoryFactory(name="Should be first")
        highlighted_category = CategoryFactory(
            name="This should be second", highlighted=True
        )
        selected_category = CategoryFactory(name="This should the only one")
        user.selected_themes.add(selected_category)
        response = self.app.get(reverse("root"), user=user)
        self.assertEqual(
            list(response.context["categories"]),
            [selected_category],
        )


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

    def test_only_published_categories_exist_in_home_page_when_anonymous(self):
        response = self.app.get(reverse("root"))
        self.assertEqual(
            list(response.context["categories"]), [self.published1, self.published2]
        )

    def test_only_published_categories_exist_in_home_page_when_logged_in(self):
        response = self.app.get(reverse("root"), user=self.user)
        self.assertEqual(
            list(response.context["categories"]), [self.published1, self.published2]
        )

    def test_only_published_categories_exist_in_breadcrumbs_when_anonymous(self):
        response = self.app.get(reverse("root"))
        self.assertEqual(
            list(response.context["menu_categories"]),
            [self.published1, self.published2],
        )

    def test_only_published_categories_exist_in_breadcrumbs_when_logged_in(self):
        response = self.app.get(reverse("root"), user=self.user)
        self.assertEqual(
            list(response.context["menu_categories"]),
            [self.published1, self.published2],
        )

    def test_only_published_categories_exist_in_list_page_when_anonymous(self):
        response = self.app.get(reverse("pdc:category_list"))
        self.assertEqual(
            list(response.context["categories"]), [self.published1, self.published2]
        )

    def test_only_published_categories_exist_in_list_page_when_logged_in(self):
        response = self.app.get(reverse("pdc:category_list"), user=self.user)
        self.assertEqual(
            list(response.context["categories"]), [self.published1, self.published2]
        )

    def test_only_published_subcategories_exist_in_detail_page_when_anonymous(self):
        descendent1 = self.published1.add_child(
            path="00010001", name="first-child", slug="first-child", published=True
        )
        descendent2 = self.published1.add_child(
            path="00010002", name="second-child", slug="second-child", published=False
        )
        response = self.app.get(
            reverse("pdc:category_detail", kwargs={"slug": self.published1.slug})
        )
        self.assertEqual(list(response.context["subcategories"]), [descendent1])

    def test_only_published_subcategories_exist_in_detail_page_when_logged_in(self):
        descendent1 = self.published1.add_child(
            path="00010003", name="first-child-2", slug="first-child-2", published=True
        )
        descendent2 = self.published1.add_child(
            path="00010004",
            name="second-child-2",
            slug="second-child-2",
            published=False,
        )
        response = self.app.get(
            reverse("pdc:category_detail", kwargs={"slug": self.published1.slug}),
            user=self.user,
        )
        self.assertEqual(list(response.context["subcategories"]), [descendent1])

    def test_only_published_categories_exist_in_my_themes_page(self):
        response = self.app.get(reverse("accounts:my_themes"), user=self.user)
        self.assertEqual(
            list(response.context["categories"]),
            [self.published1, self.published2],
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
