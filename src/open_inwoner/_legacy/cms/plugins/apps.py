from django.apps import AppConfig


class LegacyPluginsConfig(AppConfig):
    """
    Legacy 'plugins' app configuration - migrations only.

    This app originally contained all CMS plugin models but has been refactored.
    All models have been migrated to individual plugin apps or the profile app:
    - VideoPlayer → videoplayer_plugin
    - UserFeed → userfeed_plugin
    - TextPluginConfig → text_plugin
    - CMSLinkPluginConfig, ExtendedCMSLink → link_plugin
    - UserAppointments → profile (accounts.cms.mijn_profiel)
    - TasksPluginConfig, ZakenPluginConfig → mijn_aanvragen_cms

    This app is kept only to maintain migration history and dependencies.
    """

    name = "open_inwoner._legacy.cms.plugins"
    label = "plugins"  # Must preserve original label for migration history
    verbose_name = "Legacy CMS Plugins (migrations only)"
