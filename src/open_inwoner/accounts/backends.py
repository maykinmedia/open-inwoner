from typing import NamedTuple, TypedDict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.urls import reverse

import structlog
from axes.backends import AxesBackend
from glom import Path, glom
from mozilla_django_oidc_db.backends import OIDCAuthenticationBackend
from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.registry import register as registry
from mozilla_django_oidc_db.typing import JSONObject
from oath import accept_totp

from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.hash import generate_email_from_string
from open_inwoner.utils.views import LogMixin

from .choices import LoginTypeChoices
from .models import User
from .oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
    OIDC_EIDAS_IDENTIFIER,
)

logger = structlog.stdlib.get_logger(__name__)


class UserModelEmailBackend(ModelBackend):
    """
    Authentication backend for login with email address.
    """

    def authenticate(
        self, request, username=None, password=None, user=None, token=None, **kwargs
    ):
        config = SiteConfiguration.get_solo()
        User = get_user_model()
        if username and password and not config.login_2fa_sms:
            try:
                user = User.objects.get(
                    email__iexact=username,
                    login_type=LoginTypeChoices.default,
                )
                if check_password(
                    password, user.password
                ) and self.user_can_authenticate(user):
                    return user
            except User.MultipleObjectsReturned:
                # Found multiple users with this email (shouldn't happen if we added checks)
                # Run the default password hasher once to reduce the timing
                # difference between an existing and a nonexistent user (#20760).
                User().set_password(password)
                return None
            except User.DoesNotExist:
                # No user was found, return None - triggers default login failed
                # Run the default password hasher once to reduce the timing
                # difference between an existing and a nonexistent user (#20760).
                User().set_password(password)
                return None

        # 2FA with sms verification
        if config.login_2fa_sms and user and token:
            accepted, drift = accept_totp(
                key=user.seed,
                response=token,
                period=getattr(settings, "ACCOUNTS_USER_TOKEN_EXPIRE_TIME", 300),
            )
            if not accepted:
                return None

            return user


class CustomAxesBackend(AxesBackend):
    def authenticate(self, request=None, *args, **kwargs):
        if request:
            return super().authenticate(request, *args, **kwargs)


class CustomOIDCBackend(OIDCAuthenticationBackend):
    def _check_candidate_backend(self) -> bool:
        if self.config.identifier != OIDC_ADMIN_CONFIG_IDENTIFIER:
            return False

        if self.request and SiteConfiguration.get_solo().openid_enabled_for_admin:
            # oidc_login_next still drives the post-login redirect: the upstream
            # OIDCAuthenticationCallbackView.success_url reads it from the session.
            self.request.session["oidc_login_next"] = reverse("admin:index")

        return super()._check_candidate_backend()

    def _extract_username(self, claims: JSONObject) -> str:
        return registry[OIDC_ADMIN_CONFIG_IDENTIFIER].get_username(claims)

    def create_user(self, claims):
        """
        Return object for a newly created user account.

        before we got here we already checked for existing users based on the overriden queryset from the .filter_users_by_claims()
        """
        unique_id = self._extract_username(claims)

        if "email" in claims:
            email = claims["email"]
        else:
            email = generate_email_from_string(unique_id)

        existing_user = self.UserModel.objects.filter(
            email__iexact=email,
            login_type=LoginTypeChoices.default,
            is_active=True,
        ).first()
        if existing_user:
            logger.debug(
                "Updating OIDC user with email",
                oidc_id=unique_id,
                email=email,
            )
            existing_user.oidc_id = unique_id
            existing_user.login_type = LoginTypeChoices.oidc
            # TODO verify we want unusable_password
            existing_user.set_unusable_password()
            existing_user.save()
            # Ensure `make_user_staff` is used
            self.update_user(existing_user, claims)
            return existing_user
        else:
            logger.debug("Creating OIDC user", oidc_id=unique_id)

            kwargs = {
                "oidc_id": unique_id,
                "email": email,
                "login_type": LoginTypeChoices.oidc,
            }
            user = self.UserModel.objects.create_user(**kwargs)
            # Ensure `make_user_staff` is used
            self.update_user(user, claims)
            # TODO verify we want unusable_password
            user.set_unusable_password()
            # Saving after using `set_unusable_password` is required, otherwise the user
            # will not actually be authenticated, see: https://taiga.maykinmedia.nl/project/open-inwoner/issue/2101
            user.save()

            return user

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified subject."""
        unique_id = self._extract_username(claims)

        if not unique_id:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(**{"oidc_id__iexact": unique_id})


class DigiDOIDCBackend(LogMixin, OIDCAuthenticationBackend):
    OIP_UNIQUE_ID_USER_FIELDNAME = "bsn"
    OIP_LOGIN_TYPE = LoginTypeChoices.digid

    def _check_candidate_backend(self) -> bool:
        # Check the identifier first: only defer to the parent (which validates
        # the plugin settings and reads `enabled`) when this config is ours.
        return (
            self.config.identifier == OIDC_DIGID_IDENTIFIER
            and super()._check_candidate_backend()
        )

    def _extract_username(self, claims: JSONObject) -> str:
        claim_path = self.config.options["identity_settings"]["bsn_claim_path"]
        return glom(claims, Path(*claim_path), default="")

    def verify_claims(self, claims: JSONObject) -> bool:
        # The generic backend delegates verify_claims to the plugin, but our
        # plugins are thin (schema/callback only) and the user logic lives here.
        # Authentication may proceed iff the BSN claim is present.
        return bool(self._extract_username(claims))

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified subject."""
        unique_id = self._extract_username(claims)

        if not unique_id:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(
            **{f"{self.OIP_UNIQUE_ID_USER_FIELDNAME}__iexact": unique_id}
        )

    def create_user(self, claims):
        """
        Return object for a newly created user account.
        """

        unique_id = self._extract_username(claims)

        logger.debug("Creating OIDC user", oidc_id=unique_id)

        user = self.UserModel.objects.create_user(
            **{
                self.UserModel.USERNAME_FIELD: generate_email_from_string(
                    unique_id, domain="localhost"
                ),
                self.OIP_UNIQUE_ID_USER_FIELDNAME: unique_id,
                "login_type": self.OIP_LOGIN_TYPE,
            }
        )

        return user

    def update_user(self, user: AbstractUser, claims: JSONObject):
        # BSN doesn't change, nothing to update.
        return user


