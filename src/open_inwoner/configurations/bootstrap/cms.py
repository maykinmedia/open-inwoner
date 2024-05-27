from django.conf import settings

from django_setup_configuration.configuration import BaseConfigurationStep

from open_inwoner.cms.benefits.cms_apps import SSDApphook
from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.collaborate.cms_apps import CollaborateApphook
from open_inwoner.cms.inbox.cms_apps import InboxApphook
from open_inwoner.cms.products.cms_apps import ProductsApphook
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests import cms_tools


def create_apphook_page_args(config_mapping: dict) -> dict:
    """
    Helper function to create mappings with arguments for :func:`create_apphook_page`
    """

    apphook_page_args = dict()

    for setting_name, config_field_name in config_mapping.items():
        setting = getattr(settings, setting_name, None)
        if setting is not None:
            apphook_page_args[config_field_name] = setting

    return apphook_page_args


class GenericCMSConfigurationStep(BaseConfigurationStep):
    """
    Generic base class for configuring CMS apps
    """

    def is_configured(self):
        """
        CMS apps have no required settings; we consider them "configured"
        if the configuration option is enabled
        """
        return (
            getattr(settings, f"CMS_CONFIG_{self.app_name.upper()}_ENABLE", None)
            is not None
        )

    def configure(self):
        """
        Create apphook page with common extenion settings

        The method is sufficient for generic CMS apps that don't require any
        configuration beyond the commonextension. Override to provide additional
        arguments to :func:`create_apphook_page`.
        """
        extension_args = create_apphook_page_args(self.extension_settings)

        if (
            getattr(settings, f"CMS_CONFIG_{self.app_name.upper()}_ENABLE", None)
            is not None
        ):
            cms_tools.create_apphook_page(
                self.app_hook,
                extension_args=extension_args,
            )

    def test_configuration(self):
        ...


class CMSBenefitsConfigurationStep(GenericCMSConfigurationStep):
    verbose_name = "Configuration for CMS social benefits (SSD) app"
    extension_settings = {
        "CMS_SSD_REQUIRES_AUTH": "requires_auth",
        "CMS_SSD_REQUIRES_AUTH_BSN_OR_KVK": "requires_auth_bsn_or_kvk",
        "CMS_SSD_MENU_INDICATOR": "menu_indicator",
        "CMS_SSD_MENU_ICON": "menu_icon",
    }

    def __init__(self):
        self.app_name = "ssd"
        self.app_hook = SSDApphook


class CMSCasesConfigurationStep(GenericCMSConfigurationStep):
    verbose_name = "Configuration for CMS cases app"
    extension_settings = {
        "CMS_CASES_REQUIRES_AUTH": "requires_auth",
        "CMS_CASES_REQUIRES_AUTH_BSN_OR_KVK": "requires_auth_bsn_or_kvk",
        "CMS_CASES_MENU_INDICATOR": "menu_indicator",
        "CMS_CASES_MENU_ICON": "menu_icon",
    }

    def __init__(self):
        self.app_name = "cases"
        self.app_hook = CasesApphook


class CMSCollaborateConfigurationStep(GenericCMSConfigurationStep):
    verbose_name = "Configuration for CMS collaborate app"
    extension_settings = {
        "CMS_COLLABORATE_REQUIRES_AUTH": "requires_auth",
        "CMS_COLLABORATE_REQUIRES_AUTH_BSN_OR_KVK": "requires_auth_bsn_or_kvk",
        "CMS_COLLABORATE_MENU_INDICATOR": "menu_indicator",
        "CMS_COLLABORATE_MENU_ICON": "menu_icon",
    }

    def __init__(self):
        self.app_name = "collaborate"
        self.app_hook = CollaborateApphook


class CMSInboxConfigurationStep(GenericCMSConfigurationStep):
    verbose_name = "Configuration for CMS inbox app"
    extension_settings = {
        "CMS_INBOX_REQUIRES_AUTH": "requires_auth",
        "CMS_INBOX_REQUIRES_AUTH_BSN_OR_KVK": "requires_auth_bsn_or_kvk",
        "CMS_INBOX_MENU_INDICATOR": "menu_indicator",
        "CMS_INBOX_MENU_ICON": "menu_icon",
    }

    def __init__(self):
        self.app_name = "inbox"
        self.app_hook = InboxApphook


class CMSProductsConfigurationStep(GenericCMSConfigurationStep):
    verbose_name = "Configuration for CMS product app"
    extension_settings = {
        "CMS_PRODUCTS_REQUIRES_AUTH": "requires_auth",
        "CMS_PRODUCTS_REQUIRES_AUTH_BSN_OR_KVK": "requires_auth_bsn_or_kvk",
        "CMS_PRODUCTS_MENU_INDICATOR": "menu_indicator",
        "CMS_PRODUCTS_MENU_ICON": "menu_icon",
    }

    def __init__(self):
        self.app_name = "products"
        self.app_hook = ProductsApphook


class CMSProfileConfigurationStep(GenericCMSConfigurationStep):
    verbose_name = "Configuration for CMS profile app"
    config_settings = {
        "CMS_PROFILE_MY_DATA": "my_data",
        "CMS_PROFILE_SELECTED_CATEGORIES": "selected_categories",
        "CMS_PROFILE_MENTORS": "mentors",
        "CMS_PROFILE_MY_CONTACTS": "my_contacts",
        "CMS_PROFILE_SELFDIAGNOSE": "selfdiagnose",
        "CMS_PROFILE_ACTIONS": "actions",
        "CMS_PROFILE_NOTIFICATIONS": "notifications",
        "CMS_PROFILE_QUESTIONS": "questions",
        "CMS_PROFILE_SSD": "ssd",
        "CMS_PROFILE_NEWSLETTERS": "newsletters",
        "CMS_PROFILE_APPOINTMENTS": "appointments",
    }
    extension_settings = {
        "CMS_PROFILE_REQUIRES_AUTH": "requires_auth",
        "CMS_PROFILE_REQUIRES_AUTH_BSN_OR_KVK": "requires_auth_bsn_or_kvk",
        "CMS_PROFILE_MENU_INDICATOR": "menu_indicator",
        "CMS_PROFILE_MENU_ICON": "menu_icon",
    }

    def __init__(self):
        self.app_name = "profile"

    def configure(self):
        config_args = create_apphook_page_args(self.config_settings)
        extension_args = create_apphook_page_args(self.extension_settings)

        if getattr(settings, "CMS_CONFIG_PROFILE_ENABLE", None) is not None:
            cms_tools.create_apphook_page(
                ProfileApphook,
                config_args=config_args,
                extension_args=extension_args,
            )
