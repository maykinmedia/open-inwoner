from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import CreateView, ListView
from django.views.generic.edit import DeleteView, UpdateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.utils.views import LogMixin

from ..choices import ContactTypeChoices
from ..forms import ContactFilterForm, ContactForm
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
        base_qs = base_qs.get_extended_contacts_for_user(me=self.request.user)
        type_filter = self.request.GET.get("type")
        if type_filter:
            if type_filter == ContactTypeChoices.contact:
                base_qs = base_qs.filter(
                    Q(contact_user__contact_type=type_filter)
                    | Q(contact_user__isnull=True)
                )
            else:
                base_qs = base_qs.filter(contact_user__contact_type=type_filter)
        return base_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ContactFilterForm(data=self.request.GET)
        return context


class ContactUpdateView(LogMixin, LoginRequiredMixin, BaseBreadcrumbMixin, UpdateView):
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

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            "user": self.request.user,
            "create": False,
        }

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(created_by=self.request.user)

    def form_valid(self, form):
        self.object = form.save()

        self.log_change(self.object, _("contact was modified"))
        return HttpResponseRedirect(self.get_success_url())


class ContactCreateView(LogMixin, LoginRequiredMixin, BaseBreadcrumbMixin, CreateView):
    template_name = "pages/profile/contacts/edit.html"
    model = Contact
    form_class = ContactForm

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

    def get_success_url(self):
        if self.object:
            return self.object.get_update_url()
        return reverse_lazy("accounts:contact_list")

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            "user": self.request.user,
            "create": True,
        }

    def form_valid(self, form):
        self.object = form.save()

        # send invite to the contact
        if not self.object.contact_user and self.object.email:
            invite = Invite.objects.create(
                inviter=self.request.user,
                invitee_email=self.object.email,
                contact=self.object,
            )
            invite.send(self.request)

        # FIXME type off message
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _(
                "{contact} is toegevoegd aan uw contactpersonen.".format(
                    contact=self.object
                )
            ),
        )

        self.log_addition(self.object, _("contact was created"))
        return HttpResponseRedirect(self.get_success_url())


class ContactDeleteView(LogMixin, LoginRequiredMixin, DeleteView):
    model = Contact
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("accounts:contact_list")

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(created_by=self.request.user)

    def delete(self, request, *args, **kwargs):
        object = self.get_object()
        super().delete(request, *args, **kwargs)

        self.log_deletion(object, _("contact was deleted"))
        return HttpResponseRedirect(self.success_url)
