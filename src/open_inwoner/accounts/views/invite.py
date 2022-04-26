from django.http.response import Http404, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView

from furl import furl

from ..forms import InviteForm
from ..models import Invite

from open_inwoner.utils.logentry import LogMixin


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

        self.log_system_action(str(_("invitation accepted")), self.object)
        return HttpResponseRedirect(url)

    def get_object(self, queryset=None):
        invite = super().get_object(queryset)

        if invite.expired():
            self.log_system_action(str(_("invitation expired")), invite)
            raise Http404(_("The invitation was expired"))

        return invite
