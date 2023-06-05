from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest

from ..models import ProductCondition
from .factories import ProductConditionFactory, ProductFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class ProductConditions(WebTest):
    def setUp(self):
        self.product1 = ProductFactory(name="Product A")
        self.product2 = ProductFactory(name="Product B")
        self.product3 = ProductFactory(name="Product C")
        self.product4 = ProductFactory(name="Product D")
        self.product5 = ProductFactory(name="Product E")
        self.product6 = ProductFactory(name="Product F")
        self.product7 = ProductFactory(name="Product G")
        self.product8 = ProductFactory(name="Product H")
        self.product9 = ProductFactory(name="Product I")
        self.product10 = ProductFactory(name="Product J")
        self.product11 = ProductFactory(name="Product K")
        self.product12 = ProductFactory(name="Product L")

        self.condition1 = ProductConditionFactory(question="Question 1")
        self.condition2 = ProductConditionFactory(question="Question 2")
        self.condition3 = ProductConditionFactory(question="Question 3")
        self.condition4 = ProductConditionFactory(question="Question 4")

        self.product1.conditions.add(self.condition1)
        self.product2.conditions.add(self.condition1, self.condition2)
        self.product3.conditions.add(self.condition1, self.condition2, self.condition3)
        self.product4.conditions.add(
            self.condition1, self.condition2, self.condition3, self.condition4
        )
        self.product5.conditions.add(self.condition2)
        self.product6.conditions.add(self.condition2, self.condition3)
        self.product7.conditions.add(self.condition2, self.condition3, self.condition4)
        self.product8.conditions.add(self.condition3)
        self.product9.conditions.add(self.condition3, self.condition4)
        self.product10.conditions.add(self.condition4)

    def test_no_filter(self):
        response = self.app.get(reverse("products:product_finder"))
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 0)
        self.assertEqual(len(possible_products), 12)
        self.assertNotIn(self.product1, matched_products)
        self.assertIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes(self):
        response = self.app.get(reverse("products:product_finder"))
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 4)
        self.assertEqual(len(possible_products), 8)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no(self):
        response = self.app.get(reverse("products:product_finder"))
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 0)
        self.assertEqual(len(possible_products), 8)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()
        self.assertContains(response, self.condition2.question)

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()
        self.assertContains(response, self.condition3.question)

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 7)
        self.assertEqual(len(possible_products), 5)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 1)
        self.assertEqual(len(possible_products), 5)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 3)
        self.assertEqual(len(possible_products), 5)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 0)
        self.assertEqual(len(possible_products), 5)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_yes_q3_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 9)
        self.assertEqual(len(possible_products), 3)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_yes_q3_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 3)
        self.assertEqual(len(possible_products), 3)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_no_q3_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 3)
        self.assertEqual(len(possible_products), 3)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_no_q3_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 1)
        self.assertEqual(len(possible_products), 3)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_yes_q3_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 5)
        self.assertEqual(len(possible_products), 3)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_yes_q3_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 1)
        self.assertEqual(len(possible_products), 3)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_no_q3_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 2)
        self.assertEqual(len(possible_products), 3)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_no_q3_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 0)
        self.assertEqual(len(possible_products), 3)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_yes_q3_yes_q4_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 10)
        self.assertEqual(len(possible_products), 2)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_yes_q3_yes_q4_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 6)
        self.assertEqual(len(possible_products), 2)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_yes_q3_no_q4_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 4)
        self.assertEqual(len(possible_products), 2)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_yes_q3_no_q4_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 3)
        self.assertEqual(len(possible_products), 2)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_no_q3_yes_q4_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 4)
        self.assertEqual(len(possible_products), 2)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_no_q3_yes_q4_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 2)
        self.assertEqual(len(possible_products), 2)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_no_q3_no_q4_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 2)
        self.assertEqual(len(possible_products), 2)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_yes_q2_no_q3_no_q4_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 1)
        self.assertEqual(len(possible_products), 2)
        self.assertIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_yes_q3_yes_q4_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 6)
        self.assertEqual(len(possible_products), 2)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_yes_q3_yes_q4_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 3)
        self.assertEqual(len(possible_products), 2)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_yes_q3_no_q4_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 2)
        self.assertEqual(len(possible_products), 2)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_yes_q3_no_q4_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 1)
        self.assertEqual(len(possible_products), 2)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_no_q3_yes_q4_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 3)
        self.assertEqual(len(possible_products), 2)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_no_q3_yes_q4_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 1)
        self.assertEqual(len(possible_products), 2)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_no_q3_no_q4_yes(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "yes"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 1)
        self.assertEqual(len(possible_products), 2)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_q1_no_q2_no_q3_no_q4_no(self):
        response = self.app.get(reverse("products:product_finder"))

        # Answering q1
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q2
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q3
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        # Answering q4
        form = response.forms["product-finder"]
        form["answer"].value = "no"
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        matched_products = list(response.context["matched_products"])
        possible_products = list(response.context["possible_products"])
        self.assertEqual(len(matched_products), 0)
        self.assertEqual(len(possible_products), 2)
        self.assertNotIn(self.product1, matched_products)
        self.assertNotIn(self.product1, possible_products)
        self.assertNotIn(self.product2, matched_products)
        self.assertNotIn(self.product2, possible_products)
        self.assertNotIn(self.product3, matched_products)
        self.assertNotIn(self.product3, possible_products)
        self.assertNotIn(self.product4, matched_products)
        self.assertNotIn(self.product4, possible_products)
        self.assertNotIn(self.product5, matched_products)
        self.assertNotIn(self.product5, possible_products)
        self.assertNotIn(self.product6, matched_products)
        self.assertNotIn(self.product6, possible_products)
        self.assertNotIn(self.product7, matched_products)
        self.assertNotIn(self.product7, possible_products)
        self.assertNotIn(self.product8, matched_products)
        self.assertNotIn(self.product8, possible_products)
        self.assertNotIn(self.product9, matched_products)
        self.assertNotIn(self.product9, possible_products)
        self.assertNotIn(self.product10, matched_products)
        self.assertNotIn(self.product10, possible_products)
        self.assertNotIn(self.product11, matched_products)
        self.assertIn(self.product11, possible_products)
        self.assertNotIn(self.product12, matched_products)
        self.assertIn(self.product12, possible_products)

    def test_product_finder_is_reset_when_no_condition(self):
        response = self.app.get(reverse("products:product_finder"))
        form = response.forms["product-finder"]

        ProductCondition.objects.all().delete()

        form["answer"].value = "yes"
        response = form.submit()

        self.assertRedirects(response, reverse("products:product_finder"))

        session = self.app.session
        response.follow()

        self.assertEqual(session["product_finder"], {})
        self.assertIsNone(session["current_condition"])
        self.assertFalse(session["conditions_done"])
