from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse_lazy
from django.views.generic import CreateView, ListView
from django.views.generic.edit import UpdateView

from ..forms import ContactForm
from ..models import Contact


class ContactListView(LoginRequiredMixin, ListView):
    template_name = "pages/profile/contacts/list.html"
    model = Contact
    paginate_by = 10


class ContactUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "pages/profile/contacts/edit.html"
    model = Contact
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = ContactForm
    success_url = reverse_lazy("accounts:contact_list")

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
        return HttpResponseRedirect(self.get_success_url())
