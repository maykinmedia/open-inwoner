import logging

from django.urls import reverse_lazy

from mozilla_django_oidc_db.backends import OIDCAuthenticationBackend as BaseBackend
from solo.models import SingletonModel

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.utils.hash import generate_email_from_string

from .models import OpenIDConnectDigiDConfig, OpenIDConnectEHerkenningConfig

logger = logging.getLogger(__name__)


class OIDCAuthenticationBackend(BaseBackend):
    callback_path = None
    unique_id_user_fieldname = ""

    login_type: LoginTypeChoices
    _config_class: type[SingletonModel]

    def authenticate(self, request, *args, **kwargs):
        # Avoid attempting OIDC for a specific variant if we know that that is not the
        # correct variant being attempted
        if request and request.path != self.callback_path:
            return

        # XXX: Sanity check while we still work with subclasses.
        assert request._oidcdb_config_class is self._config_class

        return super().authenticate(request, *args, **kwargs)

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified subject."""
        unique_id = self._extract_username(claims)

        if not unique_id:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(
            **{f"{self.unique_id_user_fieldname}__iexact": unique_id}
        )

    def create_user(self, claims):
        """Return object for a newly created user account."""

        unique_id = self._extract_username(claims)

        logger.debug("Creating OIDC user: %s", unique_id)

        user = self.UserModel.objects.create_user(
            **{
                self.UserModel.USERNAME_FIELD: generate_email_from_string(
                    unique_id, domain="localhost"
                ),
                self.unique_id_user_fieldname: unique_id,
                "login_type": self.login_type,
            }
        )

        return user

    def update_user(self, user, claims):
        # TODO should we do anything here? or do we only fetch data from HaalCentraal
        return user


class OIDCAuthenticationDigiDBackend(OIDCAuthenticationBackend):
    """
    Allows logging in via OIDC with DigiD
    """

    _config_class = OpenIDConnectDigiDConfig

    login_type = LoginTypeChoices.digid
    callback_path = reverse_lazy("digid_oidc:callback")
    unique_id_user_fieldname = "bsn"


class OIDCAuthenticationEHerkenningBackend(OIDCAuthenticationBackend):
    """
    Allows logging in via OIDC with eHerkenning
    """

    _config_class = OpenIDConnectEHerkenningConfig

    login_type = LoginTypeChoices.eherkenning
    callback_path = reverse_lazy("eherkenning_oidc:callback")
    unique_id_user_fieldname = "kvk"
