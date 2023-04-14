from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import (
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.translation import gettext as _

from digid_eherkenning.mock import conf
from digid_eherkenning.mock.views.digid import DigiDAssertionConsumerServiceMockView
from digid_eherkenning.views.base import get_redirect_url
from digid_eherkenning.views.digid import DigiDAssertionConsumerServiceView

from open_inwoner.utils.views import LogMixin

from ..choices import LoginTypeChoices
from ..forms import CustomPasswordResetForm


class LogPasswordChangeView(UserPassesTestMixin, LogMixin, PasswordChangeView):
    def test_func(self):
        if self.request.user.is_authenticated:
            return self.request.user.login_type == LoginTypeChoices.default
        return False

    def form_valid(self, form):
        response = super().form_valid(form)

        object = self.request.user
        self.log_user_action(object, _("password was changed"))
        return response


class LogPasswordResetView(LogMixin, PasswordResetView):
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        self.log_system_action(_("password reset was accessed"))
        return super().form_valid(form)


class LogPasswordResetConfirmView(LogMixin, PasswordResetConfirmView):
    def form_valid(self, form):
        response = super().form_valid(form)

        object = self.get_user(self.kwargs["uidb64"])
        self.log_system_action(_("password reset was completed"), object)
        return response


class CustomDigiDAssertionConsumerServiceMockView(
    DigiDAssertionConsumerServiceMockView
):
    def get_login_url(self):
        """
        where to go after unsuccessful login
        """
        invite_url = self.request.session.get("invite_url")
        next_url = self.request.GET.get("next")

        if (
            invite_url
            and next_url
            and reverse("profile:registration_necessary") in next_url
        ):
            # If user logs in via the invitation flow redirect to the invitation
            # accept view if login fails
            absolute_invite_url = self.request.build_absolute_uri(invite_url)
            return absolute_invite_url
        elif (
            invite_url
            and next_url
            and not reverse("profile:registration_necessary") in next_url
        ):
            del self.request.session["invite_url"]

        url = self.request.build_absolute_uri(conf.get_cancel_url())
        url = get_redirect_url(
            self.request, url, require_https=self.request.is_secure()
        )

        if url:
            return url

        if hasattr(settings, "DIGID"):
            digid_login_url = settings.DIGID.get("login_url")
            if digid_login_url:
                return resolve_url(digid_login_url)

        return resolve_url(settings.LOGIN_URL)

    def get_success_url(self):
        session = self.request.session

        # Remove invite url from user's session after successful digid login
        if "invite_url" in session.keys():
            del session["invite_url"]

        return super().get_success_url()


class CustomDigiDAssertionConsumerServiceView(DigiDAssertionConsumerServiceView):
    def get_login_url(self, **kwargs):
        invite_url = self.request.session.get("invite_url")
        next_url = self.request.GET.get("RelayState")

        if (
            invite_url
            and next_url
            and reverse("profile:registration_necessary") in next_url
        ):
            # If user logs in via the invitation flow redirect to the invitation
            # accept view if login fails
            absolute_invite_url = self.request.build_absolute_uri(invite_url)
            return absolute_invite_url
        elif (
            invite_url
            and next_url
            and not reverse("profile:registration_necessary") in next_url
        ):
            del self.request.session["invite_url"]
        url = self.get_redirect_url()
        if url:
            return url

        digid_login_url = settings.DIGID.get("login_url")
        if digid_login_url:
            return resolve_url(digid_login_url)

        return resolve_url(settings.LOGIN_URL)

    def get_success_url(self):
        session = self.request.session
        # Remove invite url from user's session after successful digid login
        if "invite_url" in session.keys():
            del session["invite_url"]

        return super().get_success_url()
