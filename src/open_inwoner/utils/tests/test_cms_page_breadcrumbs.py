from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from cms.appresolver import clear_app_resolvers, get_app_patterns
from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.collaborate.cms_apps import CollaborateApphook
from open_inwoner.cms.profile.cms_appconfig import ProfileConfig
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests import cms_tools
from open_inwoner.plans.tests.factories import PlanFactory
from open_inwoner.utils.views import get_cms_page_title


class GetCMSPageTitleTests(TestCase):
    def test_returns_title_of_current_cms_page(self):
        page = cms_tools.create_apphook_page(CollaborateApphook, title="Samen doen")
        request = RequestFactory().get("/")
        request.current_page = page

        self.assertEqual(get_cms_page_title(request, "fallback"), "Samen doen")

    def test_returns_fallback_without_current_cms_page(self):
        request = RequestFactory().get("/")

        self.assertEqual(get_cms_page_title(request, "fallback"), "fallback")

        request.current_page = None

        self.assertEqual(get_cms_page_title(request, "fallback"), "fallback")


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CMSPageBreadcrumbsTests(WebTest):
    def setUp(self):
        self.user = UserFactory()
        cms_tools.create_homepage()
        ProfileConfig.objects.create(namespace=ProfileApphook.app_name)
        cms_tools.create_apphook_page(ProfileApphook, title="Mijn omgeving")
        cms_tools.create_apphook_page(CollaborateApphook, title="Samen doen")

        # The CMS resolves the page behind an apphook sub-URL with resolvers that
        # are built once per process, so rebuild them for the pages created here
        clear_app_resolvers()
        get_app_patterns()
        self.addCleanup(clear_app_resolvers)

    def test_nested_profile_page_uses_cms_page_title(self):
        response = self.app.get(reverse("profile:contact_list"), user=self.user)

        crumbs = response.pyquery(".breadcrumbs__list-item")
        self.assertIn("Mijn omgeving", crumbs[1].text_content())

    def test_plan_detail_uses_cms_page_title(self):
        plan = PlanFactory(created_by=self.user)
        plan.plan_contacts.add(self.user)

        response = self.app.get(
            reverse("collaborate:plan_detail", kwargs={"uuid": plan.uuid}),
            user=self.user,
        )

        crumbs = response.pyquery(".breadcrumbs__list-item")
        self.assertIn("Samen doen", crumbs[1].text_content())
        self.assertIn(plan.title, crumbs[2].text_content())
