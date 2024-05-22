====================
Setup configurations
====================

OIP supports automating the configuration of (parts of) the platform via the management command ``setup_configuration``. The command uses environment variables to configure OIP and (by default) automatically tests the configuration to detect problems.


Defining variables
==================

Variables can be defined by creating a ``.env`` file in the root directory of the project (on the same level as the ``src`` directory, not inside it) and setting the relevant variables as documented in the sections below, replacing the example values with values of your choice. Alternatively, you can use a process manager like supervisor or systemd. For example, both of the following:

::

    # .env
    SITE_WARNING_BANNER_ENABLED=True
    SITE_NAME="My site"

    # systemd config file
    [Service]
    Environment="SITE_WARNING_BANNER_ENABLED=True"
    Environment="SITE_NAME=My site"

will enable the warning banner and define the name of the site as "My site". Note that the variables are namespaced: ``SITE_FOO=BAR`` for variables concerning the general configuration, ``ZGW_BAR=BAZ`` for variables concerning the configuration of ZGW, and so on. For an overview of the features that support automatic configuration and the relevant environment variables, see ``Supported configurations`` below.


Usage
=====

If the project is being configured for the first time, run the command from the project root:

::

    src/manage.py setup_configuration

By default, ``setup_configuration`` checks per configuration step if it is already configured and skips this step if that is the case. In order to overwrite an existing configuration, use:

::

    src/manage.py setup_configuration --overwrite


Also by default, ``setup_configuration`` tests the configuration to detect problems. You can disable this with the following:

::

    src/manage.py setup_configuration --no-selftest


For a full overview of the command and its options:

::

    src/manage.py setup_configuration --help



Supported configurations
========================

`General configuration <./siteconfig.rst>`_

`Klanten configuration <./kic.rst>`_

`ZGW configuration <./zgw.rst>`_

`Admin OIDC configuration <./admin_oidc.rst>`_

`DigiD OIDC configuration <./digid_oidc.rst>`_

`DigiD SAML configuration <./digid_saml.rst>`_

`eHerkenning OIDC configuration <./eherkenning_oidc.rst>`_

`eHerkenning SAML configuration <./eherkenning_saml.rst>`_


.. toctree::
   :maxdepth: 1
   :caption: Further reading

   admin_oidc
   digid_oidc
   digid_saml
   eherkenning_oidc
   eherkenning_saml
   kic
   siteconfig
   zgw
