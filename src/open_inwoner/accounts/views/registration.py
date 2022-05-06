from typing import Optional
from urllib.parse import unquote

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from django_registration.backends.one_step.views import RegistrationView

from open_inwoner.utils.views import LogMixin

from ..forms import CustomRegistrationForm
from ..models import Invite, User


class CustomRegistrationView(LogMixin, RegistrationView):
    form_class = CustomRegistrationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        existing_user = self.get_object()
        if (
            existing_user
            and not existing_user.is_active
            and not existing_user.deactivated_on
        ):
            kwargs["instance"] = existing_user

        return kwargs

    def get_initial(self):
        initial = super().get_initial()

        invite = self.get_invite()
        if invite:
            initial["invite"] = invite

        return initial

    def get_invite(self) -> Optional[Invite]:
        """return Invite model instance if the user registers after accepting invite"""
        invite_key = unquote(self.request.GET.get("invite", ""))
        if not invite_key:
            return

        return get_object_or_404(Invite, key=invite_key)

    def get_object(self) -> Optional[User]:
        """return existing user with this email"""
        invite = self.get_invite()

        email = (
            invite.invitee.email
            if invite
            else self.request.POST.get("email", self.get_initial().get("email"))
        )
        if not email:
            return

        return User.objects.filter(email=email).first()

    def form_valid(self, form):
        object = form.save()

        self.request.user = object
        self.log_user_action(object, _("user was created"))
        return HttpResponseRedirect(self.get_success_url())
