from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import (
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _

from open_inwoner.utils.views import LogMixin


class LogPasswordChangeView(LogMixin, PasswordChangeView):
    def form_valid(self, form):
        response = super().form_valid(form)

        object = self.request.user
        self.log_user_action(object, _("password was changed"))
        return response


class LogPasswordResetView(LogMixin, PasswordResetView):
    def form_valid(self, form):
        self.log_system_action(_("password reset was accessed"))
        return super().form_valid(form)


class LogPasswordResetConfirmView(LogMixin, PasswordResetConfirmView):
    def form_valid(self, form):
        response = super().form_valid(form)

        object = self.get_user(self.kwargs["uidb64"])
        self.log_system_action(_("password reset was completed"), object)
        return response
