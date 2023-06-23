from django.test import override_settings

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.collaborate.cms_apps import CollaborateApphook
from open_inwoner.cms.collaborate.cms_plugins import ActivePlansPlugin
from open_inwoner.cms.tests import cms_tools
from open_inwoner.plans.tests.factories import PlanFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestActivePlansPlugin(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.plan = PlanFactory.create(plan_contacts=[self.user])

        PlanFactory.create(plan_contacts=[UserFactory()])

    def test_connected_plans_are_rendered_when_logged_in(self):
        cms_tools.create_apphook_page(CollaborateApphook)

        html, context = cms_tools.render_plugin(ActivePlansPlugin, user=self.user)

        self.assertEqual(list(context["plans"]), [self.plan])

    def test_connected_plans_are_not_rendered_when_anonymous(self):
        cms_tools.create_apphook_page(CollaborateApphook)

        html, context = cms_tools.render_plugin(ActivePlansPlugin)

        self.assertNotIn("plans", context)

    def test_no_output_generated_without_apphook(self):
        html, context = cms_tools.render_plugin(ActivePlansPlugin)
        self.assertEqual("", html)
