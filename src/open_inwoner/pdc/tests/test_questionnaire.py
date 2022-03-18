from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.questionnaire.models import QuestionnaireStep
from open_inwoner.questionnaire.tests.factories import QuestionnaireStepFactory


class QuestionnaireTestCase(WebTest):
    def setUp(self):
        QuestionnaireStepFactory(slug="foo", path="0001")
        QuestionnaireStepFactory(slug="foo-bar", path="0002")
        self.root_nodes = QuestionnaireStep.get_root_nodes()

    def test_home_page_contains_root_nodes(self):
        response = self.app.get(reverse("root"))

        self.assertEquals(response.context.get("questionnaire_roots").count(), 2)
        self.assertContains(response, self.root_nodes[0].get_absolute_url())
        self.assertContains(response, self.root_nodes[1].get_absolute_url())

    def test_user_home_page_does_not_contain_root_nodes(self):
        user = UserFactory()
        response = self.app.get(reverse("root"), user=user)

        self.assertNotContains(response, self.root_nodes[0].get_absolute_url())
        self.assertNotContains(response, self.root_nodes[1].get_absolute_url())

    def test_home_page_contains_up_to_six_objects(self):
        for i in range(5):
            QuestionnaireStepFactory(slug=f"foo{i+1}", path=f"000{i+5}")
        response = self.app.get(reverse("root"))

        self.assertEquals(response.context.get("questionnaire_roots").count(), 6)
