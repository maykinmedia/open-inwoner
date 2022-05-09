from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.questionnaire.models import QuestionnaireStep
from open_inwoner.questionnaire.tests.factories import QuestionnaireStepFactory


class QuestionnaireTestCase(WebTest):
    def setUp(self):
        QuestionnaireStepFactory(code="foo", slug="foo", path="0001")
        QuestionnaireStepFactory(code="foo-bar", slug="foo-bar", path="0002")
        self.root_nodes = QuestionnaireStep.get_root_nodes()

    def test_home_page_contains_root_nodes(self):
        response = self.app.get(reverse("root"))

        self.assertEquals(response.context.get("questionnaire_roots").count(), 2)
        self.assertContains(response, self.root_nodes[0].get_absolute_url())
        self.assertContains(response, self.root_nodes[1].get_absolute_url())

    def test_user_home_page_contains_root_nodes(self):
        user = UserFactory()
        response = self.app.get(reverse("root"), user=user)

        self.assertContains(response, self.root_nodes[0].get_absolute_url())
        self.assertContains(response, self.root_nodes[1].get_absolute_url())
