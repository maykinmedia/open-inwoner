from mozilla_django_oidc_db.models import UserInformationClaimsSources
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    generate_default_file_extensions,
)

from .utils import generate_api_fields_from_template, populate_fields

CONFIDENTIALITY_LEVELS = [
    choice[0] for choice in VertrouwelijkheidsAanduidingen.choices
]
FILE_EXTENSIONS = [ext for ext in generate_default_file_extensions()]
USER_INFO_CLAIM_SOURCES = [choice[0] for choice in UserInformationClaimsSources.choices]


#
# SiteConfiguration
#
require = (
    "name",
    "primary_color",
    "secondary_color",
    "accent_color",
)
exclude = (
    "id",
    "email_logo",
    "footer_logo",
    "favicon",
    "openid_connect_logo",
    "extra_css",
    "logo",
    "hero_image_login",
    "theme_stylesheet",
)
all_fields = (
    field
    for field in SiteConfiguration._meta.concrete_fields
    if field.name not in exclude
)
siteconfig_fields = {
    "all": [],
    "required": [],
}

populate_fields(
    siteconfig_fields, require=require, exclude=exclude, all_fields=all_fields
)


#
# KIC config
#
klanten_api_fields = generate_api_fields_from_template("klanten_api")
contactmomenten_api_fields = generate_api_fields_from_template("contactmomenten_api")

require = (
    "register_type",
    "register_contact_moment",
    *klanten_api_fields.keys(),
    *contactmomenten_api_fields.keys(),
)
exclude = ("id", "klanten_service", "contactmomenten_service")
all_fields = (
    field
    for field in OpenKlantConfig._meta.concrete_fields
    if field.name not in exclude
)
kic_fields = {
    "all": [],
    "required": [
        "register_type",
        "register_contact_moment",
        *klanten_api_fields.keys(),
        *contactmomenten_api_fields.keys(),
    ],
}

populate_fields(kic_fields, require=None, exclude=exclude, all_fields=all_fields)


#
# ZGW config
#
zaak_api_fields = generate_api_fields_from_template("zaak_api")
catalogi_api_fields = generate_api_fields_from_template("catalogi_api")
documenten_api_fields = generate_api_fields_from_template("documenten_api")
formulieren_api_fields = generate_api_fields_from_template("formulieren_api")

exclude = ("id", "catalogi_service", "document_service", "form_service", "zaak_service")
all_fields = (
    field for field in OpenZaakConfig._meta.concrete_fields if field.name not in exclude
)
zgw_fields = {
    "all": [],
    "required": [
        *zaak_api_fields.keys(),
        *catalogi_api_fields.keys(),
        *documenten_api_fields.keys(),
        *formulieren_api_fields.keys(),
    ],
}

populate_fields(zgw_fields, require=None, exclude=exclude, all_fields=all_fields)


#
# DigiD OIDC
#
exclude = "id"
all_fields = (
    field
    for field in OpenIDConnectDigiDConfig._meta.concrete_fields
    if field.name not in exclude
)
digid_oidc_fields = {
    "all": [],
    "required": [
        "oidc_rp_client_id",
        "oidc_rp_client_secret",
    ],
}

populate_fields(digid_oidc_fields, require=None, exclude=exclude, all_fields=all_fields)


#
# eHerkenning OIDC
#
exclude = "id"
all_fields = (
    field
    for field in OpenIDConnectEHerkenningConfig._meta.concrete_fields
    if field.name not in exclude
)
eherkenning_oidc_fields = {
    "all": [],
    "required": [
        "oidc_rp_client_id",
        "oidc_rp_client_secret",
    ],
}

populate_fields(
    eherkenning_oidc_fields, require=None, exclude=exclude, all_fields=all_fields
)
