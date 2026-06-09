from typing import Annotated

from django.utils.functional import SimpleLazyObject

from cms.app_base import CMSApp
from cms.models import Page
from cms.plugin_base import CMSPluginBase
from django_setup_configuration import ConfigurationModel
from django_setup_configuration.configuration import BaseConfigurationStep
from pydantic import Field

from open_inwoner.cms.benefits.cms_apps import SSDApphook
from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.collaborate.cms_apps import CollaborateApphook
from open_inwoner.cms.extensions.models import CommonExtension
from open_inwoner.cms.inbox.cms_apps import InboxApphook
from open_inwoner.cms.plugins.cms_plugins.tasks import TasksPlugin
from open_inwoner.cms.plugins.cms_plugins.zaken import CMSZakenPlugin
from open_inwoner.cms.plugins.models.tasks import TasksConfig
from open_inwoner.cms.plugins.models.zaken import CMSZakenPluginConfig
from open_inwoner.cms.products.cms_apps import ProductsApphook
from open_inwoner.cms.profile.cms_appconfig import ProfileConfig
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.utils import page_setup
from open_inwoner.mijn_afval.cms.cms_apps import MijnAfvalApphook
from open_inwoner.openklant.cms_apps import OpenklantApphook


class ZakenPluginConfig(ConfigurationModel):
    """Configuration for the 'Mijn zaken' plugin placed on the homepage."""

    class Meta:
        django_model_refs = {CMSZakenPluginConfig: ["title", "num_zaken"]}


class TasksPluginConfig(ConfigurationModel):
    """Configuration for the 'Mijn taken' plugin placed on the homepage."""

    class Meta:
        django_model_refs = {TasksConfig: ["title"]}


class CMSHomepageConfig(ConfigurationModel):
    """Configuration for the site homepage (a plain CMS page with no apphook)."""

    enabled: bool = False
    title: Annotated[str, Field(description="Page title for the homepage.")] = "Home"
    mijn_zaken: Annotated[
        ZakenPluginConfig | None,
        Field(description="Adds a 'Mijn zaken' plugin to the homepage."),
    ] = Field(default=None)
    mijn_taken: Annotated[
        TasksPluginConfig | None,
        Field(description="Adds a 'Mijn taken' plugin to the homepage."),
    ] = Field(default=None)


class CMSPageConfig(ConfigurationModel):
    """Configuration for a single CMS apphook-backed page."""

    enabled: bool = False
    title: Annotated[
        str | None,
        Field(
            description=(
                "Page title shown in navigation and the browser tab. "
                "Defaults to the apphook's built-in name when not set."
            )
        ),
    ] = None

    class Meta:
        django_model_refs = {
            CommonExtension: [
                "requires_auth",
                "requires_auth_bsn_or_kvk",
                "menu_indicator",
                "menu_icon",
            ]
        }


class CMSProfilePageConfig(CMSPageConfig):
    """Configuration for the Profile page; extends CMSPageConfig with section toggles."""

    class Meta:
        django_model_refs = {
            ProfileConfig: [
                "my_data",
                "selected_categories",
                "mentors",
                "my_contacts",
                "selfdiagnose",
                "actions",
                "notifications",
                "questions",
                "ssd",
                "newsletters",
                "appointments",
            ]
        }


class CMSPagesConfigurationModel(ConfigurationModel):
    """
    Groups per-page configuration for the homepage and every CMS apphook page.

    Omitting a page is the same as disabling it, hence the ``None`` defaults. A
    model instance as default would be more direct, but the documentation
    generator serializes field defaults to JSON and cannot handle those.
    """

    homepage: CMSHomepageConfig | None = Field(default=None)
    ssd: CMSPageConfig | None = Field(default=None)
    cases: CMSPageConfig | None = Field(default=None)
    collaborate: CMSPageConfig | None = Field(default=None)
    inbox: CMSPageConfig | None = Field(default=None)
    products: CMSPageConfig | None = Field(default=None)
    profile: CMSProfilePageConfig | None = Field(default=None)
    openklant: CMSPageConfig | None = Field(default=None)
    mijn_afval: CMSPageConfig | None = Field(default=None)


# maps the field name on CMSPagesConfigurationModel to the apphook it configures
# (the ordering determines the order of the pages in the navigation)
_APP_HOOKS: dict[str, type[CMSApp]] = {
    "ssd": SSDApphook,
    "cases": CasesApphook,
    "collaborate": CollaborateApphook,
    "inbox": InboxApphook,
    "products": ProductsApphook,
    "profile": ProfileApphook,
    "openklant": OpenklantApphook,
    "mijn_afval": MijnAfvalApphook,
}

