from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseBadRequest, HttpResponseRedirect
from django.urls.base import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import ListView, View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.utils.views import LogMixin

from ..forms import ContactCreateForm, ContactFilterForm
from ..models import Invite, User


class ContactListView(LoginRequiredMixin, BaseBreadcrumbMixin, ListView):
    template_name = "pages/profile/contacts/list.html"
    model = User
    paginate_by = 10

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("accounts:my_profile")),
            (_("Mijn contacten"), reverse("accounts:contact_list")),
        ]

    def get_queryset(self):
        base_qs = self.request.user.get_active_contacts()
        type_filter = self.request.GET.get("type")

        if type_filter:
            base_qs = base_qs.filter(contact_type=type_filter)

        return base_qs.order_by("-date_joined")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        pending_approvals = User.objects.get_pending_approvals(user)
        if pending_approvals.count() == 1:
            context["pending_approval"] = pending_approvals.get()
        else:
            context["pending_approval_list"] = pending_approvals
        context["contacts_for_approval"] = user.get_contacts_for_approval()
        context["pending_invitations"] = user.get_pending_invitations()
        context["form"] = ContactFilterForm(data=self.request.GET)
        return context


class ContactCreateView(LogMixin, LoginRequiredMixin, BaseBreadcrumbMixin, FormView):
    template_name = "pages/profile/contacts/edit.html"
    form_class = ContactCreateForm
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

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "user": self.request.user}

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        email = cleaned_data["email"]
        user = self.request.user
        contact_user = User.objects.filter(email=email)

        # Adding a contact-user which already exists in the platform
        if contact_user.exists():
            user.contacts_for_approval.add(contact_user.get())
            self.log_addition(contact_user[0], _("contact was added, pending approval"))
        # New contact-user which triggers an invite
        else:
            invite = Invite.objects.create(
                inviter=self.request.user,
                invitee_email=email,
                invitee_first_name=cleaned_data["first_name"],
                invitee_last_name=cleaned_data["last_name"],
            )
            invite.send(self.request)
            self.log_addition(
                invite,
                _("invite was created"),
            )

        # FIXME type off message
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _(
                "{contact} is toegevoegd aan uw contactpersonen.".format(
                    contact=cleaned_data["email"]
                )
            ),
        )
        return HttpResponseRedirect(self.get_success_url())


class ContactDeleteView(LogMixin, LoginRequiredMixin, SingleObjectMixin, View):
    model = User
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("accounts:contact_list")

    def get_queryset(self):
        base_qs = super().get_queryset()

        current_user = self.request.user
        base_qs = current_user.user_contacts.all()
        return base_qs

    def post(self, request, *args, **kwargs):
        object = self.get_object()
        current_user = self.request.user

        # Remove relationship between the two users
        current_user.user_contacts.remove(object)

        self.log_change(object, _("contact relationship was removed"))
        return HttpResponseRedirect(self.success_url)


class ContactApprovalView(LogMixin, LoginRequiredMixin, SingleObjectMixin, View):
    model = User
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("accounts:contact_list")

    def get_queryset(self):
        base_qs = super().get_queryset()
        base_qs = User.objects.get_pending_approvals(self.request.user)
        return base_qs

    def post(self, request, *args, **kwargs):
        sender = self.get_object()
        receiver = self.request.user
        approved = request.POST.get("contact_approve")
        rejected = request.POST.get("contact_reject")
        if approved or rejected:
            self.update_contact(sender, receiver, (approved or rejected))
            return HttpResponseRedirect(self.success_url)

        return HttpResponseBadRequest(
            "contact_approve or contact_reject must be provided"
        )

    def update_contact(self, sender, receiver, type_of_approval):
        if type_of_approval == "approve":
            sender.contacts_for_approval.remove(receiver)
            sender.user_contacts.add(receiver)
            self.log_change(sender, _("contact was approved"))

        elif type_of_approval == "reject":
            sender.contacts_for_approval.remove(receiver)
            self.log_change(sender, _("contact was rejected"))
