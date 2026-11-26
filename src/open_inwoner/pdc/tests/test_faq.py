from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.pdc.models import Question

from .factories import CategoryFactory, ProductFactory, QuestionFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestGeneralFAQ(WebTest):
    def test_model_constraints_disallows_both_product_and_category(self):
        product = ProductFactory.create()
        category = CategoryFactory.create()
        question = Question(product=product, category=category)

        with self.assertRaises(IntegrityError):
            question.save()

    def test_model_clean_disallows_both_product_and_category(self):
        product = ProductFactory.create()
        category = CategoryFactory.create()
        question = Question(product=product, category=category)

        with self.assertRaises(ValidationError) as context:
            question.clean()

        self.assertEqual(
            set(context.exception.error_dict.keys()), {"product", "category"}
        )

    def test_general_faq_view_only_lists_general_questions(self):
        question = QuestionFactory.create(question="General question")

        product = ProductFactory.create()
        QuestionFactory.create(question="Product question", product=product)

        category = CategoryFactory.create()
        QuestionFactory.create(question="Category question", category=category)

        response = self.app.get(reverse("general_faq"))

        self.assertContains(response, question.question)

        # Only our general question
        self.assertEqual(list(response.context["faqs"]), [question])
