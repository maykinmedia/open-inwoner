from django.urls import reverse

from django_webtest import WebTest

from .factories import CategoryFactory, ProductFactory, QuestionFactory


class TestGeneralFAQ(WebTest):
    def test_general_faq_only_lists_general_questions(self):
        question = QuestionFactory(question="General question")

        product = ProductFactory()
        QuestionFactory(question="Product question", product=product)

        category = CategoryFactory()
        QuestionFactory(question="Category question", category=category)

        response = self.app.get(reverse("general_faq"))

        self.assertContains(response, question.question)

        # Only our general question
        self.assertEqual(list(response.context["faqs"]), [question])
