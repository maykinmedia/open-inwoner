from django.core import mail
from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory

from .factories import ProductConditionFactory, ProductFactory


class ProductFinderViewTests(WebTest):
    csrf_checks = False

    def setUp(self) -> None:
        self.user = UserFactory()

        self.url = reverse("pdc:product_finder")

    def test_login_not_required(self):
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_with_condition(self):
        condition = ProductConditionFactory()
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, condition.question)

    def test_with_conditions(self):
        condition = ProductConditionFactory()
        condition2 = ProductConditionFactory()
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.forms["product-finder"]
        form["answer"] = "yes"

        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, condition2.question)

    def test_with_conditions_no_next(self):
        condition = ProductConditionFactory()
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.forms["product-finder"]
        form["answer"] = "yes"

        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)

    def test_empty(self):
        condition = ProductConditionFactory()
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.forms["product-finder"]
        response = form.submit()
        self.assertEqual(response.status_code, 200)

    def test_reset(self):
        condition = ProductConditionFactory()
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.forms["product-finder"]
        form["answer"] = "yes"

        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        form = response.forms["product-finder"]
        response = form.submit("reset").follow()
        self.assertEqual(response.status_code, 200)

    def test_previous(self):
        condition = ProductConditionFactory()
        condition2 = ProductConditionFactory()
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.forms["product-finder"]
        form["answer"] = "yes"

        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, condition2.question)
        form = response.forms["product-finder"]
        response = form.submit("previous").follow()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, condition.question)

    def test_product_filtered(self):
        condition = ProductConditionFactory()
        condition2 = ProductConditionFactory()
        product1 = ProductFactory(name="Product A")
        product2 = ProductFactory(name="Product B")

        product1.conditions.add(condition)
        product2.conditions.add(condition2)

        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product1)
        self.assertContains(response, product2)
        form = response.forms["product-finder"]
        form["answer"] = "yes"

        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, condition2.question)
        self.assertContains(response, product1)
        self.assertNotContains(response, product2)
        self.assertIn(product1, response.context["matched_products"])

    def test_product_excluded(self):
        condition = ProductConditionFactory()
        condition2 = ProductConditionFactory()
        product1 = ProductFactory(name="Product A")
        product2 = ProductFactory(name="Product B")

        product1.conditions.add(condition)
        product2.conditions.add(condition2)

        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product1)
        self.assertContains(response, product2)
        form = response.forms["product-finder"]
        form["answer"] = "no"

        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, condition2.question)
        self.assertNotContains(response, product1)
        self.assertContains(response, product2)
        self.assertIn(product2, response.context["matched_products"])

    def test_product_filtered_multiple(self):
        condition = ProductConditionFactory()
        condition2 = ProductConditionFactory()
        product1 = ProductFactory(name="Product A")
        product2 = ProductFactory(name="Product B")

        product1.conditions.add(condition)
        product2.conditions.add(condition, condition2)

        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product1)
        self.assertContains(response, product2)
        form = response.forms["product-finder"]
        form["answer"] = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product1)
        self.assertContains(response, product2)
        form = response.forms["product-finder"]
        form["answer"] = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, product1
        )  # Can be found in the possible products.
        self.assertContains(response, product2)

        self.assertIn(product2, response.context["matched_products"])
        self.assertIn(product1, response.context["possible_products"])
