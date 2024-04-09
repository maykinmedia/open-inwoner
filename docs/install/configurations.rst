====================
Setup configurations
====================

OIP supports automating the configuration of (parts of) the platform via the management command ``setup_configuration``. The command uses environment variables to configure OIP and (by default) automatically tests the configuration to detect problems.


Environment variables
=====================

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


By default, ``setup_configuration`` checks if a configuration already exists and will stop executing if it finds one. In order to overwrite an existing configuration, use:

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

In the following, ``FOO=<value1 | value2 | value3>`` means that only ``FOO=value1``, ``FOO=value2``, and ``FOO=value3`` are admissible.


General configuration
^^^^^^^^^^^^^^^^^^^^^

Required:
"""""""""

::

    SITE_PRIMARY_COLOR
    SITE_SECONDARY_COLOR
    SITE_ACCENT_COLOR
    SITE_PRIMARY_FONT_COLOR


All variables:
""""""""""""""

::

    SITE_CONFIG_ENABLE=True
    SITE_NAME="My site"
    SITE_SECONDARY_COLOR="#000000"
    SITE_ACCENT_COLOR="#000000"
    SITE_PRIMARY_FONT_COLOR="#111111"
    SITE_SECONDARY_FONT_COLOR="#222222"
    SITE_ACCENT_FONT_COLOR="#333333"
    SITE_WARNING_BANNER_ENABLED=<True | False>
    SITE_WARNING_BANNER_TEXT="warning banner text"
    SITE_WARNING_BANNER_BACKGROUND_COLOR="#444444"
    SITE_WARNING_BANNER_FONT_COLOR="#555555"
    SITE_LOGIN_SHOW=False
    SITE_LOGIN_ALLOW_REGISTRATION=<True | False>
    SITE_LOGIN_2FA_SMS=<True | False>
    SITE_LOGIN_TEXT="login text"
    SITE_REGISTRATION_TEXT="registration text"
    SITE_HOME_WELCOME_TITLE="welcome title"
    SITE_HOME_WELCOME_INTRO="welcome intro"
    SITE_HOME_THEME_TITLE="home theme title"
    SITE_HOME_THEME_INTRO="home theme intro"
    SITE_THEME_TITLE="theme title"
    SITE_THEME_INTRO="theme intro"
    SITE_HOME_MAP_TITLE="home map title"
    SITE_HOME_MAP_INTRO="home map intro"
    SITE_HOME_QUESTIONNAIRE_TITLE="home questionnaire title"
    SITE_HOME_QUESTIONNAIRE_INTRO="home questionnaire intro"
    SITE_HOME_PRODUCT_FINDER_TITLE="home product finder title"
    SITE_HOME_PRODUCT_FINDER_INTRO="home product finder intro"
    SITE_SELECT_QUESTIONNAIRE_TITLE="select questionnaire title"
    SITE_SELECT_QUESTIONNAIRE_INTRO="select questionnaire intro"
    SITE_PLANS_INTRO="plans intro"
    SITE_PLANS_NO_PLANS_MESSAGE="plans no plans_message"
    SITE_PLANS_EDIT_MESSAGE="plans edit message"
    SITE_FOOTER_LOGO_TITLE="footer logo title"
    SITE_FOOTER_LOGO_URL="footer logo url"
    SITE_HOME_HELP_TEXT="home help text"
    SITE_THEME_HELP_TEXT="theme help text"
    SITE_PRODUCT_HELP_TEXT="product help text"
    SITE_SEARCH_HELP_TEXT="search help text"
    SITE_ACCOUNT_HELP_TEXT="account help text"
    SITE_QUESTIONNAIRE_HELP_TEXT="questionnaire help text"
    SITE_PLAN_HELP_TEXT="plan help text"
    SITE_SEARCH_FILTER_CATEGORIES=False
    SITE_SEARCH_FILTER_TAGS=False
    SITE_SEARCH_FILTER_ORGANIZATIONS=False
    SITE_EMAIL_NEW_MESSAGE=False
    SITE_RECIPIENTS_EMAIL_DIGEST="foo@test.nl,bar@test.nl,baz@test.nl"
    SITE_CONTACT_PHONENUMBER="12345"
    SITE_CONTACT_PAGE="https://test.test"
    SITE_GTM_CODE="gtm code"
    SITE_GA_CODE="ga code"
    SITE_MATOMO_URL="matomo url"
    SITE_MATOMO_SITE_ID=88
    SITE_SITEIMPROVE_ID="88"
    SITE_COOKIE_INFO_TEXT="cookie info text"
    SITE_COOKIE_LINK_TEXT="cookie link text"
    SITE_COOKIE_LINK_URL="cookie link url"
    SITE_KCM_SURVEY_LINK_TEXT="kcm survey link text"
    SITE_KCM_SURVEY_LINK_URL="kcm survey link url"
    SITE_OPENID_CONNECT_LOGIN_TEXT="openid connect login_text"
    SITE_OPENID_DISPLAY="<admin | regular>"
    SITE_REDIRECT_TO="redirect to"
    SITE_ALLOW_MESSAGES_FILE_SHARING=False
    SITE_HIDE_CATEGORIES_FROM_ANONYMOUS_USERS=True
    SITE_HIDE_SEARCH_FROM_ANONYMOUS_USERS=True
    SITE_DISPLAY_SOCIAL=<True | False>
    SITE_EHERKENNING_ENABLED=<True | False>

Not supported:
""""""""""""""

::

   Logo
   Hero image login
   Footer logo
   Email logo
   Favicon image
   Openid Connect Logo
   Theme stylesheet
   Custom fonts
   Flatpages


Klanten
^^^^^^^

Required:
"""""""""

