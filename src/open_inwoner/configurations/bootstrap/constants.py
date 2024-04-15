from mozilla_django_oidc_db.models import UserInformationClaimsSources
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from open_inwoner.openzaak.models import generate_default_file_extensions

from .utils import generate_api_fields_from_template

CONFIDENTIALITY_CHOICES = [
    choice[0] for choice in VertrouwelijkheidsAanduidingen.choices
]
FILE_EXTENSION_CHOICES = [ext for ext in generate_default_file_extensions()]
USER_INFO_CLAIM_SOURCES_CHOICES = [
    choice[0] for choice in UserInformationClaimsSources.choices
]


siteconfig_fields = {
    "name": {"values": "string"},
    "primary_color": {"values": "string"},
    "secondary_color": {"values": "string"},
    "accent_color": {"values": "string"},
    "primary_font_color": {"values": "string"},
    "secondary_font_color": {"values": "string"},
    "accent_font_color": {"values": "string"},
    "warning_banner_enabled": {"values": "True, False"},
    "warning_banner_text": {"values": "string"},
    "warning_banner_background_color": {"values": "string"},
    "warning_banner_font_color": {"values": "string"},
    "login_show": {"values": "True, False"},
    "login_allow_registration": {"values": "True, False"},
    "login_2fa_sms": {"values": "True, False"},
    "login_text": {"values": "string"},
    "registration_text": {"values": "string"},
    "home_welcome_title": {"values": "string"},
    "home_welcome_intro": {"values": "string"},
    "home_theme_title": {"values": "string"},
    "home_theme_intro": {"values": "string"},
    "theme_title": {"values": "string"},
    "theme_intro": {"values": "string"},
    "home_map_title": {"values": "string"},
    "home_map_intro": {"values": "string"},
    "home_questionnaire_title": {"values": "string"},
    "home_questionnaire_intro": {"values": "string"},
    "home_product_finder_title": {"values": "string"},
    "home_product_finder_intro": {"values": "string"},
    "select_questionnaire_title": {"values": "string"},
    "select_questionnaire_intro": {"values": "string"},
    "plans_intro": {"values": "string"},
    "plans_no_plans_message": {"values": "string"},
    "plans_edit_message": {"values": "string"},
    "footer_logo_title": {"values": "string"},
    "footer_logo_url": {"values": "string (URL)"},
    "home_help_text": {"values": "string"},
    "theme_help_text": {"values": "string"},
    "product_help_text": {"values": "string"},
    "search_help_text": {"values": "string"},
    "account_help_text": {"values": "string"},
    "questionnaire_help_text": {"values": "string"},
    "plan_help_text": {"values": "string"},
    "search_filter_categories": {"values": "True, False"},
    "search_filter_tags": {"values": "True, False"},
    "search_filter_organizations": {"values": "True, False"},
    "email_new_message": {"values": "True, False"},
    "recipients_email_digest": {
        "values": "string, comma-delimited (e.g. 'user1@test.nl, user2@test.nl'"
    },
    "contact_phonenumber": {"values": "string"},
    "contact_page": {"values": "string (URL)"},
    "gtm_code": {"values": "string"},
    "ga_code": {"values": "string"},
    "matomo_url": {"values": "string (URL)"},
    "matomo_site_id": {"values": "string"},
    "siteimprove_id": {"values": "string"},
    "cookie_info_text": {"values": "string"},
    "cookie_link_text": {"values": "string"},
    "cookie_link_url": {"values": "string"},
    "kcm_survey_link_text": {"values": "string"},
    "kcm_survey_link_url": {"values": "string (URL)"},
    "openid_connect_login_text": {"values": "string"},
    "openid_display": {"values": "string"},
    "redirect_to": {"values": "string (URL)"},
    "allow_messages_file_sharing": {"values": "True, False"},
    "hide_categories_from_anonymous_users": {"values": "True, False"},
    "hide_search_from_anonymous_users": {"values": "True, False"},
    "display_social": {"values": "True, False"},
    "eherkenning_enabled": {"values": "True, False"},
}


#
# KIC config
#
kic_fields = {
    "register_email": {
        "values": "string (Email)",
    },
    "register_contact_moment": {
        "values": "True, False",
    },
    "register_bronorganisatie_rsin": {
        "values": "string",
    },
    "register_channel": {
        "values": "string",
    },
    "register_type": {
        "values": "string",
    },
    "register_employee_id": {
        "values": "string",
    },
    "use_rsin_for_innNnpId_query_parameter": {
        "values": "True, False",
    },
}

klanten_api_fields = generate_api_fields_from_template("klanten_api")
contactmomenten_api_fields = generate_api_fields_from_template("contactmomenten_api")

#
# ZGW config
#
zgw_fields = {
    "zaak_max_confidentiality": {
        "values": ",".join(CONFIDENTIALITY_CHOICES),
    },
    "document_max_confidentiality": {
        "values": ",".join(CONFIDENTIALITY_CHOICES),
    },
    "allowed_file_extensions": {
        "values": ",".join(FILE_EXTENSION_CHOICES),
    },
    "skip_notification_statustype_informeren": {
        "values": "True, False",
    },
    "reformat_esuite_zaak_identificatie": {
        "values": "True, False",
    },
    "fetch_eherkenning_zaken_with_rsin": {
        "values": "True, False",
    },
    "title_text": {
        "values": "True, False",
    },
    "enable_categories_filtering_with_zaken": {
        "values": "True, False",
    },
    "action_required_deadline_days": {
        "values": "string (number)",
    },
}

zaak_api_fields = generate_api_fields_from_template("zaak_api")
catalogi_api_fields = generate_api_fields_from_template("catalogi_api")
documenten_api_fields = generate_api_fields_from_template("documenten_api")
formulieren_api_fields = generate_api_fields_from_template("formulieren_api")


#
# DigiD OIDC
#
digid_oidc_fields = {
    "enabled": {
        "values": "True, False",
    },
    "identifier_claim_name": {
        "values": "string",
    },
    "oidc_rp_scopes_list": {
        "values": "string, comma-delimited (i.e. 'foo,bar,baz')",
    },
    "oidc_rp_client_id": {
        "values": "string",
    },
    "oidc_rp_client_secret": {
        "values": "string",
    },
    "oidc_rp_sign_algo": {
        "values": "string",
    },
    "oidc_op_discovery_endpoint": {
        "values": "string (URL)",
    },
    "oidc_op_jwks_endpoint": {
        "values": "string (URL)",
    },
    "oidc_op_authorization_endpoint": {
        "values": "string (URL)",
    },
    "oidc_op_token_endpoint": {
        "values": "string (URL)",
    },
    "oidc_op_user_endpoint": {
        "values": "string (URL)",
    },
    "oidc_rp_idp_sign_key": {
        "values": "string",
    },
    "oidc_use_nonce": {
        "values": "True, False",
    },
    "oidc_nonce_size": {
        "values": "string (positive integer)",
    },
    "oidc_state_size": {
        "values": "string (positive integer)",
    },
    "oidc_exempt_urls": {
        "values": "string, comma-delimited ('foo,bar,baz')",
    },
    "userinfo_claims_source": {
        "values": ",".join(USER_INFO_CLAIM_SOURCES_CHOICES),
    },
    "oidc_op_logout_endpoint": {
        "values": "string (URL)",
    },
    "error_message_mapping": {
        "values": "JSON ({'key':'value'})",
    },
    "oidc_keycloak_idp_hint": {
        "values": "string",
    },
}


#
# eHerkenning OIDC
#
eherkenning_oidc_fields = digid_oidc_fields
