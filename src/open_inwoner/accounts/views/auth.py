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
        object = form.save()
        self.log_user_action(object, _("password was changed"))
        # Updating the password logs out all other sessions for the user
        # except the current one.
        update_session_auth_hash(self.request, form.user)
        return super().form_valid(form)


class LogPasswordResetView(LogMixin, PasswordResetView):
    def form_valid(self, form):
        self.log_system_action(_("password reset was accessed"))
        return super().form_valid(form)


class LogPasswordResetConfirmView(LogMixin, PasswordResetConfirmView):
    def form_valid(self, form):
        super().form_valid(form)
        object = self.get_user(self.kwargs["uidb64"])

        self.log_system_action(_("password reset was completed"), object)
        return HttpResponseRedirect(self.get_success_url())
