from maykin_common.config import DocumentationParams, config

SETUP_CONFIGURATION_STEPS = [
    "mozilla_django_oidc_db.setup_configuration.steps.AdminOIDCConfigurationStep",
    "zgw_consumers.contrib.setup_configuration.steps.ServiceConfigurationStep",
    "open_inwoner.configurations.bootstrap.zgw.OpenZaakConfigurationStep",
    "open_inwoner.configurations.bootstrap.openklant.KlantenSysteemConfigurationStep",
    "open_inwoner.configurations.bootstrap.default_users.UserConfigurationStep",
    "django_setup_configuration.contrib.sites.steps.SitesConfigurationStep",
]
OIP_ORGANIZATION = config(
    "OIP_ORGANIZATION",
    default="",
    documentation=DocumentationParams(
        help_text="Name of the municipality or organisation operating this Open Inwoner installation.",
        group="Setup-configuration",
    ),
)

# ZGW configuration variables
ZGW_CONFIG_ENABLE = config(
    "ZGW_CONFIG_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable automatic ZGW API service configuration via setup-configuration.",
        group="Setup-configuration",
    ),
)
ZGW_SERVER_CERTIFICATE_LABEL = config(
    "ZGW_SERVER_CERTIFICATE_LABEL",
    default="",
    documentation=DocumentationParams(
        help_text="Label used to identify the TLS client certificate for ZGW services in the certificate store.",
        group="Setup-configuration",
    ),
)
ZGW_SERVER_CERTIFICATE_TYPE = config(
    "ZGW_SERVER_CERTIFICATE_TYPE",
    default="",
    documentation=DocumentationParams(
        help_text="Certificate store type for ZGW services. Use 'certificate-only' or 'key-pair'.",
        group="Setup-configuration",
    ),
)
ZGW_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE = (
    "ZGW_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE",
    None,
)
ZGW_ZAAK_SERVICE_API_ROOT = config(
    "ZGW_ZAAK_SERVICE_API_ROOT",
    default="",
    documentation=DocumentationParams(
        help_text="Root URL of the Zaken API. Must end with a trailing slash.",
        group="Setup-configuration",
    ),
)
if ZGW_ZAAK_SERVICE_API_ROOT and not ZGW_ZAAK_SERVICE_API_ROOT.endswith("/"):
    ZGW_ZAAK_SERVICE_API_ROOT = f"{ZGW_ZAAK_SERVICE_API_ROOT.strip()}/"
ZGW_ZAKEN_OAS_URL = ZGW_ZAAK_SERVICE_API_ROOT  # this is still required by the form, but not actually used
ZGW_ZAAK_SERVICE_API_CLIENT_ID = config(
    "ZGW_ZAAK_SERVICE_API_CLIENT_ID",
    default="",
    documentation=DocumentationParams(
        help_text="Client ID for JWT authentication with the Zaken API.",
        group="Setup-configuration",
    ),
)
ZGW_ZAAK_SERVICE_API_SECRET = config(
    "ZGW_ZAAK_SERVICE_API_SECRET",
    default="",
    documentation=DocumentationParams(
        help_text="Secret for JWT authentication with the Zaken API.",
        group="Setup-configuration",
    ),
)
ZGW_CATALOGI_SERVICE_API_ROOT = config(
    "ZGW_CATALOGI_SERVICE_API_ROOT",
    default="",
    documentation=DocumentationParams(
        help_text="Root URL of the Catalogi API. Must end with a trailing slash.",
        group="Setup-configuration",
    ),
)
if ZGW_CATALOGI_SERVICE_API_ROOT and not ZGW_CATALOGI_SERVICE_API_ROOT.endswith("/"):
    ZGW_CATALOGI_SERVICE_API_ROOT = f"{ZGW_CATALOGI_SERVICE_API_ROOT.strip()}/"
ZGW_CATALOGI_OAS_URL = ZGW_CATALOGI_SERVICE_API_ROOT  # this is still required by the form, but not actually used
ZGW_CATALOGI_SERVICE_API_CLIENT_ID = config(
    "ZGW_CATALOGI_SERVICE_API_CLIENT_ID",
    default="",
    documentation=DocumentationParams(
        help_text="Client ID for JWT authentication with the Catalogi API.",
        group="Setup-configuration",
    ),
)
ZGW_CATALOGI_SERVICE_API_SECRET = config(
    "ZGW_CATALOGI_SERVICE_API_SECRET",
    default="",
    documentation=DocumentationParams(
        help_text="Secret for JWT authentication with the Catalogi API.",
        group="Setup-configuration",
    ),
)
ZGW_DOCUMENTEN_SERVICE_API_ROOT = config(
    "ZGW_DOCUMENTEN_SERVICE_API_ROOT",
    default="",
    documentation=DocumentationParams(
        help_text="Root URL of the Documenten API. Must end with a trailing slash.",
        group="Setup-configuration",
    ),
)
if ZGW_DOCUMENTEN_SERVICE_API_ROOT and not ZGW_DOCUMENTEN_SERVICE_API_ROOT.endswith(
    "/"
):
    ZGW_DOCUMENTEN_SERVICE_API_ROOT = f"{ZGW_DOCUMENTEN_SERVICE_API_ROOT.strip()}/"
ZGW_DOCUMENTEN_OAS_URL = ZGW_DOCUMENTEN_SERVICE_API_ROOT  # this is still required by the form, but not actually used
ZGW_DOCUMENTEN_SERVICE_API_CLIENT_ID = config(
    "ZGW_DOCUMENTEN_SERVICE_API_CLIENT_ID",
    default="",
    documentation=DocumentationParams(
        help_text="Client ID for JWT authentication with the Documenten API.",
        group="Setup-configuration",
    ),
)
ZGW_DOCUMENTEN_SERVICE_API_SECRET = config(
    "ZGW_DOCUMENTEN_SERVICE_API_SECRET",
    default="",
    documentation=DocumentationParams(
        help_text="Secret for JWT authentication with the Documenten API.",
        group="Setup-configuration",
    ),
)
ZGW_FORM_SERVICE_API_ROOT = config(
    "ZGW_FORM_SERVICE_API_ROOT",
    default="",
    documentation=DocumentationParams(
        help_text="Root URL of the Formulieren API. Must end with a trailing slash.",
        group="Setup-configuration",
    ),
)
if ZGW_FORM_SERVICE_API_ROOT and not ZGW_FORM_SERVICE_API_ROOT.endswith("/"):
    ZGW_FORM_SERVICE_API_ROOT = f"{ZGW_FORM_SERVICE_API_ROOT.strip()}/"
ZGW_FORMULIEREN_OAS_URL = ZGW_FORM_SERVICE_API_ROOT  # this is still required by the form, but not actually used
ZGW_FORM_SERVICE_API_CLIENT_ID = config(
    "ZGW_FORM_SERVICE_API_CLIENT_ID",
    default="",
    documentation=DocumentationParams(
        help_text="Client ID for JWT authentication with the Formulieren API.",
        group="Setup-configuration",
    ),
)
ZGW_FORM_SERVICE_API_SECRET = config(
    "ZGW_FORM_SERVICE_API_SECRET",
    default="",
    documentation=DocumentationParams(
        help_text="Secret for JWT authentication with the Formulieren API.",
        group="Setup-configuration",
    ),
)
# ZGW config options
ZGW_ZAAK_MAX_CONFIDENTIALITY = config(
    "ZGW_ZAAK_MAX_CONFIDENTIALITY",
    default=None,
    documentation=DocumentationParams(
        help_text="Maximum vertrouwelijkheidaanduiding for zaken shown to citizens. Zaken above this level are hidden.",
        group="Setup-configuration",
    ),
)
ZGW_DOCUMENT_MAX_CONFIDENTIALITY = config(
    "ZGW_DOCUMENT_MAX_CONFIDENTIALITY",
    default=None,
    documentation=DocumentationParams(
        help_text="Maximum vertrouwelijkheidaanduiding for documents shown to citizens. Documents above this level are hidden.",
        group="Setup-configuration",
    ),
)
ZGW_ACTION_REQUIRED_DEADLINE_DAYS = config(
    "ACTION_REQUIRED_DEADLINE_DAYS",
    default=None,
    documentation=DocumentationParams(
        help_text="Default number of days from today used as the deadline for required actions on a zaak.",
        group="Setup-configuration",
    ),
)
ZGW_ALLOWED_FILE_EXTENSIONS = config(
    "ZGW_ALLOWED_FILE_EXTENSIONS",
    default=None,
    documentation=DocumentationParams(
        help_text="Comma-separated list of allowed file extensions for document uploads via ZGW.",
        group="Setup-configuration",
    ),
)
ZGW_MIJN_AANVRAGEN_TITLE_TEXT = config(
    "ZGW_MIJN_AANVRAGEN_TITLE_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Custom heading shown at the top of the Mijn Aanvragen page.",
        group="Setup-configuration",
    ),
)
ZGW_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN = config(
    "ZGW_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN",
    default=None,
    documentation=DocumentationParams(
        help_text="Filter the PDC category list to only show categories linked to the user's zaaktypen.",
        group="Setup-configuration",
    ),
)
ZGW_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN = config(
    "ZGW_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN",
    default=None,
    documentation=DocumentationParams(
        help_text="Skip sending notifications for statustypen that have 'informeren' set to False.",
        group="Setup-configuration",
    ),
)
ZGW_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE = config(
    "ZGW_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE",
    default=None,
    documentation=DocumentationParams(
        help_text="Reformat eSuite zaak identificatie numbers to a human-readable format.",
        group="Setup-configuration",
    ),
)
ZGW_FETCH_EHERKENNING_ZAKEN_WITH_RSIN = config(
    "ZGW_FETCH_EHERKENNING_ZAKEN_WITH_RSIN",
    default=None,
    documentation=DocumentationParams(
        help_text="Fetch eHerkenning zaken using the organisation's RSIN instead of KvK number.",
        group="Setup-configuration",
    ),
)

