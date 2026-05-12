from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _

from cms import api

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    UserFactory,
    eHerkenningUserFactory,
)
from open_inwoner.cms.benefits.cms_apps import SSDApphook
from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.collaborate.cms_apps import CollaborateApphook
from open_inwoner.cms.extensions.models import CommonExtension
from open_inwoner.cms.inbox.cms_apps import InboxApphook
from open_inwoner.cms.products.cms_apps import ProductsApphook
from open_inwoner.cms.profile.cms_appconfig import ProfileConfig
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests import cms_tools
from open_inwoner.cms.tests.cms_tools import (
    create_apphook_page,
    create_homepage,
    publish_page,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.core.views import _get_category_data_for_user
from open_inwoner.pdc.tests.factories import CategoryFactory, ProductFactory
from open_inwoner.questionnaire.tests.factories import QuestionnaireStepFactory


class SitemapCategoryDataTest(TestCase):
    def test_display_categories_simple(self):
        """No children, no products"""
        anon_user = AnonymousUser()
        category = CategoryFactory()

        res = _get_category_data_for_user(category, anon_user)

        self.assertEqual(res["category"], category)
        self.assertEqual(len(res["sub_categories"]), 0)
        self.assertEqual(list(res["products"]), [])

    def test_display_category_children(self):
        """Test display of category children, no nesting, no products"""
        anon_user = AnonymousUser()

        scenarios = [
            (True, True, 2),
            (True, False, 1),
            (False, True, 1),
            (False, False, 1),
        ]
        for published, visible, result in scenarios:
            with self.subTest(f"published: {published}, visible: {visible}"):
                root_category = CategoryFactory()
                # sanity check: one category is always visible
                root_category.add_child(
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=True,
                )
                root_category.add_child(
                    slug=f"child2-published-{published}-visible-{visible}",
                    published=published,
                    visible_for_anonymous=visible,
                )

                res = _get_category_data_for_user(root_category, anon_user)

                self.assertEqual(len(res["sub_categories"]), result)

    def test_display_category_products(self):
        """Test display of category products, no children"""
        anon_user = AnonymousUser()

        scenarios = [(True, 2), (False, 1)]
        for published, result in scenarios:
            with self.subTest(f"published: {published}"):
                root_category = CategoryFactory()
                # sanity check: one product is always visible
                ProductFactory(
                    name=get_random_string(length=8),
                    categories=(root_category,),
                )
                ProductFactory(
                    name=get_random_string(length=8),
                    categories=(root_category,),
                    published=published,
                )

                res = _get_category_data_for_user(root_category, anon_user)

                self.assertEqual(len(res["products"]), result)

    def test_display_categories_nested(self):
        """Test display of nested category structure"""
        anon_user = AnonymousUser()

        root_category = CategoryFactory()
        # children
        root_child1 = root_category.add_child(
            name="root child 1",
            slug="root-child-1",
            published=True,
            visible_for_anonymous=True,
        )
        root_child2 = root_category.add_child(
            name="root child 2",
            slug="root-child-2",
            published=True,
            visible_for_anonymous=True,
        )
        root_category.add_child(
            name="root child invisible",
            slug="root-child-invisible",
            published=True,
            visible_for_anonymous=False,
        )
        # nested children
        nested_child_1 = root_child1.add_child(
            name="nested child 1",
            slug="nested-child-1",
            published=True,
            visible_for_anonymous=True,
        )
        nested_child_2 = root_child1.add_child(
            name="nested child 2",
            slug="nested-child-2",
            published=True,
            visible_for_anonymous=True,
        )
        # products
        prod1 = ProductFactory(
            name="prod1",
            categories=(nested_child_1,),
            published=True,
        )
        ProductFactory(
            name="prod2",
            categories=(nested_child_1,),
            published=False,
        )

        res = _get_category_data_for_user(root_category, anon_user)

        # Unfortunately we cannot use `self.assertEqual` on `res` since
        # `res` contains empty instances of `ProductQueryset` for which
        # `==` gives the wrong result; hence we need to resort to
        # piecemeal asserts

        # root
        self.assertEqual(res["category"], root_category)
        self.assertEqual(list(res["products"]), [])

        # sub categories level 1
        sub_categories = res["sub_categories"]
        self.assertEqual(len(sub_categories), 2)

        child1 = sub_categories[0]
        self.assertEqual(child1["category"], root_child1)
        self.assertEqual(list(child1["products"]), [])

        child2 = sub_categories[1]
        self.assertEqual(child2["category"], root_child2)
        self.assertEqual(list(child2["products"]), [])

        # sub categories level 2
        sub_sub_categories = child1["sub_categories"]
        self.assertEqual(len(sub_sub_categories), 2)

        nested_1 = sub_sub_categories[0]
        self.assertEqual(nested_1["category"], nested_child_1)
        self.assertEqual(list(nested_1["products"]), [prod1])

        nested_2 = sub_sub_categories[1]
        self.assertEqual(nested_2["category"], nested_child_2)
        self.assertEqual(list(nested_2["products"]), [])

    def test_display_category_visibility(self):
        """Test restriction of visibility for different users"""
        anon_user = AnonymousUser()
        digid_user = DigidUserFactory()
        eherkenning_user = eHerkenningUserFactory()

        scenarios_anon = [
            (True, True, True, 2),
            (True, True, False, 2),
            (True, False, True, 2),
            (True, False, False, 2),
            (False, True, True, 1),
            (False, True, False, 1),
            (False, False, True, 1),
            (False, False, False, 1),
        ]
        for visible_anon, visible_citizen, visible_eh, res_anon in scenarios_anon:
            with self.subTest(
                f"Scenario for anon user: {visible_anon}, {visible_citizen}, {visible_eh}"
            ):
                root_category = CategoryFactory()
                root_category.add_child(
                    name="root child 1",
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=True,
                    visible_for_citizens=True,
                    visible_for_companies=True,
                )
                root_category.add_child(
                    name="root child 2",
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=visible_anon,
                    visible_for_citizens=visible_citizen,
                    visible_for_companies=visible_eh,
                )

                res = _get_category_data_for_user(root_category, anon_user)

                self.assertEqual(len(res["sub_categories"]), res_anon)

        scenarios_citizen = [
            (True, True, True, 2),
            (True, True, False, 2),
            (True, False, True, 1),
            (True, False, False, 1),
            (False, True, True, 2),
            (False, True, False, 2),
            (False, False, True, 1),
            (False, False, False, 1),
        ]
        for visible_anon, visible_citizen, visible_eh, res_citizen in scenarios_citizen:
            with self.subTest(
                f"Scenario for anon user: {visible_anon}, {visible_citizen}, {visible_eh}"
            ):
                root_category = CategoryFactory()
                root_category.add_child(
                    name="root child 1",
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=True,
                    visible_for_citizens=True,
                    visible_for_companies=True,
                )
                root_category.add_child(
                    name="root child 2",
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=visible_anon,
                    visible_for_citizens=visible_citizen,
                    visible_for_companies=visible_eh,
                )

                res = _get_category_data_for_user(root_category, digid_user)

                self.assertEqual(len(res["sub_categories"]), res_citizen)

        scenarios_company = [
            (True, True, True, 2),
            (True, True, False, 1),
            (True, False, True, 2),
            (True, False, False, 1),
            (False, True, True, 2),
            (False, True, False, 1),
            (False, False, True, 2),
            (False, False, False, 1),
        ]
        for visible_anon, visible_citizen, visible_eh, res_company in scenarios_company:
            with self.subTest(
                f"Scenario for anon user: {visible_anon}, {visible_citizen}, {visible_eh}"
            ):
                root_category = CategoryFactory()
                root_category.add_child(
                    name="root child 1",
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=True,
                    visible_for_citizens=True,
                    visible_for_companies=True,
                )
                root_category.add_child(
                    name="root child 2",
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=visible_anon,
                    visible_for_citizens=visible_citizen,
                    visible_for_companies=visible_eh,
                )

                res = _get_category_data_for_user(root_category, eherkenning_user)

                self.assertEqual(len(res["sub_categories"]), res_company)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class SitemapViewTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

        # Homepage is required for sitemap
        create_homepage()

        self.config = SiteConfiguration.objects.create(name="Test Site")

    def test_sitemap_renders_for_anonymous_user(self):
        response = self.client.get(reverse("sitemap"))

        self.assertEqual(response.status_code, 200)
        # Verify sitemap heading is present
        self.assertContains(response, _("Links naar pagina's op "))

    def test_sitemap_renders_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("sitemap"))

        self.assertEqual(response.status_code, 200)
        # Verify sitemap heading is present
        self.assertContains(response, _("Links naar pagina's op "))

    def test_sitemap_includes_categories(self):
        cms_tools.create_apphook_page(ProductsApphook)
        category = CategoryFactory(published=True, visible_for_anonymous=True)

        response = self.client.get(reverse("sitemap"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(category.name.encode(), response.content)

    def test_sitemap_includes_platform_pages(self):
        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn(_("Home page"), content)
        self.assertIn(_("Login or create an account"), content)

    def test_sitemap_hides_login_for_authenticated_users(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertNotIn(_("Login or create an account"), content)

    # Contact form was removed from sitemap to avoid duplicates (see commit 7941087c9)
    # It now appears in footer via CMS pages if configured

    def test_sitemap_includes_benefits_page_when_published(self):
        create_apphook_page(SSDApphook)
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn(_("Mijn uitkeringen"), content)

    def test_sitemap_excludes_benefits_page_when_not_published(self):
        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertNotIn(_("Mijn uitkeringen"), content)

    def test_sitemap_includes_case_pages_when_published(self):
        create_apphook_page(CasesApphook)
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn(_("Mijn zaken"), content)
        self.assertIn(_("Mijn vragen"), content)

    def test_sitemap_includes_collaborate_page_when_published(self):
        create_apphook_page(CollaborateApphook)
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn(_("Mijn samenwerkingen"), content)

    def test_sitemap_includes_inbox_page_when_published(self):
        create_apphook_page(InboxApphook)
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn(_("Mijn berichten"), content)

    def test_sitemap_includes_products_page_when_published(self):
        create_apphook_page(ProductsApphook)
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn(_("Zelftest"), content)

    def test_sitemap_includes_profile_pages_when_published(self):
        create_apphook_page(ProfileApphook)
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn(_("Mijn profiel"), content)

    def test_sitemap_excludes_profile_section_for_anonymous_users(self):
        create_apphook_page(ProfileApphook)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertNotIn(_("Mijn profiel"), content)

    def test_sitemap_includes_profile_selected_categories(self):
        create_apphook_page(ProfileApphook, config_args={"selected_categories": True})
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn(_("Mijn Interessegebieden"), content)

    def test_sitemap_excludes_profile_selected_categories_when_disabled(self):
        create_apphook_page(ProfileApphook, config_args={"selected_categories": False})
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertNotIn(_("Mijn Interessegebieden"), content)

    def test_sitemap_includes_profile_my_contacts(self):
        create_apphook_page(ProfileApphook, config_args={"my_contacts": True})
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn(_("Mijn contacten"), content)

    def test_sitemap_excludes_profile_my_contacts_when_disabled(self):
        create_apphook_page(ProfileApphook, config_args={"my_contacts": False})
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertNotIn(_("Mijn contacten"), content)

    def test_sitemap_includes_profile_selfdiagnose(self):
        create_apphook_page(ProfileApphook, config_args={"selfdiagnose": True})
        QuestionnaireStepFactory.create(published=True)
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn(_("Zelfdiagnose"), content)

    def test_sitemap_excludes_profile_selfdiagnose_when_no_questionnaires(self):
        create_apphook_page(ProfileApphook, config_args={"selfdiagnose": True})
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertNotIn(_("Zelfdiagnose"), content)

    def test_sitemap_includes_profile_actions(self):
        create_apphook_page(ProfileApphook, config_args={"actions": True})
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn(_("Openstaande acties"), content)

    def test_sitemap_excludes_profile_actions_when_disabled(self):
        create_apphook_page(ProfileApphook, config_args={"actions": False})
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertNotIn(_("Openstaande acties"), content)

    def test_sitemap_includes_profile_notifications(self):
        create_apphook_page(ProfileApphook, config_args={"notifications": True})
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn(_("Notificatievoorkeuren"), content)

    def test_sitemap_excludes_profile_notifications_when_disabled(self):
        create_apphook_page(ProfileApphook, config_args={"notifications": False})
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertNotIn(_("Notificatievoorkeuren"), content)

    def test_sitemap_handles_multiple_profile_configs_gracefully(self):
        # Create first profile page with config
        create_apphook_page(
            ProfileApphook, config_args={"namespace": "profile1", "actions": True}
        )
        # Create second profile config
        ProfileConfig.objects.create(namespace="profile2", actions=False)
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))

        self.assertEqual(response.status_code, 200)

    def test_sitemap_includes_footer_cms_pages(self):
        page = api.create_page(
            "Privacy Policy", "cms/fullwidth.html", "nl", in_navigation=True
        )
        publish_page(page, "nl")
        self.config.cms_pages.add(page)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn("Privacy Policy", content)

    def test_sitemap_excludes_auth_required_footer_pages_for_anonymous(self):
        # Create a CMS page that requires auth
        page = api.create_page(
            "Members Only", "cms/fullwidth.html", "nl", in_navigation=True
        )
        publish_page(page, "nl")
        published_page = page
        CommonExtension.objects.create(
            extended_object=published_page, requires_auth=True
        )
        # Add to site configuration
        self.config.cms_pages.add(page)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertNotIn("Members Only", content)

    def test_sitemap_includes_auth_required_footer_pages_for_authenticated(self):
        # Create a CMS page that requires auth
        page = api.create_page(
            "Members Only", "cms/fullwidth.html", "nl", in_navigation=True
        )
        publish_page(page, "nl")
        published_page = page
        CommonExtension.objects.create(
            extended_object=published_page, requires_auth=True
        )
        # Add to site configuration
        self.config.cms_pages.add(page)
        self.client.force_login(self.user)

        response = self.client.get(reverse("sitemap"))
        content = response.content.decode()

        self.assertIn("Members Only", content)
