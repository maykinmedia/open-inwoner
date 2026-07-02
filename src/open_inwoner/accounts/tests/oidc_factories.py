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
# Individual tests can still override e.g.
# ``options__identity_settings__bsn_claim_path=["absent"]``.
DIGID_IDENTITY_SETTINGS = {"bsn_claim_path": ["bsn"]}
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


class OIDCClientFactory(_OIDCClientFactory):
    """
    Extends the upstream factory with open_inwoner's flow-specific traits.

    Inspired by Open Forms' OFOIDCClientFactory. Each trait pins the identifier
    to the matching registered plugin and provides a sensible default options
    payload. Example:

        OIDCClientFactory(with_digid=True)
        OIDCClientFactory(with_eherkenning=True, enabled=False)
        OIDCClientFactory(
            with_eidas=True,
            options__identity_settings__legal_subject_bsn_identifier_claim_path=["x"],
        )
    """

    class Params:
        with_admin = factory.Trait(
            identifier=OIDC_ADMIN_CONFIG_IDENTIFIER,
            enabled=True,
            with_admin_options=True,
        )
        with_digid = factory.Trait(
            identifier=OIDC_DIGID_IDENTIFIER,
            enabled=True,
            options=factory.LazyFunction(lambda: _options(DIGID_IDENTITY_SETTINGS)),
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