# the ProfileConfig fields, i.e. everything CMSProfilePageConfig adds on top of
# the common page configuration
_PROFILE_CONFIG_FIELDS = tuple(
    name
    for name in CMSProfilePageConfig.model_fields
    if name not in CMSPageConfig.model_fields
)

# maps a CMSHomepageConfig field name to the plugin it configures on the
# homepage's "content" placeholder (the ordering determines the order the
# plugins are placed in)
_HOMEPAGE_PLUGINS: dict[str, type[CMSPluginBase]] = {
    "mijn_zaken": CMSZakenPlugin,
    "mijn_taken": TasksPlugin,
}
_HOMEPAGE_CONTENT_SLOT = "content"


class CMSPagesConfigurationStep(BaseConfigurationStep):
    """
    Creates or updates the site homepage and every individually enabled CMS
    apphook page.

    The step reads nested configuration from ``CMSPagesConfigurationModel``.
    Each sub-model carries an ``enabled`` flag; entries whose flag is ``False``
    (the default) are skipped so deployments only create the pages they need.

    A page that already exists is not left untouched: its title, common
    extension settings (``requires_auth`` and friends) and, for the profile
    page, its section toggles are all overwritten to match this configuration
    on every run, so changes made to them in the CMS admin do not survive a
    re-run. The homepage's ``mijn_zaken``/``mijn_taken`` plugins, if
    configured, are overwritten the same way. Anything else on a page --
    placeholders, plugins this step doesn't explicitly manage -- is left
    alone.
    """

    verbose_name = "Configuration for CMS pages"
    enable_setting = "cms_pages_config_enable"
    namespace = "cms_pages_config"
    config_model = CMSPagesConfigurationModel

    def execute(self, model: CMSPagesConfigurationModel) -> None:
        # resolved on first use, so a run with nothing left to create does not
        # add the service account to the user table
        user = SimpleLazyObject(page_setup.get_cms_bootstrap_user)
        homepage = self._get_or_create_homepage(model.homepage, user=user)

        if homepage is not None:
            self._sync_homepage_plugins(homepage, model.homepage, user=user)

        for model_attr, apphook in _APP_HOOKS.items():
            page_config: CMSPageConfig | None = getattr(model, model_attr)
            if page_config is None or not page_config.enabled:
                continue

            extension_args = {
                "requires_auth": page_config.requires_auth,
                "requires_auth_bsn_or_kvk": page_config.requires_auth_bsn_or_kvk,
                "menu_indicator": page_config.menu_indicator,
                "menu_icon": page_config.menu_icon,
            }

            config_args = (
                {field: getattr(page_config, field) for field in _PROFILE_CONFIG_FIELDS}
                if isinstance(page_config, CMSProfilePageConfig)
                else None
            )

            page_setup.get_or_create_apphook_page(
                apphook,
                user=user,
                title=page_config.title,
                extension_args=extension_args,
                config_args=config_args,
                parent_page=homepage,
            )

    def _get_or_create_homepage(
        self, config: CMSHomepageConfig | None, *, user
    ) -> Page | None:
        """
        Return the homepage that apphook pages are nested under.

        Creates or updates it when a config is provided and enabled. If a
        homepage already exists but this run doesn't enable one, it is
        returned as-is (not overwritten), so disabling the homepage doesn't
        detach the apphook pages from the page tree. Returns ``None`` only
        if there is no homepage and none was requested.
        """
        if config is not None and config.enabled:
            return page_setup.get_or_create_homepage(user=user, title=config.title)

        return Page.objects.filter(reverse_id=page_setup.HOMEPAGE_REVERSE_ID).first()

    def _sync_homepage_plugins(
        self, homepage: Page, config: CMSHomepageConfig | None, *, user
    ) -> None:
        """
        Add or update the plugins configured for the homepage.

        A plugin field left out of the configuration is not removed if it
        was previously added: like everything else this step doesn't
        explicitly manage, it is left as-is for admins to change.
        """
        plugin_specs = []
        if config is not None:
            for model_attr, plugin_class in _HOMEPAGE_PLUGINS.items():
                plugin_config = getattr(config, model_attr)
                if plugin_config is not None:
                    plugin_specs.append((plugin_class, plugin_config.model_dump()))

        page_setup.sync_placeholder_plugins(
            homepage, _HOMEPAGE_CONTENT_SLOT, plugin_specs, user=user
        )
