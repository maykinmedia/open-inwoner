from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse_lazy
from django.views.generic import CreateView, ListView
from django.views.generic.edit import UpdateView

from ..forms import ContactForm
from ..models import Contact, Invite


class ContactListView(LoginRequiredMixin, ListView):
    template_name = "pages/profile/contacts/list.html"
    model = Contact
    paginate_by = 10

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(created_by=self.request.user)


class ContactUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "pages/profile/contacts/edit.html"
    model = Contact
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = ContactForm
    success_url = reverse_lazy("accounts:contact_list")

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(created_by=self.request.user)

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return HttpResponseRedirect(self.get_success_url())


class ContactCreateView(LoginRequiredMixin, CreateView):
    template_name = "pages/profile/contacts/edit.html"
    model = Contact
    form_class = ContactForm
    success_url = reverse_lazy("accounts:contact_list")

    def form_valid(self, form):
        self.object = form.save(self.request.user)

        # send invite to the contact
        contact_user = self.object.contact_user
        if not contact_user.is_active and not contact_user.deactivated_on:
            invite = Invite.objects.create(
                inviter=self.request.user, invitee=contact_user, contact=self.object
            )
            invite.send()

        return HttpResponseRedirect(self.get_success_url())
