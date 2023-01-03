from django.contrib import messages
from django.http.response import Http404, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import UpdateView

from furl import furl

from open_inwoner.utils.views import LogMixin

from ..forms import InviteForm
from ..models import Invite


class InviteAcceptView(LogMixin, UpdateView):
    template_name = "accounts/invite_accept.html"
    model = Invite
    slug_field = "key"
    slug_url_kwarg = "key"
    form_class = InviteForm
    success_url = reverse_lazy("django_registration_register")

    def form_valid(self, form):
        self.object = form.save()
        url = furl(self.success_url).add({"invite": self.object.key}).url

        # add invite url to the session
        # this will be needed for redirection if digid login fails
        self.request.session["invite_url"] = url

        self.log_system_action(_("invitation accepted"), self.object)
        return HttpResponseRedirect(url)

    def get_object(self, queryset=None):
        invite = super().get_object(queryset)

        if invite.expired():
            self.log_system_action(_("invitation expired"), invite)
            raise Http404(_("The invitation was expired"))

        if invite.accepted:
            self.log_system_action(_("invitation used"), invite)
            raise Http404(_("The invitation was already used"))

        return invite

    def dispatch(self, request, *args, **kwargs):
        invite = self.get_object()
        user = request.user

        # mark invitation as accepted and add inviter to the user's contacts as well
        if user.is_authenticated:
            invite.accepted = True
            invite.invitee = user
            invite.save()

            inviter = invite.inviter
            user.user_contacts.add(inviter)
            self.log_system_action(_("invitation automatically accepted"), invite)

            messages.add_message(
                self.request,
                messages.SUCCESS,
                _(
                    "{inviter} is toegevoegd aan uw contactpersonen.".format(
                        inviter=inviter.email
                    )
                ),
            )
            return HttpResponseRedirect(reverse("accounts:contact_list"))

        return super().dispatch(request, *args, **kwargs)
