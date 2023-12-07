import logging

from django.urls import reverse_lazy

from mozilla_django_oidc_db.backends import (
    OIDCAuthenticationBackend as _OIDCAuthenticationBackend,
)

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.utils.hash import generate_email_from_string

from .mixins import SoloConfigDigiDMixin, SoloConfigEHerkenningMixin

logger = logging.getLogger(__name__)


class OIDCAuthenticationBackend(_OIDCAuthenticationBackend):
    config_identifier_field = "identifier_claim_name"
    callback_path = None

    def authenticate(self, request, *args, **kwargs):
        # Avoid attempting OIDC for a specific variant if we know that that is not the
        # correct variant being attempted
        if request and request.path != self.callback_path:
            return

        return super().authenticate(request, *args, **kwargs)

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
                self.UserModel.USERNAME_FIELD: generate_email_from_string(
                    unique_id, domain="localhost"
                ),
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
    callback_path = reverse_lazy("digid_oidc:callback")


class OIDCAuthenticationEHerkenningBackend(
    SoloConfigEHerkenningMixin, OIDCAuthenticationBackend
):
    """
    Allows logging in via OIDC with eHerkenning
    """

    login_type = LoginTypeChoices.eherkenning
    callback_path = reverse_lazy("eherkenning_oidc:callback")
