SETUP_CONFIGURATION_STEPS = [
    "mozilla_django_oidc_db.setup_configuration.steps.AdminOIDCConfigurationStep",
    # depends on the OIDC step above: SiteConfiguration.openid_display validates
    # against the admin OIDC client configuration during full_clean()
    "open_inwoner.configurations.bootstrap.siteconfig.SiteConfigurationStep",
    "open_inwoner.configurations.bootstrap.saml.DigiDSAMLConfigurationStep",
    "open_inwoner.configurations.bootstrap.saml.eHerkenningSAMLConfigurationStep",
    "zgw_consumers.contrib.setup_configuration.steps.ServiceConfigurationStep",
    "open_inwoner.configurations.bootstrap.zgw.OpenZaakConfigurationStep",
    "open_inwoner.configurations.bootstrap.openklant.KlantenSysteemConfigurationStep",
    "open_inwoner.configurations.bootstrap.default_users.UserConfigurationStep",
    "django_setup_configuration.contrib.sites.steps.SitesConfigurationStep",
    "open_inwoner.configurations.bootstrap.cms.CMSPagesConfigurationStep",
]
