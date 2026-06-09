from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings

from cms.api import add_plugin
from cms.models import CMSPlugin, Page, PageContent, Placeholder
from django_setup_configuration.test_utils import execute_single_step
from djangocms_versioning.constants import PUBLISHED

from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.plugins.models.tasks import TasksConfig
from open_inwoner.cms.plugins.models.zaken import CMSZakenPluginConfig
from open_inwoner.cms.profile.cms_appconfig import ProfileConfig
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests.cms_tools import create_homepage
from open_inwoner.cms.utils.page_display import (
    case_page_is_published,
    profile_page_is_published,
)
from open_inwoner.cms.utils.page_setup import CMS_BOOTSTRAP_USER_EMAIL
from open_inwoner.configurations.bootstrap.cms import (
    _APP_HOOKS,
    CMSPagesConfigurationModel,
    CMSPagesConfigurationStep,
)
from open_inwoner.openklant.cms_apps import OpenklantApphook

BASE_DIR = Path(__file__).parent / "files"
CMS_PAGES_STEP_HOMEPAGE = str(BASE_DIR / "cms_pages_step_homepage.yaml")
CMS_PAGES_STEP_HOMEPAGE_WITH_CASES = str(
    BASE_DIR / "cms_pages_step_homepage_with_cases.yaml"
)
CMS_PAGES_STEP_CASES_WITH_EXTENSION = str(
    BASE_DIR / "cms_pages_step_cases_with_extension.yaml"
)
CMS_PAGES_STEP_PROFILE_WITH_TOGGLES = str(
    BASE_DIR / "cms_pages_step_profile_with_toggles.yaml"
)
CMS_PAGES_STEP_MULTIPLE_PAGES = str(BASE_DIR / "cms_pages_step_multiple_pages.yaml")
CMS_PAGES_STEP_NOTHING_ENABLED = str(BASE_DIR / "cms_pages_step_nothing_enabled.yaml")
CMS_PAGES_STEP_HOMEPAGE_WITH_PLUGINS = str(
    BASE_DIR / "cms_pages_step_homepage_with_plugins.yaml"
)


def _page_is_published(hook_class) -> bool:
    page = Page.objects.filter(application_urls=hook_class.__name__).first()
    if not page:
        return False
    return PageContent._original_manager.filter(
        page=page, versions__state=PUBLISHED
    ).exists()


def _published_content_placeholder(page: Page, slot: str, language: str = "nl"):
    content = PageContent._original_manager.get(
        page=page, language=language, versions__state=PUBLISHED
    )
    return Placeholder.objects.get(
        slot=slot,
        content_type=ContentType.objects.get_for_model(content),
        object_id=content.pk,
    )


