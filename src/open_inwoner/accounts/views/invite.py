from django.http.response import Http404, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import UpdateView

from furl import furl

from open_inwoner.utils.views import CommonPageMixin, LogMixin

from ..forms import InviteForm
from ..models import Invite


class InviteAcceptView(LogMixin, CommonPageMixin, UpdateView):
    template_name = "accounts/invite_accept.html"
    model = Invite
    slug_field = "key"
    slug_url_kwarg = "key"
    form_class = InviteForm
    success_url = reverse_lazy("django_registration_register")

    def page_title(self):
        return _("Accept an invitation")

    def form_valid(self, form):
        self.object = form.save()
        url = furl(self.success_url).add({"invite": self.object.key}).url

        self.log_system_action(_("invitation accepted"), self.object)
        return HttpResponseRedirect(url)

    def get_object(self, queryset=None):
        invite = super().get_object(queryset)

        if self.request.user.is_authenticated:
            raise Http404(_("U bent al ingelogd."))

        if invite.expired():
            self.log_system_action(_("invitation expired"), invite)
            raise Http404(_("The invitation was expired"))

        if invite.accepted:
            self.log_system_action(_("invitation used"), invite)
            raise Http404(_("The invitation was already used"))

        return invite
