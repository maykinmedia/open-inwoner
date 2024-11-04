from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.pdc.tests.factories import ProductFactory
from open_inwoner.questionnaire.tests.factories import QuestionnaireStepFactory

from ..models import QuestionnaireStep


@disable_admin_mfa()
class TestQuestionnaireStepForm(WebTest):
    def setUp(self):
        self.user = UserFactory(is_superuser=True, is_staff=True)

    def test_user_can_highlight_root_questionnaire_from_change_form_page(self):
        form = self.app.get(
            reverse("admin:questionnaire_questionnairestep_add"), user=self.user
        ).forms["questionnairestep_form"]
        form["question"] = "A question"
        form["question_subject"] = "subject"
        form["slug"] = "a-question"
        form["code"] = "some code text"
        form["_position"] = "first-child"
        form["_ref_node_id"] = 0
        form["highlighted"] = True
        form.submit()
        questionnaire = QuestionnaireStep.objects.first()
        self.assertEqual(questionnaire.slug, "a-question")

    def test_user_cannot_highlight_child_questionnaire_from_change_form_page(self):
        questionnaire = QuestionnaireStepFactory(path="0001")
        form = self.app.get(
            reverse("admin:questionnaire_questionnairestep_add"), user=self.user
        ).forms["questionnairestep_form"]
        form["question"] = "This should not work"
        form["question_subject"] = "subject"
        form["slug"] = "this-should-not-work"
        form["code"] = "some code text"
        form["_position"] = "first-child"
        form["_ref_node_id"] = questionnaire.id
        form["highlighted"] = True
        form.submit()
        questionnaires = QuestionnaireStep.objects.filter(slug="this-should-not-work")
        self.assertEqual(questionnaires.count(), 0)

    def test_user_can_highlight_root_questionnaire_from_change_list_page(self):
        QuestionnaireStepFactory(path="0001")
        form = self.app.get(
            reverse("admin:questionnaire_questionnairestep_changelist"), user=self.user
        ).forms["changelist-form"]
        form["form-0-highlighted"] = True
        response = form.submit("_save")
        updated_questionnaire = QuestionnaireStep.objects.first()
        self.assertTrue(updated_questionnaire.highlighted)
        self.assertRedirects(
            response, reverse("admin:questionnaire_questionnairestep_changelist")
        )

    def test_user_cannot_highlight_child_questionnaire_from_change_list_page(self):
        root = QuestionnaireStepFactory(path="0001")
        root.add_child()
        form = self.app.get(
            reverse("admin:questionnaire_questionnairestep_changelist"), user=self.user
        ).forms["changelist-form"]
        form["form-1-highlighted"] = True
        response = form.submit("_save")
        updated_questionnaire = QuestionnaireStep.objects.first()
        self.assertFalse(updated_questionnaire.highlighted)
        self.assertContains(
            response,
            _("Only root nodes (parent questionnaire steps) can be highlighted."),
        )

    def test_draft_related_products_are_not_rendered(self):
        product1 = ProductFactory()
        product2 = ProductFactory()
        product3 = ProductFactory(published=False)
        questionnaire = QuestionnaireStepFactory(
            related_products=(product1, product2, product3)
        )

        form = self.app.get(
            reverse(
                "admin:questionnaire_questionnairestep_change",
                kwargs={"object_id": questionnaire.id},
            ),
            user=self.user,
        ).forms["questionnairestep_form"]
        options = form["related_products"].options

        self.assertIn((str(product1.id), True, product1.name), options)
        self.assertIn((str(product2.id), True, product2.name), options)
        self.assertNotIn((str(product3.id), True, product3.name), options)
