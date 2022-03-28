from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from privates.test import temp_private_root

from open_inwoner.accounts.models import Document
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.pdc.tests.factories import ProductFactory

from ..views import QUESTIONNAIRE_SESSION_KEY
from .factories import QuestionnaireStepFactory


@temp_private_root()
class QuestionnaireExportTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = UserFactory()
        self.export_url = reverse("questionnaire:questionnaire_export")
        self.questionnaire = QuestionnaireStepFactory(path="0001")
        self.session = self.client.session
        self.session[QUESTIONNAIRE_SESSION_KEY] = self.questionnaire.slug
        self.session.save()
        self.session_cookie_name = settings.SESSION_COOKIE_NAME
        self.client.cookies[self.session_cookie_name] = self.session.session_key

    def test_anonymous_user_exports_file_without_being_saved(self):
        response = self.client.get(reverse("questionnaire:questionnaire_export"))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.headers["Content-Type"], "application/pdf")
        self.assertEquals(
            response.headers["Content-Disposition"],
            f'attachment; filename="questionnaire_{self.questionnaire.slug}.pdf"',
        )
        self.assertFalse(Document.objects.exists())

    def test_logged_in_user_exports_file_and_it_is_automatically_saved(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("questionnaire:questionnaire_export"))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.headers["Content-Type"], "application/pdf")
        self.assertEquals(
            response.headers["Content-Disposition"],
            f'attachment; filename="questionnaire_{self.questionnaire.slug}.pdf"',
        )
        self.assertTrue(
            Document.objects.filter(
                name=f"questionnaire_{self.questionnaire.slug}.pdf"
            ).exists()
        )

    def test_response_contains_right_data(self):
        product = ProductFactory()
        child = self.questionnaire.add_child(path="00030001", slug="foo")
        grandchild = child.add_child(path="000300010001", slug="bar")
        grandchild.related_products.add(product)
        self.session[QUESTIONNAIRE_SESSION_KEY] = grandchild.slug
        self.session.save()
        self.session_cookie_name = settings.SESSION_COOKIE_NAME
        self.client.cookies[self.session_cookie_name] = self.session.session_key
        response = self.client.get(reverse("questionnaire:questionnaire_export"))
        self.assertEquals(response.context["root_title"], self.questionnaire.title)
        self.assertListEqual(
            response.context["steps"],
            [
                {
                    "question": self.questionnaire.question,
                    "answer": child.parent_answer,
                    "content": child.content,
                },
                {
                    "question": child.question,
                    "answer": grandchild.parent_answer,
                    "content": grandchild.content,
                },
            ],
        )
        self.assertEquals(
            response.context["last_step"],
            {"question": child.question, "content": child.content},
        )
        self.assertTrue(
            response.context["related_products"].filter(slug=product.slug).exists()
        )
