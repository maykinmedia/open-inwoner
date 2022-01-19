from django.http.response import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from ..forms import InviteForm
from ..models import Invite


class InviteAcceptView(UpdateView):
    template_name = "accounts/invite_accept.html"
    model = Invite
    slug_field = "key"
    slug_url_kwarg = "key"
    form_class = InviteForm
    success_url = reverse_lazy("django_registration_register")

    # todo not show GET and POST if invite is expired
    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())