# KIC configuration variables
KIC_CONFIG_ENABLE = config(
    "KIC_CONFIG_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable automatic KIC (Klantinteractiescomponenten) API configuration via setup-configuration.",
        group="Setup-configuration",
    ),
)
KIC_SERVER_CERTIFICATE_LABEL = config(
    "KIC_SERVER_CERTIFICATE_LABEL",
    default="",
    documentation=DocumentationParams(
        help_text="Label used to identify the TLS client certificate for KIC services in the certificate store.",
        group="Setup-configuration",
    ),
)
KIC_SERVER_CERTIFICATE_TYPE = config(
    "KIC_SERVER_CERTIFICATE_TYPE",
    default="",
    documentation=DocumentationParams(
        help_text="Certificate store type for KIC services. Use 'certificate-only' or 'key-pair'.",
        group="Setup-configuration",
    ),
)
KIC_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE = config(
    "KIC_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE",
    default=None,
    documentation=DocumentationParams(
        help_text="Path to the public certificate file for KIC TLS client authentication.",
        group="Setup-configuration",
    ),
)
KIC_KLANTEN_SERVICE_API_ROOT = config(
    "KIC_KLANTEN_SERVICE_API_ROOT",
    default="",
    documentation=DocumentationParams(
        help_text="Root URL of the Klanten API. Must end with a trailing slash.",
        group="Setup-configuration",
    ),
)
if KIC_KLANTEN_SERVICE_API_ROOT and not KIC_KLANTEN_SERVICE_API_ROOT.endswith("/"):
    KIC_KLANTEN_SERVICE_API_ROOT = f"{KIC_KLANTEN_SERVICE_API_ROOT.strip()}/"
KIC_KLANTEN_OAS_URL = KIC_KLANTEN_SERVICE_API_ROOT  # this is still required by the form, but not actually used
KIC_KLANTEN_SERVICE_API_CLIENT_ID = config(
    "KIC_KLANTEN_SERVICE_API_CLIENT_ID",
    default="",
    documentation=DocumentationParams(
        help_text="Client ID for JWT authentication with the Klanten API.",
        group="Setup-configuration",
    ),
)
KIC_KLANTEN_SERVICE_API_SECRET = config(
    "KIC_KLANTEN_SERVICE_API_SECRET",
    default="",
    documentation=DocumentationParams(
        help_text="Secret for JWT authentication with the Klanten API.",
        group="Setup-configuration",
    ),
)
KIC_CONTACTMOMENTEN_SERVICE_API_ROOT = config(
    "KIC_CONTACTMOMENTEN_SERVICE_API_ROOT",
    default="",
    documentation=DocumentationParams(
        help_text="Root URL of the Contactmomenten API. Must end with a trailing slash.",
        group="Setup-configuration",
    ),
)
if (
    KIC_CONTACTMOMENTEN_SERVICE_API_ROOT
    and not KIC_CONTACTMOMENTEN_SERVICE_API_ROOT.endswith("/")
):
    KIC_CONTACTMOMENTEN_SERVICE_API_ROOT = (
        f"{KIC_CONTACTMOMENTEN_SERVICE_API_ROOT.strip()}/"
    )
KIC_CONTACTMOMENTEN_OAS_URL = KIC_CONTACTMOMENTEN_SERVICE_API_ROOT  # this is still required by the form, but not actually used
KIC_CONTACTMOMENTEN_SERVICE_API_CLIENT_ID = config(
    "KIC_CONTACTMOMENTEN_SERVICE_API_CLIENT_ID",
    default="",
    documentation=DocumentationParams(
        help_text="Client ID for JWT authentication with the Contactmomenten API.",
        group="Setup-configuration",
    ),
)
KIC_CONTACTMOMENTEN_SERVICE_API_SECRET = config(
    "KIC_CONTACTMOMENTEN_SERVICE_API_SECRET",
    default="",
    documentation=DocumentationParams(
        help_text="Secret for JWT authentication with the Contactmomenten API.",
        group="Setup-configuration",
    ),
)
KIC_REGISTER_EMAIL = config(
    "KIC_REGISTER_EMAIL",
    default=None,
    documentation=DocumentationParams(
        help_text="Enable registering contact requests via email as a fallback when contactmomenten are unavailable.",
        group="Setup-configuration",
    ),
)
KIC_REGISTER_CONTACT_MOMENT = config(
    "KIC_REGISTER_CONTACT_MOMENT",
    default=None,
    documentation=DocumentationParams(
        help_text="Enable registering contact form submissions as contactmomenten via the KIC API.",
        group="Setup-configuration",
    ),
)
KIC_REGISTER_BRONORGANISATIE_RSIN = config(
    "KIC_REGISTER_BRONORGANISATIE_RSIN",
    default=None,
    documentation=DocumentationParams(
        help_text="RSIN of the organisation set as bronorganisatie when creating contactmomenten.",
        group="Setup-configuration",
    ),
)
KIC_REGISTER_CHANNEL = config(
    "KIC_REGISTER_CHANNEL",
    default=None,
    documentation=DocumentationParams(
        help_text="Default channel value for created contactmomenten (e.g. 'email' or 'contactformulier').",
        group="Setup-configuration",
    ),
)
KIC_REGISTER_TYPE = config(
    "KIC_REGISTER_TYPE",
    default=None,
    documentation=DocumentationParams(
        help_text="Default type value for created contactmomenten.",
        group="Setup-configuration",
    ),
)
KIC_REGISTER_EMPLOYEE_ID = config(
    "KIC_REGISTER_EMPLOYEE_ID",
    default=None,
    documentation=DocumentationParams(
        help_text="Employee identifier assigned as medewerker on newly created contactmomenten.",
        group="Setup-configuration",
    ),
)
KIC_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER = config(
    "KIC_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER",
    default=None,
    documentation=DocumentationParams(
        help_text="Use RSIN instead of KvK number for the innNnpId query parameter when looking up klanten.",
        group="Setup-configuration",
    ),
)


