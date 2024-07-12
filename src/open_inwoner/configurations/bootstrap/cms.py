from django.conf import settings

from django_setup_configuration.config_settings import ConfigSettings
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

        Pattern for enable setting: CMS_CONFIG_APPNAME_ENABLE
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
        extension_args = create_apphook_page_args(
            self.config_settings.extension_settings_mapping
        )

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


class CMSConfigSettings(ConfigSettings):
    """
    Configuration settings + documentation common to most CMS apps

    The `namespace` attribute should be of the form:
        CMS_APPNAME
    where APPNAME is the name of the cms app in upper case
    """

    def __init__(
        self,
        namespace: str,
        enable_setting: str,
        required_settings: list | None = None,
        optional_settings: list | None = None,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            namespace=namespace,
            enable_setting=enable_setting,
            required_settings=required_settings,
            optional_settings=optional_settings,
            **kwargs,
        )

        self.enable_setting = enable_setting
        self.namespace = namespace
        self.file_name = f"{self.namespace.lower()}"
        self.required_settings = required_settings or []
        self.optional_settings = optional_settings or [
            f"{self.namespace}_REQUIRES_AUTH",
            f"{self.namespace}_REQUIRES_AUTH_BSN_OR_KVK",
            f"{self.namespace}_MENU_INDICATOR",
            f"{self.namespace}_MENU_ICON",
        ]
        self.extension_settings_mapping = {
            f"{self.namespace}_REQUIRES_AUTH": "requires_auth",
            f"{self.namespace}_REQUIRES_AUTH_BSN_OR_KVK": "requires_auth_bsn_or_kvk",
            f"{self.namespace}_MENU_INDICATOR": "menu_indicator",
            f"{self.namespace}_MENU_ICON": "menu_icon",
        }
        self.additional_info = {
            "requires_auth": {
                "variable": f"{self.namespace}_REQUIRES_AUTH",
                "description": "Whether the access to the page is restricted",
                "possible_values": "True, False",
            },
            "requires_auth_bsn_or_kvk": {
                "variable": f"{self.namespace}_REQUIRES_AUTH_BSN_OR_KVK",
                "description": "Access to the page requires BSN or KVK",
                "possible_values": "True, False",
            },
            "menu_indicator": {
                "variable": f"{self.namespace}_MENU_INDICATOR",
                "description": "Menu indicator for the app",
                "possible_values": "String",
            },
            "menu_icon": {
                "variable": f"{self.namespace}_MENU_ICON",
                "description": "Icon in the menu",
                "possible_values": "String",
            },
        }


class CMSBenefitsConfigurationStep(GenericCMSConfigurationStep):
    verbose_name = "Configuration for CMS social benefits (SSD) app"
    config_settings = CMSConfigSettings(
        enable_setting="CMS_CONFIG_BENEFITS_ENABLE",
        namespace="CMS_SSD",
        display_name="CMS apps configuration: Social Benefits",
    )

    def __init__(self):
        self.app_name = "ssd"
        self.app_hook = SSDApphook


class CMSCasesConfigurationStep(GenericCMSConfigurationStep):
    verbose_name = "Configuration for CMS cases app"
    config_settings = CMSConfigSettings(
        enable_setting="CMS_CONFIG_CASES_ENABLE",
        namespace="CMS_CASES",
        display_name="CMS apps configuration: Cases",
    )

    def __init__(self):
        self.app_name = "cases"
        self.app_hook = CasesApphook


class CMSCollaborateConfigurationStep(GenericCMSConfigurationStep):
    verbose_name = "Configuration for CMS collaborate app"
    config_settings = CMSConfigSettings(
        enable_setting="CMS_CONFIG_COLLABORATE_ENABLE",
        display_name="CMS apps configuration: Collaboration",
        namespace="CMS_COLLABORATE",
    )

    def __init__(self):
        self.app_name = "collaborate"
        self.app_hook = CollaborateApphook


