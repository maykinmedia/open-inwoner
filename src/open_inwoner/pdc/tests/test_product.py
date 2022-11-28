from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.questionnaire.tests.factories import QuestionnaireStepFactory

from .factories import CategoryFactory, ProductFactory, QuestionFactory


class TestPublishedProducts(WebTest):
    def test_only_published_products_exist_on_themes_page_when_anonymous(self):
        category = CategoryFactory(path="0001", name="First one", slug="first-one")
        product1 = ProductFactory(categories=(category,))
        product2 = ProductFactory(categories=(category,), published=False)
        response = self.app.get(
            reverse("pdc:category_detail", kwargs={"slug": category.slug})
        )
        self.assertEqual(list(response.context["products"]), [product1])

    def test_only_published_products_exist_on_themes_page_when_logged_in(self):
        user = UserFactory()
        category = CategoryFactory(path="0001", name="First one", slug="first-one")
        product1 = ProductFactory(categories=(category,))
        product2 = ProductFactory(categories=(category,), published=False)
        response = self.app.get(
            reverse("pdc:category_detail", kwargs={"slug": category.slug}), user=user
        )
        self.assertEqual(list(response.context["products"]), [product1])

    def test_only_published_related_products_exist_on_product_page_when_anonymous(self):
        product1 = ProductFactory()
        product2 = ProductFactory(published=False)
        product3 = ProductFactory(related_products=(product1, product2))
        response = self.app.get(
            reverse("pdc:product_detail", kwargs={"slug": product1.slug})
        )
        self.assertContains(response, product1.name)
        self.assertNotContains(response, product2.name)

    def test_only_published_related_products_exist_on_product_page_when_logged_in(self):
        user = UserFactory()
        product1 = ProductFactory()
        product2 = ProductFactory(published=False)
        product3 = ProductFactory(related_products=(product1, product2))
        response = self.app.get(
            reverse("pdc:product_detail", kwargs={"slug": product1.slug}), user=user
        )
        self.assertContains(response, product1.name)
        self.assertNotContains(response, product2.name)

    def test_only_published_products_exist_on_zelfdiagnose_when_anoynymous(self):
        product1 = ProductFactory()
        product2 = ProductFactory(published=False)
        questionnaire = QuestionnaireStepFactory(related_products=(product1, product2))
        response = self.app.get(
            reverse("questionnaire:root_step", kwargs={"slug": questionnaire.slug})
        )
        self.assertContains(response, product1.name)
        self.assertNotContains(response, product2.name)

    def test_only_published_products_exist_on_zelfdiagnose_when_logged_in(self):
        user = UserFactory()
        product1 = ProductFactory()
        product2 = ProductFactory(published=False)
        questionnaire = QuestionnaireStepFactory(related_products=(product1, product2))
        response = self.app.get(
            reverse("questionnaire:root_step", kwargs={"slug": questionnaire.slug}),
            user=user,
        )
        self.assertContains(response, product1.name)
        self.assertNotContains(response, product2.name)

    def test_only_published_products_exist_on_product_finder_page_when_anonymous(self):
        product1 = ProductFactory()
        product2 = ProductFactory(published=False)
        response = self.app.get(reverse("pdc:product_finder"))
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 0)
        self.assertEqual(len(possible_products), 1)
        self.assertIn(product1, possible_products)
        self.assertNotIn(product2, possible_products)

    def test_only_published_products_exist_on_product_finder_page_when_logged_in(self):
        user = UserFactory()
        product1 = ProductFactory()
        product2 = ProductFactory(published=False)
        response = self.app.get(reverse("pdc:product_finder"), user=user)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 0)
        self.assertEqual(len(possible_products), 1)
        self.assertIn(product1, possible_products)
        self.assertNotIn(product2, possible_products)


class TestProductFAQ(WebTest):
    def test_product_detail_shows_product_faq(self):
        product = ProductFactory()
        question_1 = QuestionFactory(
            question="Does this sort to the bottom?", order=10, product=product
        )
        question_2 = QuestionFactory(
            question="Sorting to the top", order=1, product=product
        )

        other_product = ProductFactory()
        other_question = QuestionFactory(product=other_product)

        response = self.app.get(
            reverse("pdc:product_detail", kwargs={"slug": product.slug})
        )
        self.assertEqual(response.context["product"], product)

        # check we got our questions
        self.assertContains(response, question_1.question)
        self.assertContains(response, question_2.question)
        self.assertNotContains(response, other_question.question)

        # check ordering: Q1 comes after Q2
        q1_pos = response.text.index(question_1.question)
        q2_pos = response.text.index(question_2.question)
        self.assertGreater(q1_pos, q2_pos)
