from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.views import (
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.utils.translation import gettext as _

from open_inwoner.utils.views import LogMixin

from ..choices import LoginTypeChoices
from ..forms import CustomPasswordResetForm


class LogPasswordChangeView(UserPassesTestMixin, LogMixin, PasswordChangeView):
    def test_func(self):
        if self.request.user.is_authenticated:
            return self.request.user.login_type == LoginTypeChoices.default
        return False

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse("root"))

        return super().handle_no_permission()

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
