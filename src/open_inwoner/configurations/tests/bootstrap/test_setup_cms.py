from django.test import TestCase, override_settings

from cms.models import Page

from open_inwoner.cms.profile.cms_apps import ProfileConfig
from open_inwoner.cms.utils.page_display import (
    benefits_page_is_published,
    case_page_is_published,
    collaborate_page_is_published,
    inbox_page_is_published,
    products_page_is_published,
    profile_page_is_published,
)

from ...bootstrap.cms import (
    CMSBenefitsConfigurationStep,
    CMSCasesConfigurationStep,
    CMSCollaborateConfigurationStep,
    CMSInboxConfigurationStep,
    CMSProductsConfigurationStep,
    CMSProfileConfigurationStep,
)


class CMSSetupConfigurationTest(TestCase):
    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
        CMS_CONFIG_PROFILE_ENABLE=True,
    )
    def test_cms_profile_configure_use_defaults(self):
        configuration_step = CMSProfileConfigurationStep()

        configuration_step.configure()

        self.assertTrue(configuration_step.is_configured())

        self.assertTrue(profile_page_is_published())

        # check profile config
        config = ProfileConfig.objects.get()

        self.assertTrue(config.my_data)
        self.assertTrue(config.selected_categories)
        self.assertTrue(config.mentors)
        self.assertTrue(config.my_contacts)
        self.assertTrue(config.selfdiagnose)
        self.assertTrue(config.actions)
        self.assertTrue(config.notifications)
        self.assertTrue(config.questions)
        self.assertFalse(config.ssd)
        self.assertFalse(config.newsletters)
        self.assertFalse(config.appointments)

        # check common extension
        page = Page.objects.get(publisher_is_draft=False)
        self.assertIsNone(getattr(page, "commonextension", None))

    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
        CMS_CONFIG_PROFILE_ENABLE=True,
        # profile config
        CMS_PROFILE_MY_DATA=False,
        CMS_PROFILE_SELECTED_CATEGORIES=False,
        CMS_PROFILE_MENTORS=False,
        CMS_PROFILE_MY_CONTACTS=False,
        CMS_PROFILE_SELFDIAGNOSE=False,
        CMS_PROFILE_ACTIONS=False,
        CMS_PROFILE_NOTIFICATIONS=False,
        CMS_PROFILE_QUESTIONS=False,
        CMS_PROFILE_SSD=True,
        CMS_PROFILE_NEWSLETTERS=True,
        CMS_PROFILE_APPOINTMENTS=True,
        # common extension settings
        CMS_PROFILE_REQUIRES_AUTH=True,
        CMS_PROFILE_REQUIRES_AUTH_BSN_OR_KVK=True,
        CMS_PROFILE_MENU_INDICATOR="arrow",
        CMS_PROFILE_MENU_ICON="smiley",
    )
    def test_cms_profile_configure_override_settings(self):
        configuration_step = CMSProfileConfigurationStep()

        configuration_step.configure()

        self.assertTrue(profile_page_is_published())

        # check profile config
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

        # check common extension
        page = Page.objects.get(publisher_is_draft=False)
        extension = page.commonextension

        self.assertTrue(extension.requires_auth)
        self.assertTrue(extension.requires_auth_bsn_or_kvk)
        self.assertEqual(extension.menu_indicator, "arrow")
        self.assertEqual(extension.menu_icon, "smiley")

    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
    )
    def test_cms_profile_not_configured(self):
        configuration_step = CMSProfileConfigurationStep()

        configuration_step.configure()

        self.assertFalse(configuration_step.is_configured())

        self.assertFalse(profile_page_is_published())

    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
        CMS_CONFIG_SSD_ENABLE=True,
    )
    def test_cms_ssd_configured(self):
        configuration_step = CMSBenefitsConfigurationStep()

        configuration_step.configure()

        self.assertTrue(configuration_step.is_configured())

        self.assertTrue(benefits_page_is_published())

        # check common extension
        page = Page.objects.get(publisher_is_draft=False)
        self.assertIsNone(getattr(page, "commonextension", None))

    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
        CMS_CONFIG_SSD_ENABLE=True,
        CMS_SSD_REQUIRES_AUTH=True,
        CMS_SSD_REQUIRES_AUTH_BSN_OR_KVK=True,
        CMS_SSD_MENU_INDICATOR="arrow",
        CMS_SSD_MENU_ICON="smiley",
    )
    def test_cms_ssd_override_settings(self):
        configuration_step = CMSBenefitsConfigurationStep()

        configuration_step.configure()

        self.assertTrue(configuration_step.is_configured())

        self.assertTrue(benefits_page_is_published())

        # check common extension
        page = Page.objects.get(publisher_is_draft=False)
        extension = page.commonextension

        self.assertTrue(extension.requires_auth)
        self.assertTrue(extension.requires_auth_bsn_or_kvk)
        self.assertEqual(extension.menu_indicator, "arrow")
        self.assertEqual(extension.menu_icon, "smiley")

    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
        CMS_CONFIG_CASES_ENABLE=True,
    )
    def test_cms_cases_configured(self):
        configuration_step = CMSCasesConfigurationStep()

        configuration_step.configure()

        self.assertTrue(configuration_step.is_configured())

        self.assertTrue(case_page_is_published())

        # check common extension
        page = Page.objects.get(publisher_is_draft=False)
        self.assertIsNone(getattr(page, "commonextension", None))

    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
        CMS_CONFIG_CASES_ENABLE=True,
        CMS_CASES_REQUIRES_AUTH=True,
        CMS_CASES_REQUIRES_AUTH_BSN_OR_KVK=True,
        CMS_CASES_MENU_INDICATOR="arrow",
        CMS_CASES_MENU_ICON="smiley",
    )
    def test_cms_cases_override_settings(self):
        configuration_step = CMSCasesConfigurationStep()

        configuration_step.configure()

        self.assertTrue(configuration_step.is_configured())

        self.assertTrue(case_page_is_published())

        # check common extension
        page = Page.objects.get(publisher_is_draft=False)
        extension = page.commonextension

        self.assertTrue(extension.requires_auth)
        self.assertTrue(extension.requires_auth_bsn_or_kvk)
        self.assertEqual(extension.menu_indicator, "arrow")
        self.assertEqual(extension.menu_icon, "smiley")

    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
        CMS_CONFIG_COLLABORATE_ENABLE=True,
    )
    def test_cms_collaborate_configured(self):
        configuration_step = CMSCollaborateConfigurationStep()

        configuration_step.configure()

        self.assertTrue(configuration_step.is_configured())

        self.assertTrue(collaborate_page_is_published())

        # check common extension
        page = Page.objects.get(publisher_is_draft=False)
        self.assertIsNone(getattr(page, "commonextension", None))

    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
        CMS_CONFIG_COLLABORATE_ENABLE=True,
        CMS_COLLABORATE_REQUIRES_AUTH=True,
        CMS_COLLABORATE_REQUIRES_AUTH_BSN_OR_KVK=True,
        CMS_COLLABORATE_MENU_INDICATOR="arrow",
        CMS_COLLABORATE_MENU_ICON="smiley",
    )
    def test_cms_collaborate_override_settings(self):
        configuration_step = CMSCollaborateConfigurationStep()

        configuration_step.configure()

        self.assertTrue(configuration_step.is_configured())

        self.assertTrue(collaborate_page_is_published())

        # check common extension
        page = Page.objects.get(publisher_is_draft=False)
        extension = page.commonextension

        self.assertTrue(extension.requires_auth)
        self.assertTrue(extension.requires_auth_bsn_or_kvk)
        self.assertEqual(extension.menu_indicator, "arrow")
        self.assertEqual(extension.menu_icon, "smiley")

    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
        CMS_CONFIG_INBOX_ENABLE=True,
    )
    def test_cms_inbox_configured(self):
        configuration_step = CMSInboxConfigurationStep()

        configuration_step.configure()

        self.assertTrue(configuration_step.is_configured())

        self.assertTrue(inbox_page_is_published())

        # check common extension
        page = Page.objects.get(publisher_is_draft=False)
        self.assertIsNone(getattr(page, "commonextension", None))

    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
        CMS_CONFIG_INBOX_ENABLE=True,
        CMS_INBOX_REQUIRES_AUTH=True,
        CMS_INBOX_REQUIRES_AUTH_BSN_OR_KVK=True,
        CMS_INBOX_MENU_INDICATOR="arrow",
        CMS_INBOX_MENU_ICON="smiley",
    )
    def test_cms_inbox_override_settings(self):
        configuration_step = CMSInboxConfigurationStep()

        configuration_step.configure()

        self.assertTrue(configuration_step.is_configured())

        self.assertTrue(inbox_page_is_published())

        # check common extension
        page = Page.objects.get(publisher_is_draft=False)
        extension = page.commonextension

        self.assertTrue(extension.requires_auth)
        self.assertTrue(extension.requires_auth_bsn_or_kvk)
        self.assertEqual(extension.menu_indicator, "arrow")
        self.assertEqual(extension.menu_icon, "smiley")

    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
        CMS_CONFIG_PRODUCTS_ENABLE=True,
    )
    def test_cms_products_configured(self):
        configuration_step = CMSProductsConfigurationStep()

        configuration_step.configure()

        self.assertTrue(configuration_step.is_configured())

        self.assertTrue(products_page_is_published())

        # check common extension
        page = Page.objects.get(publisher_is_draft=False)
        self.assertIsNone(getattr(page, "commonextension", None))

    @override_settings(
        ROOT_URLCONF="open_inwoner.cms.tests.urls",
        CMS_CONFIG_PRODUCTS_ENABLE=True,
        CMS_PRODUCTS_REQUIRES_AUTH=True,
        CMS_PRODUCTS_REQUIRES_AUTH_BSN_OR_KVK=True,
        CMS_PRODUCTS_MENU_INDICATOR="arrow",
        CMS_PRODUCTS_MENU_ICON="smiley",
    )
    def test_cms_products_override_settings(self):
        configuration_step = CMSProductsConfigurationStep()

        configuration_step.configure()

        self.assertTrue(configuration_step.is_configured())

        self.assertTrue(products_page_is_published())

        # check common extension
        page = Page.objects.get(publisher_is_draft=False)
        extension = page.commonextension

        self.assertTrue(extension.requires_auth)
        self.assertTrue(extension.requires_auth_bsn_or_kvk)
        self.assertEqual(extension.menu_indicator, "arrow")
        self.assertEqual(extension.menu_icon, "smiley")
