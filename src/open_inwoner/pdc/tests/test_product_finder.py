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

    # TODO: Add tests that show that the products are filtered as expected
