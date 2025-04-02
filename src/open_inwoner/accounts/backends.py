import logging
from typing import Literal, NamedTuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import SuspiciousOperation
from django.urls import reverse, reverse_lazy

from axes.backends import AxesBackend
from digid_eherkenning.oidc.backends import BaseBackend
from glom import Path, glom
from mozilla_django_oidc_db.backends import OIDCAuthenticationBackend
from mozilla_django_oidc_db.config import dynamic_setting
from mozilla_django_oidc_db.models import OpenIDConnectConfig
from mozilla_django_oidc_db.typing import JSONObject
from oath import accept_totp

from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.hash import generate_email_from_string
from open_inwoner.utils.views import LogMixin

from .choices import LoginTypeChoices
from .models import OpenIDDigiDConfig, OpenIDEHerkenningConfig, User

logger = logging.getLogger(__name__)


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
    callback_path = reverse_lazy("oidc_authentication_callback")

    def _check_candidate_backend(self) -> bool:
        parent = super()._check_candidate_backend()
        return parent and self.config_class is OpenIDConnectConfig

    def authenticate(self, request, *args, **kwargs):
        # Avoid attempting OIDC for a specific variant if we know that that is not the
        # correct variant being attempted
        # XXX, TODO, check the config class rather than the path once there's
        # a single callback URL. We can override ``_check_candidate_backend``.
        if request and request.path != self.callback_path:
            return

        config = SiteConfiguration.get_solo()
        if request and config.openid_enabled_for_admin:
            request.session["oidc_login_next"] = reverse("admin:index")

        return super().authenticate(request, *args, **kwargs)

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
            logger.debug("Updating OIDC user: %s with email %s", unique_id, email)
            existing_user.oidc_id = unique_id
            existing_user.login_type = LoginTypeChoices.oidc
            # TODO verify we want unusable_password
            existing_user.set_unusable_password()
            existing_user.save()
            # Ensure `make_user_staff` is used
            self.update_user(existing_user, claims)
            return existing_user
        else:
            logger.debug("Creating OIDC user: %s", unique_id)

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


class DigiDOIDCBackend(LogMixin, BaseBackend):
    OIP_UNIQUE_ID_USER_FIELDNAME = dynamic_setting[Literal["bsn"]]()
    OIP_LOGIN_TYPE = dynamic_setting[LoginTypeChoices]()

    def _check_candidate_backend(self) -> bool:
        parent = super()._check_candidate_backend()
        return parent and self.config_class is OpenIDDigiDConfig

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

        logger.debug("Creating OIDC user: %s", unique_id)

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


class KvkEntityInformation(NamedTuple):
    kvk: str
    vestigingsnummer: str | None


class EHerkenningOIDCBackend(LogMixin, BaseBackend):
    OIP_UNIQUE_ID_USER_FIELDNAME = dynamic_setting[Literal["kvk"]]()
    OIP_LOGIN_TYPE = dynamic_setting[LoginTypeChoices]()

    def _check_candidate_backend(self) -> bool:
        parent = super()._check_candidate_backend()
        return parent and self.config_class is OpenIDEHerkenningConfig

    def _get_kvk_entity_information_from_claims(
        self, claims: JSONObject
    ) -> KvkEntityInformation | None:
        """Get company vestigingsnummer from OIDC claims & store in session"""
        eherkenning_config = self.config_class.get_solo()

        vestigingsnummer = glom(
            claims, Path(*eherkenning_config.branch_number_claim), default=None
        )
        kvk_or_rsin = glom(
            claims, Path(*eherkenning_config.legal_subject_claim), default=None
        )
        identifier_type = glom(
            claims, Path(*eherkenning_config.identifier_type_claim), default=None
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
                extra={"identifier_type": identifier_type},
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
        return super().update_user(user, claims)
