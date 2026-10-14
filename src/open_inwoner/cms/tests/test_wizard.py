from django.test import TestCase

from cms.cms_wizards import cms_page_wizard, cms_subpage_wizard
from cms.models import PageContent
from cms.utils.urlutils import admin_reverse
from cms.wizards.forms import WizardStep2BaseForm
from maykin_2fa.test import disable_admin_mfa

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.tests import cms_tools


@disable_admin_mfa()
class WizardCreateViewTests(TestCase):
    """
    Regression tests for #3088: with django-formtools < 2.4, the second step of the
    wizard was built with django-cms's placeholder form and crashed.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # see the helper's docstring: otherwise versioning can't find the versions
        cms_tools.reset_versionables_content_type_cache()

        cls.user = UserFactory(is_staff=True, is_superuser=True)

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def create_through_wizard(self, entry, page, title, slug):
        url = admin_reverse("cms_wizard_create")

        response = self.client.post(
            url,
            {
                "wizard_create_view-current_step": "0",
                "0-entry": entry.id,
                "0-language": "nl",
                "0-page": page.pk if page else "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], WizardStep2BaseForm)

        response = self.client.post(
            url,
            {
                "wizard_create_view-current_step": "1",
                "1-title": title,
                "1-slug": slug,
            },
        )

        self.assertEqual(response.status_code, 200)

    def test_create_first_page(self):
        self.create_through_wizard(cms_page_wizard, None, "Home", "home")

        self.assertEqual(
            list(PageContent.admin_manager.values_list("title", "language")),
            [("Home", "nl")],
        )

    def test_create_subpage(self):
        homepage = cms_tools.create_homepage()

        self.create_through_wizard(cms_subpage_wizard, homepage, "Sub", "sub")

        subpage = PageContent.admin_manager.get(title="Sub").page
        self.assertEqual(subpage.get_parent_page(), homepage)