::

    KIC_CONFIG_KLANTEN_API_ROOT
    KIC_CONFIG_KLANTEN_API_CLIENT_ID
    KIC_CONFIG_KLANTEN_API_SECRET

All variables:
""""""""""""""

::

    OIP_ORGANIZATION="Maykin"
    KIC_CONFIG_KLANTEN_API_ROOT="https://openklant.local/klanten/api/v1/"
    KIC_CONFIG_KLANTEN_API_CLIENT_ID="open-inwoner-test"
    KIC_CONFIG_KLANTEN_API_SECRET="klanten-secret"
    KIC_CONFIG_CONTACTMOMENTEN_API_ROOT="https://openklant.local/contactmomenten/api/v1/"
    KIC_CONFIG_CONTACTMOMENTEN_API_CLIENT_ID="open-inwoner-test"
    KIC_CONFIG_CONTACTMOMENTEN_API_SECRET="contactmomenten-secret"
    KIC_CONFIG_REGISTER_EMAIL="admin@oip.org"
    KIC_CONFIG_REGISTER_CONTACT_MOMENT=<True | False>
    KIC_CONFIG_REGISTER_BRONORGANISATIE_RSIN="837194569"
    KIC_CONFIG_REGISTER_CHANNEL="email"
    KIC_CONFIG_REGISTER_TYPE="bericht"
    KIC_CONFIG_REGISTER_EMPLOYEE_ID="1234"
    KIC_CONFIG_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER=<True | False>


Not supported:
""""""""""""""

::

   Certificates


Zaken
^^^^^

Required:
"""""""""

::

    ZGW_CONFIG_ZAKEN_API_ROOT
    ZGW_CONFIG_ZAKEN_API_CLIENT_ID
    ZGW_CONFIG_ZAKEN_API_SECRET

All variables:
""""""""""""""

::

    OIP_ORGANIZATION="Maykin"
    ZGW_CONFIG_ZAKEN_API_ROOT="https://openzaak.local/zaken/api/v1/"
    ZGW_CONFIG_ZAKEN_API_CLIENT_ID="open-inwoner-test"
    ZGW_CONFIG_ZAKEN_API_SECRET="zaken-secret"
    ZGW_CONFIG_CATALOGI_API_ROOT="https://openzaak.local/catalogi/api/v1/"
    ZGW_CONFIG_CATALOGI_API_CLIENT_ID="open-inwoner-test"
    ZGW_CONFIG_CATALOGI_API_SECRET="catalogi-secret"
    ZGW_CONFIG_DOCUMENTEN_API_ROOT="https://openzaak.local/documenten/api/v1/"
    ZGW_CONFIG_DOCUMENTEN_API_CLIENT_ID="open-inwoner-test"
    ZGW_CONFIG_DOCUMENTEN_API_SECRET="documenten-secret"
    ZGW_CONFIG_FORMULIEREN_API_ROOT="https://esuite.local.net/formulieren-provider/api/v1/"
    ZGW_CONFIG_FORMULIEREN_API_CLIENT_ID="open-inwoner-test"
    ZGW_CONFIG_FORMULIEREN_API_SECRET="forms-secret"
    ZGW_CONFIG_ZAAK_MAX_CONFIDENTIALITY=<"openbaar" | "beperkt_openbaar | "intern" | "zaakvertrouwelijk" | "vertrouwelijk" | "confidentieel" | "geheim" | "zeer_geheim">
    ZGW_CONFIG_DOCUMENT_MAX_CONFIDENTIALITY=<"openbaar" | "beperkt_openbaar | "intern" | "zaakvertrouwelijk" | "vertrouwelijk" | "confidentieel" | "geheim" | "zeer_geheim">
    ZGW_CONFIG_ACTION_REQUIRED_DEADLINE_DAYS=12
    ZGW_CONFIG_ALLOWED_FILE_EXTENSIONS="pdf,doc,docx,xls,xlsx,ppt,pptx,vsd,png,gif,jpg,tiff,msg,txt,rtf,jpeg,bmp"
    ZGW_CONFIG_MIJN_AANVRAGEN_TITLE_TEXT="title text"
    ZGW_CONFIG_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN=<True | False>
    ZGW_CONFIG_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN=<True | False>
    ZGW_CONFIG_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE=<True | False>
    ZGW_CONFIG_FETCH_EHERKENNING_ZAKEN_WITH_RSIN=<True | False>

Not supported:
""""""""""""""

::

   Certificates
