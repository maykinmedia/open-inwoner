from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_webtest import WebTest
from privates.test import temp_private_root

from open_inwoner.accounts.models import Document
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.pdc.tests.factories import ProductFactory

from ..views import QUESTIONNAIRE_SESSION_KEY
from .factories import QuestionnaireStepFactory


@temp_private_root()
class QuestionnaireExportTests(WebTest):
    def setUp(self) -> None:
        self.client = Client()
        self.user = UserFactory()
        self.export_url = reverse("questionnaire:questionnaire_export")
        self.questionnaire = QuestionnaireStepFactory(path="0001")
        self.descendant = self.questionnaire.add_child(slug="some-text")

    def test_anonymous_user_exports_file_without_being_saved(self):
        response = self.app.get(
            reverse(
                "questionnaire:root_step", kwargs={"slug": self.questionnaire.slug}
            ),
        )
        form = response.forms["questionnaire_step"]
        form["answer"] = self.descendant.id
        response = form.submit()
        filename = _("questionnaire_{slug}.pdf").format(slug=self.questionnaire.slug)
        response = self.client.get(reverse("questionnaire:questionnaire_export"))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.headers["Content-Type"], "application/pdf")
        self.assertEquals(
            response.headers["Content-Disposition"],
            f'attachment; filename="{filename}"',
        )
        self.assertFalse(Document.objects.exists())

    def test_logged_in_user_exports_file_and_it_is_automatically_saved(self):
        response = self.app.get(
            reverse(
                "questionnaire:root_step", kwargs={"slug": self.questionnaire.slug}
            ),
            user=self.user,
        )
        form = response.forms["questionnaire_step"]
        form["answer"] = self.descendant.id
        response = form.submit()
        filename = _("questionnaire_{slug}.pdf").format(slug=self.descendant.slug)
        response = self.app.get(
            reverse("questionnaire:questionnaire_export"), user=self.user
        )
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.headers["Content-Type"], "application/pdf")
        self.assertEquals(
            response.headers["Content-Disposition"],
            f'attachment; filename="{filename}"',
        )
        self.assertTrue(Document.objects.filter(name=filename).exists())

    def test_response_contains_right_data(self):
        product = ProductFactory()
        self.questionnaire.related_products.add(product)
        response = self.app.get(
            reverse(
                "questionnaire:root_step", kwargs={"slug": self.questionnaire.slug}
            ),
            user=self.user,
        )
        form = response.forms["questionnaire_step"]
        form["answer"] = self.descendant.id
        response = form.submit()
        response = self.client.get(reverse("questionnaire:questionnaire_export"))
        self.assertEquals(response.context["root_title"], self.questionnaire.title)
        self.assertListEqual(
            response.context["steps"],
            [
                {
                    "question": self.questionnaire.question,
                    "answer": self.questionnaire.parent_answer,
                    "content": self.questionnaire.content,
                },
            ],
        )
        self.assertEquals(
            response.context["last_step"],
            {
                "question": self.questionnaire.question,
                "content": self.questionnaire.content,
            },
        )
        self.assertTrue(
            response.context["related_products"].filter(slug=product.slug).exists()
        )
