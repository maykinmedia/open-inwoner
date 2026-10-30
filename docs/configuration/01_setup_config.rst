.. _configuration_setup_config:

Setup-configuration
===================

.. setup-config-usage::

Example configuration
---------------------

``docker/setup_configuration/data.yaml`` in the repository is a complete,
working example. The Docker Compose development stack uses it to configure
every step except DigiD/eHerkenning SAML against the local services (see
:ref:`installation_docker_compose_full_stack`). Use it as a starting point, but
note that it contains development credentials.

The ``oidc_db_config_admin_auth`` step configures more than the admin login: its
``items`` also hold the OIDC clients for DigiD (``oidc-digid``), eHerkenning
(``oidc-eherkenning``) and eIDAS (``oidc-eidas``). They all share the providers
listed under ``providers``.

Running setup-configuration more than once
------------------------------------------

Setup-configuration can be run again, e.g. after a change to the YAML file.
Steps differ in what happens to values that were changed in the admin in the
meantime:

**Every field is overwritten.** Fields missing from the YAML file are reset to
their default, so changes made in the admin are lost:

* Admin OIDC (``oidc_db_config_admin_auth``), including the DigiD, eHerkenning
  and eIDAS OIDC clients
* Site configuration (``site_config``). Files and CMS page fields are not
  managed by this step.
* DigiD and eHerkenning/eIDAS SAML (``digid_saml_config``,
  ``eherkenning_saml_config``). The certificate is only created once.
* Services (``zgw_consumers``), per service. Certificates are not managed.
* Open Zaak (``openzaak_config``), see below for the API groups
* Klantensysteem (``klantensysteem_config``), per backend (eSuite, OpenKlant2)
  present in the YAML file. If ``subjects`` is given, all contact form
  subjects for that backend are deleted and recreated.
* Objects API (``objects_api_config``) and Mijn Afval (``mijn_afval_config``)
* Sites (``sites_config``)

**Only fields in the YAML file are applied.** Fields missing from the YAML file
keep their current value:

* Haal Centraal (``haalcentraal_config``)
* KvK (``kvk_config``)
* SSD (``ssd_config``)

**Other:**

* SOAP services (``soap_services_config``): only the URL is overwritten.
* Open Zaak API groups are matched on their four services. Their name is
  always reset to "Auto-configured by django-setup-configuration". API groups
  that are not in the YAML file are not deleted.
* Users (``default_user_configuration_config``): ``is_staff`` and
  ``is_superuser`` are overwritten, but the password is only set when the user
  is created.
* CMS pages (``cms_pages_config``): only pages with ``enabled: true`` are
  touched. For existing pages, the title, page settings and configured
  homepage plugins are overwritten; other plugins are left alone.

Nothing is ever deleted, except the contact form subjects mentioned above.
