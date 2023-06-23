from django.test import TestCase, override_settings

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.products.cms_apps import ProductsApphook
from open_inwoner.cms.products.cms_plugins import QuestionnairePlugin
from open_inwoner.cms.tests import cms_tools
from open_inwoner.pdc.tests.factories import CategoryFactory
from open_inwoner.questionnaire.models import QuestionnaireStep
from open_inwoner.questionnaire.tests.factories import QuestionnaireStepFactory


class TestPluginBasics(TestCase):
    def test_no_output_generated_without_apphook(self):
        html, context = cms_tools.render_plugin(QuestionnairePlugin)
        self.assertEqual("", html)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestHighlightedQuestionnaire(WebTest):
    def setUp(self):
        self.category = CategoryFactory()
        self.questionnaire = QuestionnaireStepFactory(
            path="0001", category=self.category
        )
        self.highlighted_questionnaire_1 = QuestionnaireStepFactory(
            path="0003", category=self.category, highlighted=True
        )
        self.highlighted_questionnaire_2 = QuestionnaireStepFactory(
            path="0004", category=self.category, highlighted=True
        )
        self.highlighted_questionnaire_3 = QuestionnaireStepFactory(
            path="0005", category=self.category, highlighted=True
        )
        cms_tools.create_apphook_page(ProductsApphook)

    def test_only_highlighted_questionnaires_are_shown_on_anonymous_plugin(self):
        html, context = cms_tools.render_plugin(QuestionnairePlugin)
        self.assertEqual(
            list(context["questionnaire_roots"]),
            [
                self.highlighted_questionnaire_1,
                self.highlighted_questionnaire_2,
                self.highlighted_questionnaire_3,
            ],
        )

    def test_only_highlighted_questionnaires_are_shown_on_user_plugin(self):
        user = UserFactory()
        html, context = cms_tools.render_plugin(QuestionnairePlugin, user=user)
        self.assertEqual(
            list(context["questionnaire_roots"]),
            [
                self.highlighted_questionnaire_1,
                self.highlighted_questionnaire_2,
                self.highlighted_questionnaire_3,
            ],
        )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class QuestionnaireTestCase(WebTest):
    def setUp(self):
        QuestionnaireStepFactory(code="foo", slug="foo", path="0001", highlighted=True)
        QuestionnaireStepFactory(
            code="foo-bar", slug="foo-bar", path="0002", highlighted=True
        )
        self.root_nodes = QuestionnaireStep.get_root_nodes()

        cms_tools.create_apphook_page(ProductsApphook)

    def test_home_page_contains_highlighted_root_nodes(self):
        html, context = cms_tools.render_plugin(QuestionnairePlugin)
        html, context = cms_tools.render_plugin(QuestionnairePlugin)

        self.assertEquals(context.get("questionnaire_roots").count(), 2)
        self.assertIn(self.root_nodes[0].get_absolute_url(), html)
        self.assertIn(self.root_nodes[1].get_absolute_url(), html)

    def test_user_home_page_contains_highlighted_root_nodes(self):
        user = UserFactory()
        html, context = cms_tools.render_plugin(QuestionnairePlugin, user=user)

        self.assertIn(self.root_nodes[0].get_absolute_url(), html)
        self.assertIn(self.root_nodes[1].get_absolute_url(), html)

    def test_home_page_doesnt_show_unpublished_nodes(self):
        QuestionnaireStep.objects.update(published=False)

        html, context = cms_tools.render_plugin(QuestionnairePlugin)
        self.assertNotIn(self.root_nodes[0].get_absolute_url(), html)
        self.assertNotIn(self.root_nodes[1].get_absolute_url(), html)

    def test_user_home_page_doesnt_show_unpublished_nodes(self):
        QuestionnaireStep.objects.update(published=False)

        user = UserFactory()
        html, context = cms_tools.render_plugin(QuestionnairePlugin, user=user)
        self.assertNotIn(self.root_nodes[0].get_absolute_url(), html)
        self.assertNotIn(self.root_nodes[1].get_absolute_url(), html)
