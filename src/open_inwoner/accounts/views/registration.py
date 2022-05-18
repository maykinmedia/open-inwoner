from typing import Optional
from urllib.parse import unquote

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from django_registration.backends.one_step.views import RegistrationView

from open_inwoner.utils.views import LogMixin

from ..forms import CustomRegistrationForm
from ..models import Invite


class CustomRegistrationView(LogMixin, RegistrationView):
    form_class = CustomRegistrationForm

    def get_initial(self):
        initial = super().get_initial()

        invite = self.get_invite()
        if invite:
            initial.update(
                {
                    "invite": invite,
                    "email": invite.invitee_email,
                    "first_name": invite.contact.first_name,
                    "last_name": invite.contact.last_name,
                }
            )

        return initial

    def get_invite(self) -> Optional[Invite]:
        """return Invite model instance if the user registers after accepting invite"""
        invite_key = unquote(self.request.GET.get("invite", ""))
        if not invite_key:
            return

        return get_object_or_404(Invite, key=invite_key)

    def form_valid(self, form):
        user = form.save()

        invite = form.cleaned_data["invite"]
        if invite:
            invite.add_invitee(user)

        self.request.user = user
        self.log_user_action(user, _("user was created"))
        return HttpResponseRedirect(self.get_success_url())
