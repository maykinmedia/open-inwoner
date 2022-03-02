from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, ListView
from django.views.generic.edit import UpdateView

from view_breadcrumbs import BaseBreadcrumbMixin

from ..forms import ContactForm
from ..models import Contact, Invite


class ContactListView(LoginRequiredMixin, BaseBreadcrumbMixin, ListView):
    template_name = "pages/profile/contacts/list.html"
    model = Contact
    paginate_by = 10

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("accounts:my_profile")),
            (_("Mijn contacten"), reverse("accounts:contact_list")),
        ]

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.get_extended_contacts_for_user(me=self.request.user)


class ContactUpdateView(LoginRequiredMixin, BaseBreadcrumbMixin, UpdateView):
    template_name = "pages/profile/contacts/edit.html"
    model = Contact
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = ContactForm
    success_url = reverse_lazy("accounts:contact_list")

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("accounts:my_profile")),
            (_("Mijn contacten"), reverse("accounts:contact_list")),
            (
                _("Bewerk {}").format(self.object.get_name()),
                reverse("accounts:contact_edit", kwargs=self.kwargs),
            ),
        ]

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(created_by=self.request.user)

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return HttpResponseRedirect(self.get_success_url())


class ContactCreateView(LoginRequiredMixin, BaseBreadcrumbMixin, CreateView):
    template_name = "pages/profile/contacts/edit.html"
    model = Contact
    form_class = ContactForm
    success_url = reverse_lazy("accounts:contact_list")

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("accounts:my_profile")),
            (_("Mijn contacten"), reverse("accounts:contact_list")),
            (
                _("Maak contact aan"),
                reverse("accounts:contact_create", kwargs=self.kwargs),
            ),
        ]

    def form_valid(self, form):
        self.object = form.save(self.request.user)

        # send invite to the contact
        contact_user = self.object.contact_user
        if (
            contact_user
            and not contact_user.is_active
            and not contact_user.deactivated_on
        ):
            invite = Invite.objects.create(
                inviter=self.request.user, invitee=contact_user, contact=self.object
            )
            invite.send(self.request)

        return HttpResponseRedirect(self.get_success_url())