#
# SiteConfiguration variables
#
SITE_CONFIG_ENABLE = config(
    "SITE_CONFIG_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable automatic SiteConfiguration bootstrap via setup-configuration.",
        group="Setup-configuration",
    ),
)
SITE_NAME = config(
    "SITE_NAME",
    default=None,
    documentation=DocumentationParams(
        help_text="Site name displayed in the browser title bar and outgoing emails.",
        group="Setup-configuration",
    ),
)
SITE_PRIMARY_COLOR = config(
    "SITE_PRIMARY_COLOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Primary brand colour as a CSS hex code (e.g. #007FAD).",
        group="Setup-configuration",
    ),
)
SITE_SECONDARY_COLOR = config(
    "SITE_SECONDARY_COLOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Secondary brand colour as a CSS hex code.",
        group="Setup-configuration",
    ),
)
SITE_ACCENT_COLOR = config(
    "SITE_ACCENT_COLOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Accent colour as a CSS hex code, used for highlights and interactive elements.",
        group="Setup-configuration",
    ),
)
SITE_PRIMARY_FONT_COLOR = config(
    "SITE_PRIMARY_FONT_COLOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Font colour used on primary-colour backgrounds.",
        group="Setup-configuration",
    ),
)
SITE_SECONDARY_FONT_COLOR = config(
    "SITE_SECONDARY_FONT_COLOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Font colour used on secondary-colour backgrounds.",
        group="Setup-configuration",
    ),
)
SITE_ACCENT_FONT_COLOR = config(
    "SITE_ACCENT_FONT_COLOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Font colour used on accent-colour backgrounds.",
        group="Setup-configuration",
    ),
)
SITE_WARNING_BANNER_ENABLED = config(
    "SITE_WARNING_BANNER_ENABLED",
    default=None,
    documentation=DocumentationParams(
        help_text="Show a sitewide warning banner at the top of every page.",
        group="Setup-configuration",
    ),
)
SITE_WARNING_BANNER_TEXT = config(
    "SITE_WARNING_BANNER_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Message text displayed in the sitewide warning banner.",
        group="Setup-configuration",
    ),
)
SITE_WARNING_BANNER_BACKGROUND_COLOR = config(
    "SITE_WARNING_BANNER_BACKGROUND_COLOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Background colour of the warning banner as a CSS hex code.",
        group="Setup-configuration",
    ),
)
SITE_CONTACTMOMENT_CONTACT_FORM_ENABLED = config(
    "SITE_CONTACTMOMENT_CONTACT_FORM_ENABLED",
    default=None,
    documentation=DocumentationParams(
        help_text="Show the contact form that submits requests as contactmomenten via the KIC API.",
        group="Setup-configuration",
    ),
)
SITE_WARNING_BANNER_FONT_COLOR = config(
    "SITE_WARNING_BANNER_FONT_COLOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Font colour for the text in the warning banner.",
        group="Setup-configuration",
    ),
)
SITE_HERO_IMAGE_LOGIN = config(
    "SITE_HERO_IMAGE_LOGIN",
    default=None,
    documentation=DocumentationParams(
        help_text="Path to the hero image displayed on the login page.",
        group="Setup-configuration",
    ),
)
SITE_LOGIN_SHOW = config(
    "SITE_LOGIN_SHOW",
    default=None,
    documentation=DocumentationParams(
        help_text="Show login options on the public homepage.",
        group="Setup-configuration",
    ),
)
SITE_LOGIN_ALLOW_REGISTRATION = config(
    "SITE_LOGIN_ALLOW_REGISTRATION",
    default=None,
    documentation=DocumentationParams(
        help_text="Allow new users to self-register via the registration form.",
        group="Setup-configuration",
    ),
)
SITE_LOGIN_2FA_SMS = config(
    "SITE_LOGIN_2FA_SMS",
    default=None,
    documentation=DocumentationParams(
        help_text="Require SMS-based two-factor authentication at login.",
        group="Setup-configuration",
    ),
)
SITE_LOGIN_TEXT = config(
    "SITE_LOGIN_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Custom introductory text shown above the login form.",
        group="Setup-configuration",
    ),
)
SITE_REGISTRATION_TEXT = config(
    "SITE_REGISTRATION_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Custom introductory text shown on the registration page.",
        group="Setup-configuration",
    ),
)
SITE_HOME_WELCOME_TITLE = config(
    "SITE_HOME_WELCOME_TITLE",
    default=None,
    documentation=DocumentationParams(
        help_text="Heading of the welcome block on the homepage.",
        group="Setup-configuration",
    ),
)
SITE_HOME_WELCOME_INTRO = config(
    "SITE_HOME_WELCOME_INTRO",
    default=None,
    documentation=DocumentationParams(
        help_text="Introductory text in the welcome block on the homepage.",
        group="Setup-configuration",
    ),
)
SITE_HOME_THEME_TITLE = config(
    "SITE_HOME_THEME_TITLE",
    default=None,
    documentation=DocumentationParams(
        help_text="Heading of the theme block on the homepage.",
        group="Setup-configuration",
    ),
)
SITE_HOME_THEME_INTRO = config(
    "SITE_HOME_THEME_INTRO",
    default=None,
    documentation=DocumentationParams(
        help_text="Introductory text in the theme block on the homepage.",
        group="Setup-configuration",
    ),
)
SITE_THEME_TITLE = config(
    "SITE_THEME_TITLE",
    default=None,
    documentation=DocumentationParams(
        help_text="Page title shown on the theme overview page.",
        group="Setup-configuration",
    ),
)
SITE_THEME_INTRO = config(
    "SITE_THEME_INTRO",
    default=None,
    documentation=DocumentationParams(
        help_text="Introductory text shown on the theme overview page.",
        group="Setup-configuration",
    ),
)
SITE_HOME_MAP_TITLE = config(
    "SITE_HOME_MAP_TITLE",
    default=None,
    documentation=DocumentationParams(
        help_text="Heading of the map block on the homepage.",
        group="Setup-configuration",
    ),
)
SITE_HOME_MAP_INTRO = config(
    "SITE_HOME_MAP_INTRO",
    default=None,
    documentation=DocumentationParams(
        help_text="Introductory text in the map block on the homepage.",
        group="Setup-configuration",
    ),
)
SITE_HOME_QUESTIONNAIRE_TITLE = config(
    "SITE_HOME_QUESTIONNAIRE_TITLE",
    default=None,
    documentation=DocumentationParams(
        help_text="Heading of the questionnaire block on the homepage.",
        group="Setup-configuration",
    ),
)
SITE_HOME_QUESTIONNAIRE_INTRO = config(
    "SITE_HOME_QUESTIONNAIRE_INTRO",
    default=None,
    documentation=DocumentationParams(
        help_text="Introductory text in the questionnaire block on the homepage.",
        group="Setup-configuration",
    ),
)
SITE_HOME_PRODUCT_FINDER_TITLE = config(
    "SITE_HOME_PRODUCT_FINDER_TITLE",
    default=None,
    documentation=DocumentationParams(
        help_text="Heading of the product finder block on the homepage.",
        group="Setup-configuration",
    ),
)
SITE_HOME_PRODUCT_FINDER_INTRO = config(
    "SITE_HOME_PRODUCT_FINDER_INTRO",
    default=None,
    documentation=DocumentationParams(
        help_text="Introductory text in the product finder block on the homepage.",
        group="Setup-configuration",
    ),
)
SITE_SEARCH_ZERO_RESULTS_TEXT = config(
    "SEARCH_ZERO_RESULTS_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Text shown on the search page when a query returns no results.",
        group="Setup-configuration",
    ),
)
SITE_SELECT_QUESTIONNAIRE_TITLE = config(
    "SITE_SELECT_QUESTIONNAIRE_TITLE",
    default=None,
    documentation=DocumentationParams(
        help_text="Heading on the questionnaire selection page.",
        group="Setup-configuration",
    ),
)
SITE_SELECT_QUESTIONNAIRE_INTRO = config(
    "SITE_SELECT_QUESTIONNAIRE_INTRO",
    default=None,
    documentation=DocumentationParams(
        help_text="Introductory text on the questionnaire selection page.",
        group="Setup-configuration",
    ),
)
SITE_PLANS_INTRO = config(
    "SITE_PLANS_INTRO",
    default=None,
    documentation=DocumentationParams(
        help_text="Introductory text shown on the collaboration plans overview page.",
        group="Setup-configuration",
    ),
)
SITE_PLANS_NO_PLANS_MESSAGE = config(
    "SITE_PLANS_NO_PLANS_MESSAGE",
    default=None,
    documentation=DocumentationParams(
        help_text="Message shown when a user has no active collaboration plans.",
        group="Setup-configuration",
    ),
)
SITE_PLANS_EDIT_MESSAGE = config(
    "SITE_PLANS_EDIT_MESSAGE",
    default=None,
    documentation=DocumentationParams(
        help_text="Message shown to users when they are editing a collaboration plan.",
        group="Setup-configuration",
    ),
)
SITE_FOOTER_LOGO_TITLE = config(
    "SITE_FOOTER_LOGO_TITLE",
    default=None,
    documentation=DocumentationParams(
        help_text="Alt text and title attribute for the logo shown in the footer.",
        group="Setup-configuration",
    ),
)
SITE_FOOTER_LOGO_URL = config(
    "SITE_FOOTER_LOGO_URL",
    default=None,
    documentation=DocumentationParams(
        help_text="URL that the footer logo links to.",
        group="Setup-configuration",
    ),
)
SITE_HOME_HELP_TEXT = config(
    "SITE_HOME_HELP_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Contextual help text shown on the homepage.",
        group="Setup-configuration",
    ),
)
SITE_THEME_HELP_TEXT = config(
    "SITE_THEME_HELP_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Contextual help text shown on theme pages.",
        group="Setup-configuration",
    ),
)
SITE_PRODUCT_HELP_TEXT = config(
    "SITE_PRODUCT_HELP_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Contextual help text shown on product detail pages.",
        group="Setup-configuration",
    ),
)
SITE_SEARCH_HELP_TEXT = config(
    "SITE_SEARCH_HELP_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Contextual help text shown on the search results page.",
        group="Setup-configuration",
    ),
)
SITE_ACCOUNT_HELP_TEXT = config(
    "SITE_ACCOUNT_HELP_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Contextual help text shown on account management pages.",
        group="Setup-configuration",
    ),
)
SITE_QUESTIONNAIRE_HELP_TEXT = config(
    "SITE_QUESTIONNAIRE_HELP_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Contextual help text shown on questionnaire pages.",
        group="Setup-configuration",
    ),
)
SITE_PLAN_HELP_TEXT = config(
    "SITE_PLAN_HELP_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Contextual help text shown on collaboration plan pages.",
        group="Setup-configuration",
    ),
)
SITE_SEARCH_FILTER_CATEGORIES = config(
    "SITE_SEARCH_FILTER_CATEGORIES",
    default=None,
    documentation=DocumentationParams(
        help_text="Show the category filter on the search results page.",
        group="Setup-configuration",
    ),
)
SITE_SEARCH_FILTER_TAGS = config(
    "SITE_SEARCH_FILTER_TAGS",
    default=None,
    documentation=DocumentationParams(
        help_text="Show the tag filter on the search results page.",
        group="Setup-configuration",
    ),
)
SITE_SEARCH_FILTER_ORGANIZATIONS = config(
    "SITE_SEARCH_FILTER_ORGANIZATIONS",
    default=None,
    documentation=DocumentationParams(
        help_text="Show the organisation filter on the search results page.",
        group="Setup-configuration",
    ),
)
SITE_NOTIFICATIONS_ACTIONS_ENABLED = config(
    "SITE_NOTIFICATIONS_ACTIONS_ENABLED",
    default=None,
    documentation=DocumentationParams(
        help_text="Enable email notifications reminding users about pending actions.",
        group="Setup-configuration",
    ),
)
SITE_NOTIFICATIONS_CASES_ENABLED = config(
    "SITE_NOTIFICATIONS_CASES_ENABLED",
    default=None,
    documentation=DocumentationParams(
        help_text="Enable email notifications for case status updates.",
        group="Setup-configuration",
    ),
)
SITE_NOTIFICATIONS_PLANS_ENABLED = config(
    "SITE_NOTIFICATIONS_PLANS_ENABLED",
    default=None,
    documentation=DocumentationParams(
        help_text="Enable email notifications for collaboration plan updates.",
        group="Setup-configuration",
    ),
)
SITE_NOTIFICATIONS_MESSAGES_ENABLED = config(
    "SITE_NOTIFICATIONS_MESSAGES_ENABLED",
    default=None,
    documentation=DocumentationParams(
        help_text="Enable email notifications for new messages.",
        group="Setup-configuration",
    ),
)
SITE_RECIPIENTS_EMAIL_DIGEST = config(
    "SITE_RECIPIENTS_EMAIL_DIGEST",
    default=None,
    documentation=DocumentationParams(
        help_text="Email address that receives the daily digest of failed outgoing emails.",
        group="Setup-configuration",
    ),
)
SITE_CONTACT_PHONENUMBER = config(
    "SITE_CONTACT_PHONENUMBER",
    default=None,
    documentation=DocumentationParams(
        help_text="Municipal contact phone number shown in the site footer.",
        group="Setup-configuration",
    ),
)
SITE_CONTACT_PAGE = config(
    "SITE_CONTACT_PAGE",
    default=None,
    documentation=DocumentationParams(
        help_text="URL or path of the contact page linked from the site footer.",
        group="Setup-configuration",
    ),
)
SITE_GTM_CODE = config(
    "SITE_GTM_CODE",
    default=None,
    documentation=DocumentationParams(
        help_text="Google Tag Manager container ID (e.g. GTM-XXXXX). Leave empty to disable GTM.",
        group="Setup-configuration",
    ),
)
SITE_GA_CODE = config(
    "SITE_GA_CODE",
    default=None,
    documentation=DocumentationParams(
        help_text="Google Analytics measurement ID (e.g. G-XXXXX). Leave empty to disable GA.",
        group="Setup-configuration",
    ),
)
SITE_MATOMO_URL = config(
    "SITE_MATOMO_URL",
    default=None,
    documentation=DocumentationParams(
        help_text="URL of the Matomo instance used for analytics tracking.",
        group="Setup-configuration",
    ),
)
SITE_MATOMO_SITE_ID = config(
    "SITE_MATOMO_SITE_ID",
    default=None,
    documentation=DocumentationParams(
        help_text="Matomo site ID for this installation.",
        group="Setup-configuration",
    ),
)
SITE_SITEIMPROVE_ID = config(
    "SITE_SITEIMPROVE_ID",
    default=None,
    documentation=DocumentationParams(
        help_text="Siteimprove account ID. Leave empty to disable Siteimprove.",
        group="Setup-configuration",
    ),
)
SITE_COOKIE_INFO_TEXT = config(
    "SITE_COOKIE_INFO_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Text shown in the cookie consent banner.",
        group="Setup-configuration",
    ),
)
SITE_COOKIE_LINK_TEXT = config(
    "SITE_COOKIE_LINK_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Link text shown in the cookie consent banner.",
        group="Setup-configuration",
    ),
)
SITE_COOKIE_LINK_URL = config(
    "SITE_COOKIE_LINK_URL",
    default=None,
    documentation=DocumentationParams(
        help_text="URL the cookie consent banner link points to (e.g. privacy policy page).",
        group="Setup-configuration",
    ),
)
SITE_KCM_SURVEY_LINK_TEXT = config(
    "SITE_KCM_SURVEY_LINK_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Link text for the customer satisfaction (KCM) survey.",
        group="Setup-configuration",
    ),
)
SITE_KCM_SURVEY_LINK_URL = config(
    "SITE_KCM_SURVEY_LINK_URL",
    default=None,
    documentation=DocumentationParams(
        help_text="URL of the customer satisfaction survey.",
        group="Setup-configuration",
    ),
)
SITE_OPENID_CONNECT_LOGIN_TEXT = config(
    "SITE_OPENID_CONNECT_LOGIN_TEXT",
    default=None,
    documentation=DocumentationParams(
        help_text="Label shown on the OpenID Connect login button.",
        group="Setup-configuration",
    ),
)
SITE_OPENID_DISPLAY = config(
    "SITE_OPENID_DISPLAY",
    default=None,
    documentation=DocumentationParams(
        help_text="Controls how OpenID Connect login options are displayed.",
        group="Setup-configuration",
    ),
)
SITE_REDIRECT_TO = config(
    "SITE_REDIRECT_TO",
    default=None,
    documentation=DocumentationParams(
        help_text="URL to redirect all visitors to. Use during maintenance or migration.",
        group="Setup-configuration",
    ),
)
SITE_ALLOW_MESSAGES_FILE_SHARING = config(
    "SITE_ALLOW_MESSAGES_FILE_SHARING",
    default=None,
    documentation=DocumentationParams(
        help_text="Allow users to attach and share files via the messages feature.",
        group="Setup-configuration",
    ),
)
SITE_HIDE_CATEGORIES_FROM_ANONYMOUS_USERS = config(
    "SITE_HIDE_CATEGORIES_FROM_ANONYMOUS_USERS",
    default=None,
    documentation=DocumentationParams(
        help_text="Hide PDC theme categories from unauthenticated visitors.",
        group="Setup-configuration",
    ),
)
SITE_HIDE_SEARCH_FROM_ANONYMOUS_USERS = config(
    "SITE_HIDE_SEARCH_FROM_ANONYMOUS_USERS",
    default=None,
    documentation=DocumentationParams(
        help_text="Hide the search function from unauthenticated visitors.",
        group="Setup-configuration",
    ),
)
SITE_DISPLAY_SOCIAL = config(
    "SITE_DISPLAY_SOCIAL",
    default=None,
    documentation=DocumentationParams(
        help_text="Show social media share buttons on product pages.",
        group="Setup-configuration",
    ),
)
SITE_THEME_STYLESHEET = config(
    "SITE_THEME_STYLESHEET",
    default=None,
    documentation=DocumentationParams(
        help_text="Path to a custom CSS stylesheet that overrides default theme styles.",
        group="Setup-configuration",
    ),
)
SITE_EHERKENNING_ENABLED = config(
    "SITE_EHERKENNING_ENABLED",
    default=None,
    documentation=DocumentationParams(
        help_text="Show the eHerkenning login option on the login page.",
        group="Setup-configuration",
    ),
)


