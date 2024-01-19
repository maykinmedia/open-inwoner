from typing import Optional
from urllib.parse import unquote

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext as _
from django.views.generic import UpdateView

from django_registration.backends.one_step.views import RegistrationView
from furl import furl

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)
from open_inwoner.utils.hash import generate_email_from_string
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from ..forms import CustomRegistrationForm, NecessaryUserForm
from ..models import Invite, User


class InviteMixin(CommonPageMixin):
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
        invitee = invite.invitee
        if not invitee in inviter_contacts:
            invite.inviter.user_contacts.add(invitee)


class CustomRegistrationView(LogMixin, InviteMixin, RegistrationView):
    form_class = CustomRegistrationForm

    def page_title(self):
        return _("Registratie")

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Registratie is voltooid")
        return reverse("pages-root")

    def form_valid(self, form):
        user = form.save()

        invite = form.cleaned_data["invite"]
        if invite:
            self.add_invitee(invite, user)

        # Remove invite url from user's session
        session = self.request.session
        if "invite_url" in session.keys():
            del session["invite_url"]

        self.request.user = user
        self.log_user_action(user, _("user was created"))
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        invite_key = self.request.GET.get("invite")
        necessary_fields_url = (
            furl(reverse("profile:registration_necessary"))
            .add({"invite": invite_key})
            .url
            if invite_key
            else reverse("profile:registration_necessary")
        )

        try:
            config = OpenIDConnectDigiDConfig.get_solo()
            if config.enabled:
                digid_url = reverse("digid_oidc:init")
            else:
                digid_url = reverse("digid:login")
            context["digid_url"] = (
                furl(digid_url).add({"next": necessary_fields_url}).url
            )
        except NoReverseMatch:
            context["digid_url"] = ""

        try:
            config = OpenIDConnectEHerkenningConfig.get_solo()
            if config.enabled:
                eherkenning_url = reverse("eherkenning_oidc:init")
            else:
                eherkenning_url = reverse("eherkenning:login")
            context["eherkenning_url"] = (
                furl(eherkenning_url).add({"next": necessary_fields_url}).url
            )
        except NoReverseMatch:
            context["eherkenning_url"] = ""
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

    def page_title(self):
        return _("Registratie voltooien")

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Registratie is voltooid")
        return reverse("pages-root")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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

        generated_email = generate_email_from_string(user.kvk, domain="localhost")
        if not invite and (
            (user.bsn and user.email == generate_email_from_string(user.bsn))
            or (user.oidc_id and user.email == generate_email_from_string(user.oidc_id))
            or (user.kvk and user.email == generated_email)
        ):
            initial["email"] = ""

        return initial
