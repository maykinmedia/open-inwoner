from typing import Optional
from urllib.parse import unquote

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _

from django_registration.backends.one_step.views import RegistrationView
from furl import furl

from open_inwoner.accounts.models import Contact
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
            self.add_invitee(invite, user)

        self.request.user = user
        self.log_user_action(user, _("user was created"))
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        this_url = self.request.get_full_path()
        context["digit_url"] = furl(reverse("digid:login")).add({"next": this_url}).url
        return context

    def get(self, request, *args, **kwargs):
        """if the user is authorized and active - redirect them to the complete page"""
        if not (request.user and request.user.is_active):
            return super().get(self, request, *args, **kwargs)

        invite = self.get_invite()
        # for users logged in with digid: update their invite and contact
        if invite:
            self.add_invitee(invite, request.user)

        return HttpResponseRedirect(self.get_success_url())

    def add_invitee(self, invite, user):
        """update invite and related contact and create reversed contact"""
        if not invite.invitee:
            invite.accepted = True
            invite.invitee = user
            invite.save()

        #  update contact user
        contact = invite.contact
        if contact and not contact.contact_user:
            contact.contact_user = user
            contact.save()

        # create reverse contact
        reverse_contact, created = Contact.objects.get_or_create(
            contact_user=invite.inviter,
            created_by=user,
            defaults={
                "first_name": invite.inviter.first_name,
                "last_name": invite.inviter.last_name,
                "email": invite.inviter.email,
            },
        )
        if created:
            self.request.user = user
            self.log_user_action(reverse_contact, _("contact was created"))