class CMSInboxConfigurationStep(GenericCMSConfigurationStep):
    verbose_name = "Configuration for CMS inbox app"
    config_settings = CMSConfigSettings(
        enable_setting="CMS_CONFIG_INBOX_ENABLE",
        display_name="CMS apps configuration: Inbox",
        namespace="CMS_INBOX",
    )

    def __init__(self):
        self.app_name = "inbox"
        self.app_hook = InboxApphook


class CMSProductsConfigurationStep(GenericCMSConfigurationStep):
    verbose_name = "Configuration for CMS product app"
    config_settings = CMSConfigSettings(
        enable_setting="CMS_CONFIG_PRODUCTS_ENABLE",
        display_name="CMS apps configuration: Products",
        namespace="CMS_PRODUCTS",
    )

    def __init__(self):
        self.app_name = "products"
        self.app_hook = ProductsApphook


class CMSProfileConfigurationStep(GenericCMSConfigurationStep):
    verbose_name = "Configuration for CMS profile app"
    config_settings = CMSConfigSettings(
        enable_setting="CMS_CONFIG_PROFILE_ENABLE",
        display_name="CMS apps configuration: Profile",
        namespace="CMS_PROFILE",
        optional_settings=[
            # commonextension
            "CMS_PROFILE_REQUIRES_AUTH",
            "CMS_PROFILE_REQUIRES_AUTH_BSN_OR_KVK",
            "CMS_PROFILE_MENU_INDICATOR",
            "CMS_PROFILE_MENU_ICON",
            # custom
            "CMS_PROFILE_MY_DATA",
            "CMS_PROFILE_SELECTED_CATEGORIES",
            "CMS_PROFILE_MENTORS",
            "CMS_PROFILE_MY_CONTACTS",
            "CMS_PROFILE_SELFDIAGNOSE",
            "CMS_PROFILE_ACTIONS",
            "CMS_PROFILE_NOTIFICATIONS",
            "CMS_PROFILE_QUESTIONS",
            "CMS_PROFILE_SSD",
            "CMS_PROFILE_NEWSLETTERS",
            "CMS_PROFILE_APPOINTMENTS",
        ],
        detailed_info_extra={
            "requires_auth": {
                "variable": "CMS_PROFILE_REQUIRES_AUTH",
                "description": "Whether the access to the page is restricted",
                "possible_values": "True, False",
            },
            "requires_auth_bsn_or_kvk": {
                "variable": "CMS_PROFILE_REQUIRES_AUTH_BSN_OR_KVK",
                "description": "Access to the page requires BSN or KVK",
                "possible_values": "True, False",
            },
            "menu_indicator": {
                "variable": "CMS_PROFILE_MENU_INDICATOR",
                "description": "Menu indicator for the app",
                "possible_values": "String",
            },
            "menu_icon": {
                "variable": "CMS_PROFILE_MENU_ICON",
                "description": "Icon in the menu",
                "possible_values": "String",
            },
        },
    )

    def __init__(self):
        self.app_name = "profile"

    def configure(self):
        extension_settings = [
            "CMS_PROFILE_REQUIRES_AUTH",
            "CMS_PROFILE_REQUIRES_AUTH_BSN_OR_KVK",
            "CMS_PROFILE_MENU_INDICATOR",
            "CMS_PROFILE_MENU_ICON",
        ]
        optional_settings = [
            item
            for item in self.config_settings.optional_settings
            if item not in extension_settings
        ]
        config_mapping = {
            setting: f"{setting.split('CMS_PROFILE_', 1)[1].lower()}"
            for setting in optional_settings
        }

        config_args = create_apphook_page_args(config_mapping)
        extension_args = create_apphook_page_args(
            self.config_settings.extension_settings_mapping
        )

        if getattr(settings, "CMS_CONFIG_PROFILE_ENABLE", None) is not None:
            cms_tools.create_apphook_page(
                ProfileApphook,
                config_args=config_args,
                extension_args=extension_args,
            )