class KvkEntityInformation(NamedTuple):
    kvk: str
    vestigingsnummer: str | None


class EHerkenningOIDCBackend(LogMixin, OIDCAuthenticationBackend):
    OIP_UNIQUE_ID_USER_FIELDNAME = "kvk"
    OIP_LOGIN_TYPE = LoginTypeChoices.eherkenning

    def _check_candidate_backend(self) -> bool:
        return (
            self.config.identifier == OIDC_EH_IDENTIFIER
            and super()._check_candidate_backend()
        )

    def verify_claims(self, claims: JSONObject) -> bool:
        # See DigiDOIDCBackend.verify_claims. Authentication may proceed iff the
        # legal subject (KvK/RSIN) claim is present.
        identity_settings = self.config.options["identity_settings"]
        legal_subject = glom(
            claims,
            Path(*identity_settings["legal_subject_claim_path"]),
            default=None,
        )
        return bool(legal_subject)

    def _get_kvk_entity_information_from_claims(
        self, claims: JSONObject
    ) -> KvkEntityInformation | None:
        """Get company vestigingsnummer from OIDC claims & store in session"""
        identity_settings = self.config.options["identity_settings"]

        vestigingsnummer = glom(
            claims,
            Path(*identity_settings["branch_number_claim_path"]),
            default=None,
        )
        kvk_or_rsin = glom(
            claims,
            Path(*identity_settings["legal_subject_claim_path"]),
            default=None,
        )
        identifier_type = glom(
            claims,
            Path(*identity_settings["identifier_type_claim_path"]),
            default=None,
        )

        if not kvk_or_rsin:
            raise SuspiciousOperation(
                "Claims did not include a value for the configured legal subject claim"
            )

        # TODO: The user may be using a broker which provides RSIN rather than KvK,
        # a scenario for which we are not equipped. Our usual model just assumes that
        # the identifier claim is KvK, even if it's actually an RSIN. This is hard to
        # check for, because there is no fixed convention as to the naming of the OIDC
        # claims. In theory, they should match the SAML claims verbatim:
        #
        #   urn:etoegang:1.9:EntityConcernedID:KvKnr
        #   urn:etoegang:1.9:EntityConcernedID:RSIN
        #
        # But there is no guarantee this mapping will be used, so it's difficult to
        # raise confidently. Instead, for now, we log this so we can detect it early.
        #
        # The proper solution would be to directly support RSIN as the identifier, hence
        # the TODO.
        if identifier_type and "kvk" not in identifier_type.lower():
            # TODO: We don't really support this
            logger.warning(
                "eHerkenning OIDC backend possibly configured to use an identifier "
                "type claim which does not point to KvK",
                identifier_type=identifier_type,
            )

        return KvkEntityInformation(kvk=kvk_or_rsin, vestigingsnummer=vestigingsnummer)

    def _log_successful_authenticate(self, user: User):
        log_msg = (
            f"Successful OIDC eHerkenning login for kvk/rsin={user.kvk} and "
            f"vestiging={user.vestiging}"
        )
        self.log_system_action(log_msg)

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified subject."""
        entity_info = self._get_kvk_entity_information_from_claims(claims)
        if not entity_info:
            return self.UserModel.objects.none()

        return self.UserModel.eherkenning_objects.filter_by_kvk_and_vestiging(
            kvk=entity_info.kvk, vestiging=entity_info.vestigingsnummer
        )

    def _persist_eherkenning_params_to_session(self, user):
        session_context = EHerkenningSessionContext(self.request)
        session_context.persist_eherkenning_state_for_user(
            user=user,
            # If a branch claim was provided, mark the session as restricted and
            # set the branchs selection flag to done so we skip the selection form.
            is_branch_restricted=bool(user.vestiging),
            initial_branch_selection_done=bool(user.vestiging),
        )

    def create_user(self, claims):
        """
        Return object for a newly created user account.

        Get vestigingsnummer from OIDC claims & store in session
        """

        entity_info = self._get_kvk_entity_information_from_claims(claims)
        if not entity_info:
            return None

        email_seed = entity_info.kvk + (entity_info.vestigingsnummer or "")
        create_kwargs = {
            self.UserModel.USERNAME_FIELD: generate_email_from_string(
                email_seed, domain="localhost"
            ),
            "login_type": self.OIP_LOGIN_TYPE,
            "kvk": entity_info.kvk,
        }

        if entity_info.vestigingsnummer:
            create_kwargs["vestiging"] = entity_info.vestigingsnummer

        user = self.UserModel.objects.create_user(**create_kwargs)
        self._persist_eherkenning_params_to_session(user)
        self._log_successful_authenticate(user)
        return user

    def update_user(self, user: AbstractUser, claims: JSONObject):
        self._persist_eherkenning_params_to_session(user)
        self._log_successful_authenticate(user)
        return user


class EIDASClaimValues(TypedDict):
    """Extracted claim values from eIDAS OIDC claims."""

    pseudo_id: str | None
    bsn: str | None
    company_name: str | None
    legal_entity_id: str | None
    first_name: str | None
    family_name: str | None


class EIDASOIDCBackend(LogMixin, OIDCAuthenticationBackend):
    def _check_candidate_backend(self) -> bool:
        return (
            self.config.identifier == OIDC_EIDAS_IDENTIFIER
            and super()._check_candidate_backend()
        )

    def verify_claims(self, claims: JSONObject) -> bool:
        # See DigiDOIDCBackend.verify_claims. Authentication may proceed iff the
        # pseudo identifier claim (required for all eIDAS logins) is present.
        identity_settings = self.config.options["identity_settings"]
        pseudo_id = glom(
            claims,
            Path(*identity_settings["legal_subject_pseudo_identifier_claim_path"]),
            default=None,
        )
        return bool(pseudo_id)

    def _extract_eidas_claim_values(self, claims: JSONObject) -> EIDASClaimValues:
        """
        Extract all eIDAS claim values from the claims dict.

        Returns a typed dictionary with all possible claim values (or None if not present).
        """
        identity_settings = self.config.options["identity_settings"]

        return EIDASClaimValues(
            pseudo_id=glom(
                claims,
                Path(*identity_settings["legal_subject_pseudo_identifier_claim_path"]),
                default=None,
            ),
            bsn=glom(
                claims,
                Path(*identity_settings["legal_subject_bsn_identifier_claim_path"]),
                default=None,
            ),
            company_name=glom(
                claims,
                Path(*identity_settings["company_name_claim_path"]),
                default=None,
            ),
            legal_entity_id=glom(
                claims,
                Path(*identity_settings["legal_entity_identifier_claim_path"]),
                default=None,
            ),
            first_name=glom(
                claims,
                Path(*identity_settings["legal_subject_first_name_claim_path"]),
                default=None,
            ),
            family_name=glom(
                claims,
                Path(*identity_settings["legal_subject_family_name_claim_path"]),
                default=None,
            ),
        )

    def _construct_user_creation_kwargs_from_claims(
        self, claims: JSONObject
    ) -> dict | None:
        """
        Extract user filter and create kwargs based on eIDAS claim patterns.
        """
        # Extract all claim values
        claim_values = self._extract_eidas_claim_values(claims)
        logger.info("eidas_oidc_claims_received", claim_keys=list(claims.keys()))

        # Validate presence of required pseudo_id
        if not claim_values["pseudo_id"]:
            msg = (
                "Claims did not include a value for the configured pseudo identifier claim. "
                "Pseudo identifier is required for all eIDAS authentications."
            )
            self.log_system_error(msg)
            raise SuspiciousOperation(msg)

        # Validate that at least one identifying claim is present (excluding pseudo_id).
        # This is mainly a matter of defensive programming: although there are required
        # attributes, these may nevertheless be missing due to e.g. missing scopes in
        # in the configuration. We catch that early and report an error.
        identifying_claims = {k: v for k, v in claim_values.items() if k != "pseudo_id"}

        if not any(identifying_claims.values()):
            logger.error(
                "eIDAS claims did not contain any identifying information",
                claim_values=claim_values,
                available_claim_keys=list(claims.keys()),
            )

            raise SuspiciousOperation(
                "eIDAS claims did not contain any identifying information. "
                "Expected at least one of: BSN, company name + legal entity ID, or first/family name. "
                f"Available claim keys: {', '.join(claims.keys())}. "
                f"Check the claim path configuration in the admin."
            )

        base_create_kwargs = {
            "eidas_pseudo_id": claim_values["pseudo_id"],
            "email": generate_email_from_string(
                claim_values["pseudo_id"], domain="localhost"
            ),
        }

        # Try company first, as the required fields are unambiguous
        has_company_name = bool(claim_values["company_name"])
        has_legal_entity = bool(claim_values["legal_entity_id"])
        if has_company_name or has_legal_entity:
            if not (has_company_name and has_legal_entity):
                raise SuspiciousOperation(
                    "eIDAS company claims must include both company name and legal entity ID. "
                    f"Received: company_name={'present' if has_company_name else 'missing'}, "
                    f"legal_entity_id={'present' if has_legal_entity else 'missing'}."
                )

            return base_create_kwargs | {
                "login_type": LoginTypeChoices.eidas_company,
                "company_name": claim_values["company_name"],
                "eidas_company_id": claim_values["legal_entity_id"],
            }

        # Assume this is a person
        person_kwargs = base_create_kwargs | {
            "login_type": LoginTypeChoices.eidas_person_pseudo_id,
            "first_name": claim_values["first_name"] or "",
            "last_name": claim_values["family_name"] or "",
        }

        # Do we have a BSN? If so, add it and update login type to reflect this
        if claim_values["bsn"]:
            person_kwargs = person_kwargs | {
                "bsn": claim_values["bsn"],
                "login_type": LoginTypeChoices.eidas_person_bsn,
            }

        return person_kwargs

    def filter_users_by_claims(self, claims):
        claim_values = self._extract_eidas_claim_values(claims)
        if not claim_values["pseudo_id"]:
            return User.objects.none()

        return User.objects.filter(eidas_pseudo_id=claim_values["pseudo_id"])

    def create_user(self, claims: JSONObject):
        if not (
            create_kwargs := self._construct_user_creation_kwargs_from_claims(claims)
        ):
            return None

        logger.info(
            "Creating new eIDAS user", pseudo_id=create_kwargs["eidas_pseudo_id"]
        )
        user = User.objects.create_user(**create_kwargs)

        return user

    def update_user(self, user: User, claims: JSONObject):
        if not (
            create_kwargs := self._construct_user_creation_kwargs_from_claims(claims)
        ):
            return None

        for attr, val in create_kwargs.items():
            setattr(user, attr, val)

        try:
            user.full_clean()
        except ValidationError as exc:
            raise SuspiciousOperation(
                "Unable to update user due to a validation error"
            ) from exc
        else:
            logger.info(
                "Updating eIDAS user", pseudo_id=create_kwargs["eidas_pseudo_id"]
            )
            user.save()
        return user
