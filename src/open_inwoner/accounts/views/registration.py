from typing import Optional
from urllib.parse import unquote

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import UpdateView

from django_registration.backends.one_step.views import RegistrationView
from furl import furl

from open_inwoner.accounts.models import Contact
from open_inwoner.utils.hash import generate_email_from_string
from open_inwoner.utils.views import LogMixin

from ..forms import CustomRegistrationForm, NecessaryUserForm
from ..models import Invite, User


class InviteMixin:
    def get_initial(self):
        initial = super().get_initial()

        invite = self.get_invite()
        if invite:
            initial.update(
                {
                    "invite": invite,
                    "email": invite.invitee_email,
                    "first_name": invite.invitee_first_name,
                    "last_name": invite.invitee_last_name,
                }
            )

        return initial

    def get_invite(self) -> Optional[Invite]:
        """return Invite model instance if the user registers after accepting invite"""
        invite_key = unquote(self.request.GET.get("invite", ""))
        if not invite_key:
            return

        return get_object_or_404(Invite, key=invite_key)

    def add_invitee(self, invite, user):
        """update invite and related contact"""
        if not invite.invitee:
            invite.accepted = True
            invite.invitee = user
            invite.save()

        #  update inviter - invitee relationship
        inviter_contacts = invite.inviter.user_contacts.all()
        if not invite.invitee in inviter_contacts:
            invite.inviter.user_contacts.add(invite.invitee)


class CustomRegistrationView(LogMixin, InviteMixin, RegistrationView):
    form_class = CustomRegistrationForm

    def form_valid(self, form):
        user = form.save()

        invite = form.cleaned_data["invite"]
        if invite:
            self.add_invitee(invite, user)

        self.request.user = user
        self.log_user_action(user, _("user was created"))
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        invite_key = self.request.GET.get("invite")
        necessary_fields_url = (
            furl(reverse("accounts:registration_necessary"))
            .add({"invite": invite_key})
            .url
            if invite_key
            else reverse("accounts:registration_necessary")
        )
        context["digit_url"] = (
            furl(reverse("digid:login")).add({"next": necessary_fields_url}).url
        )
        return context

    def get(self, request, *args, **kwargs):
        """if the user is authorized and active - redirect them to the complete page"""
        if request.user and request.user.is_active:
            return HttpResponseRedirect(self.get_success_url())

        return super().get(self, request, *args, **kwargs)


class NecessaryFieldsUserView(LogMixin, LoginRequiredMixin, InviteMixin, UpdateView):
    model = User
    form_class = NecessaryUserForm
    template_name = "accounts/registration_necessary.html"
    success_url = reverse_lazy("django_registration_complete")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        user = form.save()

        invite = form.cleaned_data["invite"]
        if invite:
            self.add_invitee(invite, user)

        self.log_user_action(user, _("user was updated with necessary fields"))
        return HttpResponseRedirect(self.get_success_url())

    def get_initial(self):
        initial = super().get_initial()

        user = self.get_object()
        invite = self.get_invite()

        if not invite and (
            (user.bsn and user.email == generate_email_from_string(user.bsn))
            or (user.oidc_id and user.email == generate_email_from_string(user.oidc_id))
        ):
            initial["email"] = ""

        return initial
