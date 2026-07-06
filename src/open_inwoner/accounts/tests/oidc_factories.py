import copy

import factory
from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.tests.factories import (
    OIDCClientFactory as _OIDCClientFactory,
)

from open_inwoner.accounts.oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
    OIDC_EIDAS_IDENTIFIER,
)

# Default claim paths per flow. These deliberately use the same simple claim
# keys that the test payloads send, so most tests need no per-field override.
EHERKENNING_IDENTITY_SETTINGS = {
    "identifier_type_claim_path": ["name_qualifier"],
    "legal_subject_claim_path": ["kvk"],
    "acting_subject_claim_path": ["acting_subject"],
    "branch_number_claim_path": ["vestigingsnummer"],
}
EIDAS_IDENTITY_SETTINGS = {
    "legal_subject_pseudo_identifier_claim_path": ["pseudo_id"],
    "legal_subject_bsn_identifier_claim_path": ["bsn"],
    "legal_subject_first_name_claim_path": ["first_name"],
    "legal_subject_family_name_claim_path": ["family_name"],
    "legal_subject_date_of_birth_claim_path": ["birthdate"],
    "legal_entity_identifier_claim_path": ["legal_entity"],
    "company_name_claim_path": ["company_name"],
}


def _options(identity_settings: dict) -> dict:
    # Fresh deep copy per instance so tests that mutate options don't leak into
    # the shared module-level defaults (DB rows roll back between tests, but
    # in-memory dicts do not).
    return {"identity_settings": copy.deepcopy(identity_settings)}


def _admin_options(*, make_users_staff: bool, first_name_claim: list | None) -> dict:
    # Built fresh per instance from the factory params below (rather than sharing
    # a module-level dict), so tests never need to mutate options in place.
    return {
        "user_settings": {
            "claim_mappings": {
                "username": ["sub"],
                "email": ["email"],
                "first_name": list(first_name_claim or []),
                "last_name": [],
            },
            "username_case_sensitive": False,
            "sensitive_claims": [],
        },
        "groups_settings": {
            "make_users_staff": make_users_staff,
            "sync": False,
            "sync_pattern": "*",
            "default_groups": [],
            "claim_mapping": [],
            "superuser_group_names": [],
        },
    }


class OIDCClientFactory(_OIDCClientFactory):
    """
    Extends the upstream factory with open_inwoner's flow-specific traits.

    Inspired by Open Forms' OFOIDCClientFactory. Each trait pins the identifier
    to the matching registered plugin and provides a sensible default options
    payload. Per-flow knobs (declared as Params) let tests tweak the config
    without mutating the options dict in place, e.g.:

        OIDCClientFactory(with_digid=True)
        OIDCClientFactory(with_digid=True, bsn_claim=["sub"])
        OIDCClientFactory(with_admin=True, make_users_staff=False)
        OIDCClientFactory(
            with_digid=True,
            oidc_provider__oidc_op_logout_endpoint="https://idp/logout",
        )
    """

    class Params:
        # Admin-flow knobs, only meaningful together with ``with_admin``.
        make_users_staff = True
        first_name_claim = None
        # DigiD-flow knob, only meaningful together with ``with_digid``.
        bsn_claim = ["bsn"]
        with_admin = factory.Trait(
            identifier=OIDC_ADMIN_CONFIG_IDENTIFIER,
            enabled=True,
            options=factory.LazyAttribute(
                lambda o: _admin_options(
                    make_users_staff=o.make_users_staff,
                    first_name_claim=o.first_name_claim,
                )
            ),
        )
        with_digid = factory.Trait(
            identifier=OIDC_DIGID_IDENTIFIER,
            enabled=True,
            options=factory.LazyAttribute(
                lambda o: {"identity_settings": {"bsn_claim_path": list(o.bsn_claim)}}
            ),
        )
        with_eherkenning = factory.Trait(
            identifier=OIDC_EH_IDENTIFIER,
            enabled=True,
            options=factory.LazyFunction(
                lambda: _options(EHERKENNING_IDENTITY_SETTINGS)
            ),
        )
        with_eidas = factory.Trait(
            identifier=OIDC_EIDAS_IDENTIFIER,
            enabled=True,
            options=factory.LazyFunction(lambda: _options(EIDAS_IDENTITY_SETTINGS)),
        )
