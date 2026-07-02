from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.schemas import get_loa_mapping_schema

from .constants import EIDASAssuranceLevels

# Open Inwoner handles both natural persons and companies through a single
# eIDAS flow/backend (see EIDASOIDCBackend), so unlike DigiD/eHerkenning this
# is one combined schema rather than a person/company split.
EIDAS_OPTIONS_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Options",
    "description": _("OIDC eIDAS Configuration options."),
    "type": "object",
    "required": ["identity_settings"],
    "properties": {
        "loa_settings": {
            "title": _("LoA settings"),
            "description": _("Level of Assurance related settings."),
            "type": "object",
            "properties": {
                "claim_path": {
                    "title": _("Claim path"),
                    "description": _(
                        "Path to the claim value holding the level of assurance. If left empty, it is "
                        "assumed there is no LOA claim and the configured fallback value will be "
                        "used."
                    ),
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "default": {
                    "title": _("Default"),
                    "description": _(
                        "Fallback level of assurance, in case no claim value could be extracted."
                    ),
                    "type": "string",
                    "choices": [
                        {"title": label, "value": value}
                        for value, label in EIDASAssuranceLevels.choices
                    ],
                },
                "value_mapping": get_loa_mapping_schema(EIDASAssuranceLevels),
            },
        },
        "identity_settings": {
            "title": _("Identity settings"),
            "description": _("eIDAS identity settings."),
            "type": "object",
            "required": ["legal_subject_pseudo_identifier_claim_path"],
            "properties": {
                "legal_subject_pseudo_identifier_claim_path": {
                    "title": _("Legal subject pseudo identifier claim path"),
                    "description": _(
                        "Path to the claim value holding the pseudo identifier of "
                        "the authenticated user. Required for all eIDAS "
                        "authentications."
                    ),
                    "default": ["urn:etoegang:1.12:EntityConcernedID:PseudoID"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "legal_subject_bsn_identifier_claim_path": {
                    "title": _("Legal subject bsn identifier claim path"),
                    "description": _(
                        "Path to the claim value holding the BSN of the "
                        "authenticated user, if the subject has connected their "
                        "BSN to their eIDAS identity."
                    ),
                    "default": ["urn:etoegang:1.12:EntityConcernedID:BSN"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "legal_subject_first_name_claim_path": {
                    "title": _("Legal subject first name claim path"),
                    "description": _(
                        "Path to the claim value that holds the first/given name "
                        "of the authenticated user."
                    ),
                    "default": ["urn:etoegang:1.9:attribute:FirstName"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "legal_subject_family_name_claim_path": {
                    "title": _("Legal subject family name claim path"),
                    "description": _(
                        "Path to the claim value that holds the family "
                        "name/surname of the authenticated user."
                    ),
                    "default": ["urn:etoegang:1.9:attribute:FamilyName"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "legal_subject_date_of_birth_claim_path": {
                    "title": _("Legal subject date of birth claim path"),
                    "description": _(
                        "Path to the claim value that holds the date of birth of "
                        "the authenticated user."
                    ),
                    "default": ["urn:etoegang:1.9:attribute:DateOfBirth"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "legal_entity_identifier_claim_path": {
                    "title": _("Legal entity identifier claim path"),
                    "description": _(
                        "Path to the claim value holding the legal entity "
                        "identifier, for company authentications."
                    ),
                    "default": [
                        "urn:etoegang:1.11:EntityConcernedID:eIDASLegalIdentifier"
                    ],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "company_name_claim_path": {
                    "title": _("Company name claim path"),
                    "description": _(
                        "Path to the claim value that holds the company/"
                        "organization legal name, for company authentications."
                    ),
                    "default": ["urn:etoegang:1.11:attribute-represented:CompanyName"],
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
        },
    },
}
