import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password

from axes.backends import AxesBackend
from mozilla_django_oidc_db.backends import OIDCAuthenticationBackend
from oath import accept_totp

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.hash import generate_email_from_string

from .choices import LoginTypeChoices

logger = logging.getLogger(__name__)


class UserModelEmailBackend(ModelBackend):
    """
    Authentication backend for login with email address.
    """

    def authenticate(
        self, request, username=None, password=None, user=None, token=None, **kwargs
    ):
        config = SiteConfiguration.get_solo()

        if username and password and not config.login_2fa_sms:
            try:
                user = get_user_model().objects.get(email__iexact=username)
                if check_password(password, user.password):
                    return user
            except get_user_model().DoesNotExist:
                # No user was found, return None - triggers default login failed
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
    def create_user(self, claims):
        """Return object for a newly created user account."""
        unique_id = self.retrieve_identifier_claim(claims)

        email = generate_email_from_string(unique_id)
        if "email" in claims:
            email = claims["email"]

        existing_user = self.UserModel.objects.filter(email__iexact=email).first()
        if existing_user:
            logger.debug("Updating OIDC user: %s with email %s", unique_id, email)
            existing_user.oidc_id = unique_id
            existing_user.login_type = LoginTypeChoices.oidc
            existing_user.save()
            return existing_user
        else:
            logger.debug("Creating OIDC user: %s", unique_id)

            kwargs = {
                "oidc_id": unique_id,
                "email": email,
                "login_type": LoginTypeChoices.oidc,
            }

            user = self.UserModel.objects.create_user(**kwargs)
            self.update_user(user, claims)

            return user

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified subject."""
        unique_id = self.retrieve_identifier_claim(claims)

        if not unique_id:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(**{"oidc_id__iexact": unique_id})