class AppHookMappingTests(TestCase):
    def test_every_apphook_maps_to_a_configuration_field(self):
        model_fields = set(CMSPagesConfigurationModel.model_fields)

        self.assertTrue(set(_APP_HOOKS).issubset(model_fields))

        # every configurable page except the homepage is backed by an apphook
        self.assertEqual(model_fields - set(_APP_HOOKS), {"homepage"})


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CMSPagesConfigurationStepTests(TestCase):
    def test_cases_page_created_with_explicit_extension_settings(self):
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_CASES_WITH_EXTENSION,
        )

        self.assertTrue(case_page_is_published())

        page = Page.objects.get(application_urls=CasesApphook.__name__)
        extension = page.commonextension

        self.assertTrue(extension.requires_auth)
        self.assertTrue(extension.requires_auth_bsn_or_kvk)
        self.assertEqual(extension.menu_indicator, "inbox_new_messages")
        self.assertEqual(extension.menu_icon, "inventory_2")

    def test_profile_page_section_toggles_applied(self):
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_PROFILE_WITH_TOGGLES,
        )

        self.assertTrue(profile_page_is_published())

        config = ProfileConfig.objects.get()

        self.assertFalse(config.my_data)
        self.assertFalse(config.selected_categories)
        self.assertFalse(config.mentors)
        self.assertFalse(config.my_contacts)
        self.assertFalse(config.selfdiagnose)
        self.assertFalse(config.actions)
        self.assertFalse(config.notifications)
        self.assertFalse(config.questions)
        self.assertTrue(config.ssd)
        self.assertTrue(config.newsletters)
        self.assertTrue(config.appointments)

    def test_profile_page_extension_settings_applied(self):
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_PROFILE_WITH_TOGGLES,
        )

        page = Page.objects.get(application_urls="ProfileApphook")
        extension = page.commonextension

        self.assertTrue(extension.requires_auth)
        self.assertTrue(extension.requires_auth_bsn_or_kvk)

    def test_only_enabled_pages_are_created(self):
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_MULTIPLE_PAGES,
        )

        self.assertTrue(case_page_is_published())
        self.assertTrue(_page_is_published(OpenklantApphook))

        self.assertFalse(profile_page_is_published())
        self.assertEqual(Page.objects.count(), 2)

    def test_enabled_pages_have_default_extension_values(self):
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_MULTIPLE_PAGES,
        )

        page = Page.objects.get(application_urls=CasesApphook.__name__)
        extension = page.commonextension

        self.assertFalse(extension.requires_auth)
        self.assertFalse(extension.requires_auth_bsn_or_kvk)
        self.assertEqual(extension.menu_indicator, "")
        self.assertEqual(extension.menu_icon, "")

    def test_homepage_created_and_set_as_site_root(self):
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_HOMEPAGE,
        )

        page = Page.objects.get(reverse_id="home")

        self.assertTrue(page.is_home)
        self.assertTrue(
            PageContent._original_manager.filter(
                page=page, versions__state=PUBLISHED
            ).exists()
        )
        self.assertEqual(
            PageContent._original_manager.get(page=page, language="nl").title,
            "Welkom",
        )

    def test_homepage_creation_is_idempotent(self):
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_HOMEPAGE,
        )
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_HOMEPAGE,
        )

        self.assertEqual(Page.objects.filter(reverse_id="home").count(), 1)

    def test_apphook_page_creation_is_idempotent(self):
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_CASES_WITH_EXTENSION,
        )
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_CASES_WITH_EXTENSION,
        )

        self.assertEqual(
            Page.objects.filter(application_urls=CasesApphook.__name__).count(), 1
        )

    def test_apphook_pages_are_children_of_homepage(self):
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_HOMEPAGE_WITH_CASES,
        )

        homepage = Page.objects.get(reverse_id="home")
        cases_page = Page.objects.get(application_urls=CasesApphook.__name__)

        self.assertEqual(cases_page.parent_page, homepage)

    def test_apphook_pages_are_nested_under_pre_existing_homepage(self):
        """A homepage that already exists is used even if it is not enabled."""
        homepage = create_homepage()

        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_CASES_WITH_EXTENSION,
        )

        cases_page = Page.objects.get(application_urls=CasesApphook.__name__)

        self.assertEqual(cases_page.parent_page, homepage)

    def test_rerun_with_a_different_title_overwrites_the_admin_edit(self):
        """
        Simulates an admin editing a page's title after it was bootstrapped:
        re-running the step overwrites that edit, without touching the page
        (or anything else on it) otherwise.
        """
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_CASES_WITH_EXTENSION,
        )
        page = Page.objects.get(application_urls=CasesApphook.__name__)
        PageContent._original_manager.filter(page=page, language="nl").update(
            title="Admin-edited title"
        )

        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_CASES_WITH_EXTENSION,
        )

        same_page = Page.objects.get(application_urls=CasesApphook.__name__)
        self.assertEqual(same_page.pk, page.pk)
        published_content = PageContent._original_manager.get(
            page=same_page, language="nl", versions__state=PUBLISHED
        )
        self.assertNotEqual(published_content.title, "Admin-edited title")

    def test_rerun_does_not_touch_manually_added_plugin_content(self):
        """
        Overwriting title/extension/config on a re-run must not delete or
        otherwise disturb content an editor added to the page through the
        CMS page builder.
        """
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_CASES_WITH_EXTENSION,
        )
        page = Page.objects.get(application_urls=CasesApphook.__name__)
        page_content = PageContent._original_manager.get(page=page, language="nl")
        placeholder = Placeholder.objects.create(
            slot="content",
            content_type=ContentType.objects.get_for_model(page_content),
            object_id=page_content.pk,
        )
        add_plugin(placeholder, "TextPlugin", "nl", body="hello")

        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_CASES_WITH_EXTENSION,
        )

        self.assertTrue(Placeholder.objects.filter(pk=placeholder.pk).exists())
        self.assertEqual(CMSPlugin.objects.filter(placeholder=placeholder).count(), 1)

    def test_bootstrap_user_is_not_privileged(self):
        """
        The account recorded as the author of bootstrapped pages must not be a
        superuser: it is created in production databases, cannot be deleted
        (``Version.created_by`` is PROTECTed) and would be adopted by the OIDC
        backends on an email match.
        """
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_HOMEPAGE_WITH_CASES,
        )

        user = get_user_model().objects.get(email=CMS_BOOTSTRAP_USER_EMAIL)

        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_active)
        self.assertFalse(user.has_usable_password())

        self.assertFalse(
            get_user_model().objects.filter(is_superuser=True).exists(),
            "the step must not create superusers",
        )

    def test_existing_profile_config_is_overwritten(self):
        """
        Admin edits to an existing app config (e.g. ProfileConfig) don't
        survive a re-run: the step overwrites its fields to match the
        configuration, the same as it does for the page itself.
        """
        ProfileConfig.objects.create(namespace=ProfileApphook.app_name, my_data=True)

        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_PROFILE_WITH_TOGGLES,
        )

        config = ProfileConfig.objects.get()

        self.assertFalse(config.my_data)
        self.assertTrue(profile_page_is_published())

    def test_homepage_plugins_created_and_published(self):
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_HOMEPAGE_WITH_PLUGINS,
        )

        page = Page.objects.get(reverse_id="home")
        placeholder = _published_content_placeholder(page, "content")

        zaken = CMSZakenPluginConfig.objects.get(placeholder=placeholder)
        self.assertEqual(zaken.title, "Mijn zaken")
        self.assertEqual(zaken.num_zaken, 6)

        tasks = TasksConfig.objects.get(placeholder=placeholder)
        self.assertEqual(tasks.title, "Mijn taken")

    def test_homepage_plugins_rerun_with_unchanged_config_is_a_no_op(self):
        """
        Nothing to converge means no new page version, so an unrelated
        rerun doesn't churn through page versions.
        """
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_HOMEPAGE_WITH_PLUGINS,
        )
        page = Page.objects.get(reverse_id="home")
        content_before = PageContent._original_manager.get(
            page=page, language="nl", versions__state=PUBLISHED
        )

        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_HOMEPAGE_WITH_PLUGINS,
        )

        content_after = PageContent._original_manager.get(
            page=page, language="nl", versions__state=PUBLISHED
        )
        self.assertEqual(content_before.pk, content_after.pk)

    def test_homepage_plugin_rerun_with_a_different_value_overwrites_the_admin_edit(
        self,
    ):
        """
        Simulates an admin editing a plugin's field after it was bootstrapped:
        re-running the step overwrites that edit. Publishing the change
        creates a new page version, which must still carry over any other
        content an editor added independently (e.g. another plugin).
        """
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_HOMEPAGE_WITH_PLUGINS,
        )
        page = Page.objects.get(reverse_id="home")
        placeholder = _published_content_placeholder(page, "content")
        add_plugin(placeholder, "TextPlugin", "nl", body="hello")

        zaken = CMSZakenPluginConfig.objects.get(placeholder=placeholder)
        zaken.num_zaken = 1
        zaken.save()

        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_HOMEPAGE_WITH_PLUGINS,
        )

        new_placeholder = _published_content_placeholder(page, "content")
        self.assertEqual(
            CMSZakenPluginConfig.objects.get(placeholder=new_placeholder).num_zaken,
            6,
        )
        self.assertEqual(
            CMSPlugin.objects.filter(
                placeholder=new_placeholder, plugin_type="TextPlugin"
            ).count(),
            1,
        )

    def test_homepage_plugin_omitted_from_config_is_left_alone_on_rerun(self):
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_HOMEPAGE_WITH_PLUGINS,
        )
        page = Page.objects.get(reverse_id="home")

        execute_single_step(
            CMSPagesConfigurationStep,
            object_source={
                "cms_pages_config_enable": True,
                "cms_pages_config": {
                    "homepage": {"enabled": True, "title": "Welkom"},
                },
            },
        )

        placeholder = _published_content_placeholder(page, "content")
        self.assertTrue(
            CMSZakenPluginConfig.objects.filter(placeholder=placeholder).exists()
        )
        self.assertTrue(TasksConfig.objects.filter(placeholder=placeholder).exists())

    def test_no_service_account_is_created_when_nothing_is_enabled(self):
        execute_single_step(
            CMSPagesConfigurationStep,
            yaml_source=CMS_PAGES_STEP_NOTHING_ENABLED,
        )

        self.assertFalse(Page.objects.exists())
        self.assertFalse(
            get_user_model().objects.filter(email=CMS_BOOTSTRAP_USER_EMAIL).exists()
        )
