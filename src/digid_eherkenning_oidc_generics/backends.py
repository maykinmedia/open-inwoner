import logging

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import SuspiciousOperation

from mozilla_django_oidc_db.backends import (
    OIDCAuthenticationBackend as _OIDCAuthenticationBackend,
)
from requests.exceptions import RequestException

from open_inwoner.accounts.choices import LoginTypeChoices

from .constants import DIGID_OIDC_AUTH_SESSION_KEY, EHERKENNING_OIDC_AUTH_SESSION_KEY
from .mixins import SoloConfigDigiDMixin, SoloConfigEHerkenningMixin

logger = logging.getLogger(__name__)


class OIDCAuthenticationBackend(_OIDCAuthenticationBackend):
    config_identifier_field = "identifier_claim_name"

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified subject."""
        identifier_claim_name = getattr(self.config, self.config_identifier_field)
        unique_id = self.retrieve_identifier_claim(claims)

        if not unique_id:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(
            **{f"{identifier_claim_name}__iexact": unique_id}
        )

    def create_user(self, claims):
        """Return object for a newly created user account."""
        identifier_claim_name = getattr(self.config, self.config_identifier_field)
        unique_id = self.retrieve_identifier_claim(claims)

        logger.debug("Creating OIDC user: %s", unique_id)

        user = self.UserModel.objects.create_user(
            **{
                self.UserModel.USERNAME_FIELD: "user-{}@localhost".format(unique_id),
                identifier_claim_name: unique_id,
                "login_type": self.login_type,
            }
        )

        return user

    def update_user(self, user, claims):
        # TODO should we do anything here? or do we only fetch data from HaalCentraal
        return user


class OIDCAuthenticationDigiDBackend(SoloConfigDigiDMixin, OIDCAuthenticationBackend):
    """
    Allows logging in via OIDC with DigiD
    """

    login_type = LoginTypeChoices.digid


class OIDCAuthenticationEHerkenningBackend(
    SoloConfigEHerkenningMixin, OIDCAuthenticationBackend
):
    """
    Allows logging in via OIDC with DigiD
    """

    login_type = LoginTypeChoices.eherkenning