# Authentication configuration variables
# NOTE variables are namespaced with `DIGID_OIDC`, but some model field names also have `oidc_...` in them
DIGID_OIDC_CONFIG_ENABLE = config(
    "DIGID_OIDC_CONFIG_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable DigiD OIDC configuration via setup-configuration.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_BSN_CLAIM = config(
    "DIGID_OIDC_BSN_CLAIM",
    default=None,
    documentation=DocumentationParams(
        help_text="OIDC claim name that contains the citizen's BSN.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_RP_CLIENT_ID = config(
    "DIGID_OIDC_OIDC_RP_CLIENT_ID",
    default=None,
    documentation=DocumentationParams(
        help_text="Client ID of this application registered with the DigiD OIDC provider.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_RP_CLIENT_SECRET = config(
    "DIGID_OIDC_OIDC_RP_CLIENT_SECRET",
    default=None,
    documentation=DocumentationParams(
        help_text="Client secret for authenticating with the DigiD OIDC provider.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_RP_SIGN_ALGO = config(
    "DIGID_OIDC_OIDC_RP_SIGN_ALGO",
    default=None,
    documentation=DocumentationParams(
        help_text="JWT signing algorithm used by the DigiD OIDC provider (e.g. RS256).",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_RP_SCOPES_LIST = config(
    "DIGID_OIDC_OIDC_RP_SCOPES_LIST",
    default=None,
    documentation=DocumentationParams(
        help_text="Space-separated list of OIDC scopes to request from the DigiD provider.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_OP_DISCOVERY_ENDPOINT = config(
    "DIGID_OIDC_OIDC_OP_DISCOVERY_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="DigiD OIDC provider discovery endpoint URL (/.well-known/openid-configuration).",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_OP_JWKS_ENDPOINT = config(
    "DIGID_OIDC_OIDC_OP_JWKS_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="DigiD OIDC provider JWKS endpoint URL for verifying token signatures.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT = config(
    "DIGID_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="DigiD OIDC provider authorization endpoint URL.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_OP_TOKEN_ENDPOINT = config(
    "DIGID_OIDC_OIDC_OP_TOKEN_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="DigiD OIDC provider token endpoint URL.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_OP_USER_ENDPOINT = config(
    "DIGID_OIDC_OIDC_OP_USER_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="DigiD OIDC provider userinfo endpoint URL.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_RP_IDP_SIGN_KEY = config(
    "DIGID_OIDC_OIDC_RP_IDP_SIGN_KEY",
    default=None,
    documentation=DocumentationParams(
        help_text="Public key used to verify DigiD ID token signatures (PEM format).",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_USERINFO_CLAIMS_SOURCE = config(
    "DIGID_OIDC_USERINFO_CLAIMS_SOURCE",
    default=None,
    documentation=DocumentationParams(
        help_text="Source of user claims for DigiD: 'userinfo_endpoint' or 'id_token'.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_OP_LOGOUT_ENDPOINT = config(
    "DIGID_OIDC_OIDC_OP_LOGOUT_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="DigiD OIDC provider logout endpoint URL.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_KEYCLOAK_IDP_HINT = config(
    "DIGID_OIDC_OIDC_KEYCLOAK_IDP_HINT",
    default=None,
    documentation=DocumentationParams(
        help_text="Keycloak IdP hint passed to DigiD for broker routing to the correct identity provider.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_USE_NONCE = config(
    "DIGID_OIDC_OIDC_USE_NONCE",
    default=None,
    documentation=DocumentationParams(
        help_text="Include a nonce in the DigiD OIDC authentication request to prevent replay attacks.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_NONCE_SIZE = config(
    "DIGID_OIDC_OIDC_NONCE_SIZE",
    default=None,
    documentation=DocumentationParams(
        help_text="Byte length of the nonce generated for DigiD OIDC authentication requests.",
        group="Setup-configuration",
    ),
)
DIGID_OIDC_OIDC_STATE_SIZE = config(
    "DIGID_OIDC_OIDC_STATE_SIZE",
    default=None,
    documentation=DocumentationParams(
        help_text="Byte length of the state parameter generated for DigiD OIDC authentication requests.",
        group="Setup-configuration",
    ),
)

# NOTE variables are namespaced with `EHERKENNING_OIDC`, but some model field names also have `oidc_...` in them
EHERKENNING_OIDC_CONFIG_ENABLE = config(
    "EHERKENNING_OIDC_CONFIG_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable eHerkenning OIDC configuration via setup-configuration.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_LEGAL_SUBJECT_CLAIM = config(
    "EHERKENNING_OIDC_LEGAL_SUBJECT_CLAIM",
    default=None,
    documentation=DocumentationParams(
        help_text="OIDC claim name containing the legal subject identifier (KvK number or RSIN).",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_RP_CLIENT_ID = config(
    "EHERKENNING_OIDC_OIDC_RP_CLIENT_ID",
    default=None,
    documentation=DocumentationParams(
        help_text="Client ID of this application registered with the eHerkenning OIDC provider.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_RP_CLIENT_SECRET = config(
    "EHERKENNING_OIDC_OIDC_RP_CLIENT_SECRET",
    default=None,
    documentation=DocumentationParams(
        help_text="Client secret for authenticating with the eHerkenning OIDC provider.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_RP_SIGN_ALGO = config(
    "EHERKENNING_OIDC_OIDC_RP_SIGN_ALGO",
    default=None,
    documentation=DocumentationParams(
        help_text="JWT signing algorithm used by the eHerkenning OIDC provider (e.g. RS256).",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_RP_SCOPES_LIST = config(
    "EHERKENNING_OIDC_OIDC_RP_SCOPES_LIST",
    default=None,
    documentation=DocumentationParams(
        help_text="Space-separated list of OIDC scopes to request from the eHerkenning provider.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_OP_DISCOVERY_ENDPOINT = config(
    "EHERKENNING_OIDC_OIDC_OP_DISCOVERY_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="eHerkenning OIDC provider discovery endpoint URL.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_OP_JWKS_ENDPOINT = config(
    "EHERKENNING_OIDC_OIDC_OP_JWKS_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="eHerkenning OIDC provider JWKS endpoint URL.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT = config(
    "EHERKENNING_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="eHerkenning OIDC provider authorization endpoint URL.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_OP_TOKEN_ENDPOINT = config(
    "EHERKENNING_OIDC_OIDC_OP_TOKEN_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="eHerkenning OIDC provider token endpoint URL.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_OP_USER_ENDPOINT = config(
    "EHERKENNING_OIDC_OIDC_OP_USER_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="eHerkenning OIDC provider userinfo endpoint URL.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_RP_IDP_SIGN_KEY = config(
    "EHERKENNING_OIDC_OIDC_RP_IDP_SIGN_KEY",
    default=None,
    documentation=DocumentationParams(
        help_text="Public key used to verify eHerkenning ID token signatures (PEM format).",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_USERINFO_CLAIMS_SOURCE = config(
    "EHERKENNING_OIDC_USERINFO_CLAIMS_SOURCE",
    default=None,
    documentation=DocumentationParams(
        help_text="Source of user claims for eHerkenning: 'userinfo_endpoint' or 'id_token'.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_OP_LOGOUT_ENDPOINT = config(
    "EHERKENNING_OIDC_OIDC_OP_LOGOUT_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="eHerkenning OIDC provider logout endpoint URL.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_KEYCLOAK_IDP_HINT = config(
    "EHERKENNING_OIDC_OIDC_KEYCLOAK_IDP_HINT",
    default=None,
    documentation=DocumentationParams(
        help_text="Keycloak IdP hint for routing to the eHerkenning identity provider.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_USE_NONCE = config(
    "EHERKENNING_OIDC_OIDC_USE_NONCE",
    default=None,
    documentation=DocumentationParams(
        help_text="Include a nonce in eHerkenning OIDC authentication requests.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_NONCE_SIZE = config(
    "EHERKENNING_OIDC_OIDC_NONCE_SIZE",
    default=None,
    documentation=DocumentationParams(
        help_text="Byte length of the nonce for eHerkenning OIDC authentication requests.",
        group="Setup-configuration",
    ),
)
EHERKENNING_OIDC_OIDC_STATE_SIZE = config(
    "EHERKENNING_OIDC_OIDC_STATE_SIZE",
    default=None,
    documentation=DocumentationParams(
        help_text="Byte length of the state parameter for eHerkenning OIDC authentication requests.",
        group="Setup-configuration",
    ),
)

# NOTE variables are namespaced with `ADMIN_OIDC`, but some model field names also have `oidc_...` in them
ADMIN_OIDC_CONFIG_ENABLE = config(
    "ADMIN_OIDC_CONFIG_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable admin OIDC SSO configuration via setup-configuration.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_RP_CLIENT_ID = config(
    "ADMIN_OIDC_OIDC_RP_CLIENT_ID",
    default=None,
    documentation=DocumentationParams(
        help_text="Client ID of this application registered with the admin OIDC provider.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_RP_CLIENT_SECRET = config(
    "ADMIN_OIDC_OIDC_RP_CLIENT_SECRET",
    default=None,
    documentation=DocumentationParams(
        help_text="Client secret for authenticating with the admin OIDC provider.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_RP_SCOPES_LIST = config(
    "ADMIN_OIDC_OIDC_RP_SCOPES_LIST",
    default=None,
    documentation=DocumentationParams(
        help_text="Space-separated list of OIDC scopes to request from the admin OIDC provider.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_RP_SIGN_ALGO = config(
    "ADMIN_OIDC_OIDC_RP_SIGN_ALGO",
    default=None,
    documentation=DocumentationParams(
        help_text="JWT signing algorithm used by the admin OIDC provider (e.g. RS256).",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_RP_IDP_SIGN_KEY = config(
    "ADMIN_OIDC_OIDC_RP_IDP_SIGN_KEY",
    default=None,
    documentation=DocumentationParams(
        help_text="Public key used to verify admin OIDC ID token signatures (PEM format).",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_OP_DISCOVERY_ENDPOINT = config(
    "ADMIN_OIDC_OIDC_OP_DISCOVERY_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="Admin OIDC provider discovery endpoint URL.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_OP_JWKS_ENDPOINT = config(
    "ADMIN_OIDC_OIDC_OP_JWKS_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="Admin OIDC provider JWKS endpoint URL.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT = config(
    "ADMIN_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="Admin OIDC provider authorization endpoint URL.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_OP_TOKEN_ENDPOINT = config(
    "ADMIN_OIDC_OIDC_OP_TOKEN_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="Admin OIDC provider token endpoint URL.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_OP_USER_ENDPOINT = config(
    "ADMIN_OIDC_OIDC_OP_USER_ENDPOINT",
    default=None,
    documentation=DocumentationParams(
        help_text="Admin OIDC provider userinfo endpoint URL.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_USERNAME_CLAIM = config(
    "ADMIN_OIDC_USERNAME_CLAIM",
    default=None,
    documentation=DocumentationParams(
        help_text="OIDC claim used as the admin user's username.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_GROUPS_CLAIM = config(
    "ADMIN_OIDC_GROUPS_CLAIM",
    default=None,
    documentation=DocumentationParams(
        help_text="OIDC claim containing the user's group memberships.",
        group="Setup-configuration",
    ),
)
# XXX: this needs to be provided as a Mapping[str, list[str]] now instead of Mapping[str, str]!
ADMIN_OIDC_CLAIM_MAPPING = config(
    "ADMIN_OIDC_CLAIM_MAPPING",
    default=None,
    documentation=DocumentationParams(
        help_text="JSON mapping of OIDC claims to Django user model fields.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_SYNC_GROUPS = config(
    "ADMIN_OIDC_SYNC_GROUPS",
    default=None,
    documentation=DocumentationParams(
        help_text="Synchronise admin user Django groups from the OIDC groups claim.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_SYNC_GROUPS_GLOB_PATTERN = config(
    "ADMIN_OIDC_SYNC_GROUPS_GLOB_PATTERN",
    default=None,
    documentation=DocumentationParams(
        help_text="Glob pattern to filter which OIDC groups are synchronised to Django.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_DEFAULT_GROUPS = config(
    "ADMIN_OIDC_DEFAULT_GROUPS",
    default=None,
    documentation=DocumentationParams(
        help_text="Django groups assigned to new admin users by default.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_MAKE_USERS_STAFF = config(
    "ADMIN_OIDC_MAKE_USERS_STAFF",
    default=None,
    documentation=DocumentationParams(
        help_text="Automatically grant is_staff to users who log in via admin OIDC SSO.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_SUPERUSER_GROUP_NAMES = config(
    "ADMIN_OIDC_SUPERUSER_GROUP_NAMES",
    default=None,
    documentation=DocumentationParams(
        help_text="OIDC group names whose members are granted Django superuser status.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_USE_NONCE = config(
    "ADMIN_OIDC_OIDC_USE_NONCE",
    default=None,
    documentation=DocumentationParams(
        help_text="Include a nonce in admin OIDC authentication requests.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_NONCE_SIZE = config(
    "ADMIN_OIDC_OIDC_NONCE_SIZE",
    default=None,
    documentation=DocumentationParams(
        help_text="Byte length of the nonce for admin OIDC authentication requests.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_OIDC_STATE_SIZE = config(
    "ADMIN_OIDC_OIDC_STATE_SIZE",
    default=None,
    documentation=DocumentationParams(
        help_text="Byte length of the state parameter for admin OIDC authentication requests.",
        group="Setup-configuration",
    ),
)
ADMIN_OIDC_USERINFO_CLAIMS_SOURCE = config(
    "ADMIN_OIDC_USERINFO_CLAIMS_SOURCE",
    default=None,
    documentation=DocumentationParams(
        help_text="Source of admin user claims: 'userinfo_endpoint' or 'id_token'.",
        group="Setup-configuration",
    ),
)

#
# DigiD SAML
#
DIGID_SAML_CONFIG_ENABLE = config(
    "DIGID_SAML_SAML_CONFIG_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable DigiD SAML configuration via setup-configuration.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_CERTIFICATE_LABEL = config(
    "DIGID_SAML_CERTIFICATE_LABEL",
    default=None,
    documentation=DocumentationParams(
        help_text="Label identifying the DigiD SP certificate in the certificate store.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_CERTIFICATE_TYPE = config(
    "DIGID_SAML_CERTIFICATE_TYPE",
    default=None,
    documentation=DocumentationParams(
        help_text="DigiD SP certificate type. Use 'certificate-only' or 'key-pair'.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_CERTIFICATE_PUBLIC_CERTIFICATE = config(
    "DIGID_SAML_CERTIFICATE_PUBLIC_CERTIFICATE",
    default=None,
    documentation=DocumentationParams(
        help_text="Path to the DigiD SP public certificate file (PEM format).",
        group="Setup-configuration",
    ),
)
DIGID_SAML_CERTIFICATE_PRIVATE_KEY = config(
    "DIGID_SAML_CERTIFICATE_PRIVATE_KEY",
    default=None,
    documentation=DocumentationParams(
        help_text="Path to the DigiD SP private key file (PEM format).",
        group="Setup-configuration",
    ),
)
DIGID_SAML_METADATA_FILE_SOURCE = config(
    "DIGID_SAML_METADATA_FILE_SOURCE",
    default=None,
    documentation=DocumentationParams(
        help_text="URL or file path of the DigiD IdP SAML metadata.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_WANT_ASSERTIONS_SIGNED = config(
    "DIGID_SAML_WANT_ASSERTIONS_SIGNED",
    default=None,
    documentation=DocumentationParams(
        help_text="Require DigiD SAML assertions to be signed by the IdP.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_WANT_ASSERTIONS_ENCRYPTED = config(
    "DIGID_SAML_WANT_ASSERTIONS_ENCRYPTED",
    default=None,
    documentation=DocumentationParams(
        help_text="Require DigiD SAML assertions to be encrypted by the IdP.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_ARTIFACT_RESOLVE_CONTENT_TYPE = config(
    "DIGID_SAML_ARTIFACT_RESOLVE_CONTENT_TYPE",
    default=None,
    documentation=DocumentationParams(
        help_text="Content-Type header sent with DigiD artifact resolve requests.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_KEY_PASSPHRASE = config(
    "DIGID_SAML_KEY_PASSPHRASE",
    default=None,
    documentation=DocumentationParams(
        help_text="Passphrase for the encrypted DigiD SP private key.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_SIGNATURE_ALGORITHM = config(
    "DIGID_SAML_SIGNATURE_ALGORITHM",
    default=None,
    documentation=DocumentationParams(
        help_text="XML signature algorithm URI for DigiD SAML messages.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_DIGEST_ALGORITHM = config(
    "DIGID_SAML_DIGEST_ALGORITHM",
    default=None,
    documentation=DocumentationParams(
        help_text="XML digest algorithm URI for DigiD SAML messages.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_ENTITY_ID = config(
    "DIGID_SAML_ENTITY_ID",
    default=None,
    documentation=DocumentationParams(
        help_text="SAML EntityID (audience URI) of this service provider for DigiD.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_BASE_URL = config(
    "DIGID_SAML_BASE_URL",
    default=None,
    documentation=DocumentationParams(
        help_text="Base URL of this application used to construct DigiD SAML callback URLs.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_SERVICE_NAME = config(
    "DIGID_SAML_SERVICE_NAME",
    default=None,
    documentation=DocumentationParams(
        help_text="Service name presented to citizens during DigiD authentication.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_SERVICE_DESCRIPTION = config(
    "DIGID_SAML_SERVICE_DESCRIPTION",
    default=None,
    documentation=DocumentationParams(
        help_text="Service description presented to citizens during DigiD authentication.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_TECHNICAL_CONTACT_PERSON_TELEPHONE = config(
    "DIGID_SAML_TECHNICAL_CONTACT_PERSON_TELEPHONE",
    default=None,
    documentation=DocumentationParams(
        help_text="Phone number of the technical contact person for DigiD, included in SAML metadata.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_TECHNICAL_CONTACT_PERSON_EMAIL = config(
    "DIGID_SAML_TECHNICAL_CONTACT_PERSON_EMAIL",
    default=None,
    documentation=DocumentationParams(
        help_text="Email address of the technical contact person for DigiD, included in SAML metadata.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_ORGANIZATION_URL = config(
    "DIGID_SAML_ORGANIZATION_URL",
    default=None,
    documentation=DocumentationParams(
        help_text="URL of the operating organisation, included in DigiD SAML metadata.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_ORGANIZATION_NAME = config(
    "DIGID_SAML_ORGANIZATION_NAME",
    default=None,
    documentation=DocumentationParams(
        help_text="Name of the operating organisation, included in DigiD SAML metadata.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_ATTRIBUTE_CONSUMING_SERVICE_INDEX = config(
    "DIGID_SAML_ATTRIBUTE_CONSUMING_SERVICE_INDEX",
    default=None,
    documentation=DocumentationParams(
        help_text="AttributeConsumingService index in the DigiD SAML metadata.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_REQUESTED_ATTRIBUTES = config(
    "DIGID_SAML_REQUESTED_ATTRIBUTES",
    default=None,
    documentation=DocumentationParams(
        help_text="JSON list of SAML attribute names requested from DigiD.",
        group="Setup-configuration",
    ),
)
DIGID_SAML_SLO = config(
    "DIGID_SAML_SLO",
    default=None,
    documentation=DocumentationParams(
        help_text="Enable SAML Single Logout for DigiD.",
        group="Setup-configuration",
    ),
)

#
# Eherkenning SAML
#
EHERKENNING_SAML_CONFIG_ENABLE = config(
    "EHERKENNING_SAML_CONFIG_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable eHerkenning SAML configuration via setup-configuration.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_CERTIFICATE_LABEL = config(
    "EHERKENNING_SAML_CERTIFICATE_LABEL",
    default=None,
    documentation=DocumentationParams(
        help_text="Label identifying the eHerkenning SP certificate in the certificate store.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_CERTIFICATE_TYPE = config(
    "EHERKENNING_SAML_CERTIFICATE_TYPE",
    default=None,
    documentation=DocumentationParams(
        help_text="eHerkenning SP certificate type. Use 'certificate-only' or 'key-pair'.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_CERTIFICATE_PUBLIC_CERTIFICATE = config(
    "EHERKENNING_SAML_CERTIFICATE_PUBLIC_CERTIFICATE",
    default=None,
    documentation=DocumentationParams(
        help_text="Path to the eHerkenning SP public certificate file (PEM format).",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_CERTIFICATE_PRIVATE_KEY = config(
    "EHERKENNING_SAML_CERTIFICATE_PRIVATE_KEY",
    default=None,
    documentation=DocumentationParams(
        help_text="Path to the eHerkenning SP private key file (PEM format).",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_METADATA_FILE_SOURCE = config(
    "EHERKENNING_SAML_METADATA_FILE_SOURCE",
    default=None,
    documentation=DocumentationParams(
        help_text="URL or file path of the eHerkenning IdP SAML metadata.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_WANT_ASSERTIONS_SIGNED = config(
    "EHERKENNING_SAML_WANT_ASSERTIONS_SIGNED",
    default=None,
    documentation=DocumentationParams(
        help_text="Require eHerkenning SAML assertions to be signed by the IdP.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_WANT_ASSERTIONS_ENCRYPTED = config(
    "EHERKENNING_SAML_WANT_ASSERTIONS_ENCRYPTED",
    default=None,
    documentation=DocumentationParams(
        help_text="Require eHerkenning SAML assertions to be encrypted by the IdP.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_ARTIFACT_RESOLVE_CONTENT_TYPE = config(
    "EHERKENNING_SAML_ARTIFACT_RESOLVE_CONTENT_TYPE",
    default=None,
    documentation=DocumentationParams(
        help_text="Content-Type header sent with eHerkenning artifact resolve requests.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_KEY_PASSPHRASE = config(
    "EHERKENNING_SAML_KEY_PASSPHRASE",
    default=None,
    documentation=DocumentationParams(
        help_text="Passphrase for the encrypted eHerkenning SP private key.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_SIGNATURE_ALGORITHM = config(
    "EHERKENNING_SAML_SIGNATURE_ALGORITHM",
    default=None,
    documentation=DocumentationParams(
        help_text="XML signature algorithm URI for eHerkenning SAML messages.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_DIGEST_ALGORITHM = config(
    "EHERKENNING_SAML_DIGEST_ALGORITHM",
    default=None,
    documentation=DocumentationParams(
        help_text="XML digest algorithm URI for eHerkenning SAML messages.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_ENTITY_ID = config(
    "EHERKENNING_SAML_ENTITY_ID",
    default=None,
    documentation=DocumentationParams(
        help_text="SAML EntityID (audience URI) of this service provider for eHerkenning.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_BASE_URL = config(
    "EHERKENNING_SAML_BASE_URL",
    default=None,
    documentation=DocumentationParams(
        help_text="Base URL of this application used to construct eHerkenning SAML callback URLs.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_SERVICE_NAME = config(
    "EHERKENNING_SAML_SERVICE_NAME",
    default=None,
    documentation=DocumentationParams(
        help_text="Service name presented during eHerkenning authentication.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_SERVICE_DESCRIPTION = config(
    "EHERKENNING_SAML_SERVICE_DESCRIPTION",
    default=None,
    documentation=DocumentationParams(
        help_text="Service description presented during eHerkenning authentication.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_TECHNICAL_CONTACT_PERSON_TELEPHONE = config(
    "EHERKENNING_SAML_TECHNICAL_CONTACT_PERSON_TELEPHONE",
    default=None,
    documentation=DocumentationParams(
        help_text="Phone number of the technical contact person for eHerkenning, included in SAML metadata.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_TECHNICAL_CONTACT_PERSON_EMAIL = config(
    "EHERKENNING_SAML_TECHNICAL_CONTACT_PERSON_EMAIL",
    default=None,
    documentation=DocumentationParams(
        help_text="Email address of the technical contact person for eHerkenning, included in SAML metadata.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_ORGANIZATION_URL = config(
    "EHERKENNING_SAML_ORGANIZATION_URL",
    default=None,
    documentation=DocumentationParams(
        help_text="URL of the operating organisation, included in eHerkenning SAML metadata.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_ORGANIZATION_NAME = config(
    "EHERKENNING_SAML_ORGANIZATION_NAME",
    default=None,
    documentation=DocumentationParams(
        help_text="Name of the operating organisation, included in eHerkenning SAML metadata.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_EH_LOA = config(
    "EHERKENNING_SAML_EH_LOA",
    default=None,
    documentation=DocumentationParams(
        help_text="Level of Assurance (LoA) required for eHerkenning authentication.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_EH_ATTRIBUTE_CONSUMING_SERVICE_INDEX = config(
    "EHERKENNING_SAML_EH_ATTRIBUTE_CONSUMING_SERVICE_INDEX",
    default=None,
    documentation=DocumentationParams(
        help_text="AttributeConsumingService index for eHerkenning in the SAML metadata.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_EH_REQUESTED_ATTRIBUTES = config(
    "EHERKENNING_SAML_EH_REQUESTED_ATTRIBUTES",
    default=None,
    documentation=DocumentationParams(
        help_text="JSON list of SAML attribute names requested from eHerkenning.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_EH_SERVICE_UUID = config(
    "EHERKENNING_SAML_EH_SERVICE_UUID",
    default=None,
    documentation=DocumentationParams(
        help_text="UUID identifying this service in the eHerkenning service catalogue.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_EH_SERVICE_INSTANCE_UUID = config(
    "EHERKENNING_SAML_EH_SERVICE_INSTANCE_UUID",
    default=None,
    documentation=DocumentationParams(
        help_text="UUID identifying this service instance in the eHerkenning service catalogue.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_EIDAS_LOA = config(
    "EHERKENNING_SAML_EIDAS_LOA",
    default=None,
    documentation=DocumentationParams(
        help_text="Level of Assurance required for eIDAS authentication via eHerkenning.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_EIDAS_ATTRIBUTE_CONSUMING_SERVICE_INDEX = config(
    "EHERKENNING_SAML_EIDAS_ATTRIBUTE_CONSUMING_SERVICE_INDEX",
    default=None,
    documentation=DocumentationParams(
        help_text="AttributeConsumingService index for eIDAS in the eHerkenning SAML metadata.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_EIDAS_REQUESTED_ATTRIBUTES = config(
    "EHERKENNING_SAML_EIDAS_REQUESTED_ATTRIBUTES",
    default=None,
    documentation=DocumentationParams(
        help_text="JSON list of SAML attribute names requested for eIDAS via eHerkenning.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_EIDAS_SERVICE_UUID = config(
    "EHERKENNING_SAML_EIDAS_SERVICE_UUID",
    default=None,
    documentation=DocumentationParams(
        help_text="UUID identifying the eIDAS service in the eHerkenning service catalogue.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_EIDAS_SERVICE_INSTANCE_UUID = config(
    "EHERKENNING_SAML_EIDAS_SERVICE_INSTANCE_UUID",
    default=None,
    documentation=DocumentationParams(
        help_text="UUID identifying the eIDAS service instance in the eHerkenning service catalogue.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_OIN = config(
    "EHERKENNING_SAML_OIN",
    default=None,
    documentation=DocumentationParams(
        help_text="OIN (Organisatie-identificatienummer) of the operating organisation for eHerkenning.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_NO_EIDAS = config(
    "EHERKENNING_SAML_NO_EIDAS",
    default=None,
    documentation=DocumentationParams(
        help_text="Disable eIDAS support in the eHerkenning SAML configuration.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_PRIVACY_POLICY = config(
    "EHERKENNING_SAML_PRIVACY_POLICY",
    default=None,
    documentation=DocumentationParams(
        help_text="URL of the privacy policy, included in eHerkenning SAML metadata.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_MAKELAAR_ID = config(
    "EHERKENNING_SAML_MAKELAAR_ID",
    default=None,
    documentation=DocumentationParams(
        help_text="OIN of the eHerkenning makelaar (broker) used for this installation.",
        group="Setup-configuration",
    ),
)
EHERKENNING_SAML_SERVICE_LANGUAGE = config(
    "EHERKENNING_SAML_SERVICE_LANGUAGE",
    default=None,
    documentation=DocumentationParams(
        help_text="Language code of the service description in eHerkenning SAML metadata (e.g. 'nl').",
        group="Setup-configuration",
    ),
)

#
# CMS configuration variables
#

# benefits (ssd)
CMS_CONFIG_SSD_ENABLE = config(
    "CMS_CONFIG_SSD_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable setup-configuration for the Benefits (SSD) CMS app.",
        group="Setup-configuration",
    ),
)
# common extension
CMS_SSD_REQUIRES_AUTH = config(
    "CMS_SSD_REQUIRES_AUTH",
    default=None,
    documentation=DocumentationParams(
        help_text="Require authentication to access the Benefits section.",
        group="Setup-configuration",
    ),
)
CMS_SSD_REQUIRES_AUTH_BSN_OR_KVK = config(
    "CMS_SSD_REQUIRES_AUTH_BSN_OR_KVK",
    default=None,
    documentation=DocumentationParams(
        help_text="Require BSN or KvK identification to access the Benefits section.",
        group="Setup-configuration",
    ),
)
CMS_SSD_MENU_INDICATOR = config(
    "CMS_SSD_MENU_INDICATOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Show a notification indicator on the Benefits menu item.",
        group="Setup-configuration",
    ),
)
CMS_SSD_MENU_ICON = config(
    "CMS_SSD_MENU_ICON",
    default=None,
    documentation=DocumentationParams(
        help_text="Icon shown next to the Benefits item in the navigation menu.",
        group="Setup-configuration",
    ),
)

# cases
CMS_CONFIG_CASES_ENABLE = config(
    "CMS_CONFIG_CASES_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable setup-configuration for the Cases CMS app.",
        group="Setup-configuration",
    ),
)
# common extension
CMS_CASES_REQUIRES_AUTH = config(
    "CMS_CASES_REQUIRES_AUTH",
    default=None,
    documentation=DocumentationParams(
        help_text="Require authentication to access the Cases section.",
        group="Setup-configuration",
    ),
)
CMS_CASES_REQUIRES_AUTH_BSN_OR_KVK = config(
    "CMS_CASES_REQUIRES_AUTH_BSN_OR_KVK",
    default=None,
    documentation=DocumentationParams(
        help_text="Require BSN or KvK identification to access the Cases section.",
        group="Setup-configuration",
    ),
)
CMS_CASES_MENU_INDICATOR = config(
    "CMS_CASES_MENU_INDICATOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Show a notification indicator on the Cases menu item.",
        group="Setup-configuration",
    ),
)
CMS_CASES_MENU_ICON = config(
    "CMS_CASES_MENU_ICON",
    default=None,
    documentation=DocumentationParams(
        help_text="Icon shown next to the Cases item in the navigation menu.",
        group="Setup-configuration",
    ),
)

# collaborations
CMS_CONFIG_COLLABORATE_ENABLE = config(
    "CMS_CONFIG_COLLABORATE_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable setup-configuration for the Collaborations CMS app.",
        group="Setup-configuration",
    ),
)
# common extension
CMS_COLLABORATE_REQUIRES_AUTH = config(
    "CMS_COLLABORATE_REQUIRES_AUTH",
    default=None,
    documentation=DocumentationParams(
        help_text="Require authentication to access the Collaborations section.",
        group="Setup-configuration",
    ),
)
CMS_COLLABORATE_REQUIRES_AUTH_BSN_OR_KVK = config(
    "CMS_COLLABORATE_REQUIRES_AUTH_BSN_OR_KVK",
    default=None,
    documentation=DocumentationParams(
        help_text="Require BSN or KvK identification to access the Collaborations section.",
        group="Setup-configuration",
    ),
)
CMS_COLLABORATE_MENU_INDICATOR = config(
    "CMS_COLLABORATE_MENU_INDICATOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Show a notification indicator on the Collaborations menu item.",
        group="Setup-configuration",
    ),
)
CMS_COLLABORATE_MENU_ICON = config(
    "CMS_COLLABORATE_MENU_ICON",
    default=None,
    documentation=DocumentationParams(
        help_text="Icon shown next to the Collaborations item in the navigation menu.",
        group="Setup-configuration",
    ),
)

# inbox
CMS_CONFIG_INBOX_ENABLE = config(
    "CMS_CONFIG_INBOX_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable setup-configuration for the Inbox CMS app.",
        group="Setup-configuration",
    ),
)
# common extension
CMS_INBOX_REQUIRES_AUTH = config(
    "CMS_INBOX_REQUIRES_AUTH",
    default=None,
    documentation=DocumentationParams(
        help_text="Require authentication to access the Inbox section.",
        group="Setup-configuration",
    ),
)
CMS_INBOX_REQUIRES_AUTH_BSN_OR_KVK = config(
    "CMS_INBOX_REQUIRES_AUTH_BSN_OR_KVK",
    default=None,
    documentation=DocumentationParams(
        help_text="Require BSN or KvK identification to access the Inbox section.",
        group="Setup-configuration",
    ),
)
CMS_INBOX_MENU_INDICATOR = config(
    "CMS_INBOX_MENU_INDICATOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Show a notification indicator on the Inbox menu item.",
        group="Setup-configuration",
    ),
)
CMS_INBOX_MENU_ICON = config(
    "CMS_INBOX_MENU_ICON",
    default=None,
    documentation=DocumentationParams(
        help_text="Icon shown next to the Inbox item in the navigation menu.",
        group="Setup-configuration",
    ),
)

# products
CMS_CONFIG_PRODUCTS_ENABLE = config(
    "CMS_CONFIG_PRODUCTS_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable setup-configuration for the Products CMS app.",
        group="Setup-configuration",
    ),
)
# common extension
CMS_PRODUCTS_REQUIRES_AUTH = config(
    "CMS_PRODUCTS_REQUIRES_AUTH",
    default=None,
    documentation=DocumentationParams(
        help_text="Require authentication to access the Products section.",
        group="Setup-configuration",
    ),
)
CMS_PRODUCTS_REQUIRES_AUTH_BSN_OR_KVK = config(
    "CMS_PRODUCTS_REQUIRES_AUTH_BSN_OR_KVK",
    default=None,
    documentation=DocumentationParams(
        help_text="Require BSN or KvK identification to access the Products section.",
        group="Setup-configuration",
    ),
)
CMS_PRODUCTS_MENU_INDICATOR = config(
    "CMS_PRODUCTS_MENU_INDICATOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Show a notification indicator on the Products menu item.",
        group="Setup-configuration",
    ),
)
CMS_PRODUCTS_MENU_ICON = config(
    "CMS_PRODUCTS_MENU_ICON",
    default=None,
    documentation=DocumentationParams(
        help_text="Icon shown next to the Products item in the navigation menu.",
        group="Setup-configuration",
    ),
)

# profile app enable
CMS_CONFIG_PROFILE_ENABLE = config(
    "CMS_CONFIG_PROFILE_ENABLE",
    default=False,
    documentation=DocumentationParams(
        help_text="Enable setup-configuration for the Profile CMS app.",
        group="Setup-configuration",
    ),
)
# procile config
CMS_PROFILE_MY_DATA = config(
    "CMS_PROFILE_MY_DATA",
    default=None,
    documentation=DocumentationParams(
        help_text="Show the 'My data' section on the profile page.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_SELECTED_CATEGORIES = config(
    "CMS_PROFILE_SELECTED_CATEGORIES",
    default=None,
    documentation=DocumentationParams(
        help_text="Show selected theme categories on the profile page.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_MENTORS = config(
    "CMS_PROFILE_MENTORS",
    default=None,
    documentation=DocumentationParams(
        help_text="Show assigned mentors on the profile page.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_MY_CONTACTS = config(
    "CMS_PROFILE_MY_CONTACTS",
    default=None,
    documentation=DocumentationParams(
        help_text="Show personal contacts on the profile page.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_SELFDIAGNOSE = config(
    "CMS_PROFILE_SELFDIAGNOSE",
    default=None,
    documentation=DocumentationParams(
        help_text="Show the self-diagnose questionnaire link on the profile page.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_ACTIONS = config(
    "CMS_PROFILE_ACTIONS",
    default=None,
    documentation=DocumentationParams(
        help_text="Show tasks and actions on the profile page.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_NOTIFICATIONS = config(
    "CMS_PROFILE_NOTIFICATIONS",
    default=None,
    documentation=DocumentationParams(
        help_text="Show notification preferences on the profile page.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_QUESTIONS = config(
    "CMS_PROFILE_QUESTIONS",
    default=None,
    documentation=DocumentationParams(
        help_text="Show submitted questions on the profile page.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_SSD = config(
    "CMS_PROFILE_SSD",
    default=None,
    documentation=DocumentationParams(
        help_text="Show benefits (SSD) data on the profile page.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_NEWSLETTERS = config(
    "CMS_PROFILE_NEWSLETTERS",
    default=None,
    documentation=DocumentationParams(
        help_text="Show newsletter subscriptions on the profile page.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_APPOINTMENTS = config(
    "CMS_PROFILE_APPOINTMENTS",
    default=None,
    documentation=DocumentationParams(
        help_text="Show appointments on the profile page.",
        group="Setup-configuration",
    ),
)
# profile common extension
CMS_PROFILE_REQUIRES_AUTH = config(
    "CMS_PROFILE_REQUIRES_AUTH",
    default=None,
    documentation=DocumentationParams(
        help_text="Require authentication to access the Profile section.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_REQUIRES_AUTH_BSN_OR_KVK = config(
    "CMS_PROFILE_REQUIRES_AUTH_BSN_OR_KVK",
    default=None,
    documentation=DocumentationParams(
        help_text="Require BSN or KvK identification to access the Profile section.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_MENU_INDICATOR = config(
    "CMS_PROFILE_MENU_INDICATOR",
    default=None,
    documentation=DocumentationParams(
        help_text="Show a notification indicator on the Profile menu item.",
        group="Setup-configuration",
    ),
)
CMS_PROFILE_MENU_ICON = config(
    "CMS_PROFILE_MENU_ICON",
    default=None,
    documentation=DocumentationParams(
        help_text="Icon shown next to the Profile item in the navigation menu.",
        group="Setup-configuration",
    ),
)
