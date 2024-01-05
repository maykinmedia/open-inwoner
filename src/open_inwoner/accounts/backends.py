import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password
from django.urls import reverse_lazy

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

    def authenticate(self, request, *args, **kwargs):
        # Avoid attempting OIDC for a specific variant if we know that that is not the
        # correct variant being attempted
        if request and request.path != self.callback_path:
            return

        return super().authenticate(request, *args, **kwargs)

    def create_user(self, claims):
        """
        Return object for a newly created user account.

        before we got here we already checked for existing users based on the overriden queryset from the .filter_users_by_claims()
        """
        unique_id = self.retrieve_identifier_claim(claims)

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
            # TODO verify we want unusable_password
            user.set_unusable_password()

            return user

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified subject."""
        unique_id = self.retrieve_identifier_claim(claims)

        if not unique_id:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(**{"oidc_id__iexact": unique_id})
