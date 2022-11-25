from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.forms.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import DetailView, FormView, UpdateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.accounts.choices import (
    ContactTypeChoices,
    LoginTypeChoices,
    StatusChoices,
)
from open_inwoner.questionnaire.models import QuestionnaireStep
from open_inwoner.utils.mixins import ExportMixin
from open_inwoner.utils.views import LogMixin

from ..forms import ThemesForm, UserForm
from ..models import Action, Contact, User


class MyProfileView(LogMixin, LoginRequiredMixin, BaseBreadcrumbMixin, FormView):
    template_name = "pages/profile/me.html"
    form_class = Form

    @cached_property
    def crumbs(self):
        return [(_("Mijn profiel"), reverse("accounts:my_profile"))]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()

        context["anchors"] = [
            ("#title", _("Persoonlijke gegevens")),
            ("#overview", _("Persoonlijk overzicht")),
            ("#files", _("Bestanden")),
        ]
        # List of names of 'mentor' users that are a contact of me
        mentor_contacts = [
            str(c.get_full_name())
            for c in user.user_contacts.filter(
                contact_type=ContactTypeChoices.begeleider
            )
        ]

        context["mentor_contacts"] = mentor_contacts
        context["next_action"] = (
            Action.objects.visible()
            .connected(self.request.user)
            .filter(end_date__gte=today, status=StatusChoices.open)
            .order_by("end_date")
            .first()
        )
        context["files"] = user.get_all_files()
        context["theme_text"] = user.get_interests()
        context["action_text"] = _(
            f"{Action.objects.visible().connected(self.request.user).filter(status=StatusChoices.open).count()} acties staan open."
        )
        contacts = user.get_all_contacts()
        # Invited contacts
        contact_names = [
            f"{contact.first_name} ({contact.get_contact_type_display()})"
            for contact in contacts[:3]
        ]

        if contacts.count() > 0:
            context[
                "contact_text"
            ] = f"{', '.join(contact_names)}{'...' if contacts.count() > 3 else ''}"
        else:
            context["contact_text"] = _("U heeft nog geen contacten.")
        context["questionnaire_exists"] = QuestionnaireStep.objects.exists()
        context["can_change_password"] = user.login_type != LoginTypeChoices.digid
        return context

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff:
            instance = User.objects.get(id=request.user.id)
            self.request.user.deactivate()

            self.log_user_action(instance, _("user was deactivated via frontend"))
            return redirect(instance.get_logout_url())
        else:
            messages.warning(request, _("Uw account kon niet worden gedeactiveerd"))
            return redirect("accounts:my_profile")


class EditProfileView(LogMixin, LoginRequiredMixin, BaseBreadcrumbMixin, UpdateView):
    template_name = "pages/profile/edit.html"
    model = User
    form_class = UserForm
    success_url = reverse_lazy("accounts:my_profile")

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("accounts:my_profile")),
            (_("Bewerk profiel"), reverse("accounts:edit_profile", kwargs=self.kwargs)),
        ]

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        form.save()

        self.log_change(self.get_object(), _("profile was modified"))
        return HttpResponseRedirect(self.get_success_url())


class MyCategoriesView(LogMixin, LoginRequiredMixin, BaseBreadcrumbMixin, UpdateView):
    template_name = "pages/profile/categories.html"
    model = User
    form_class = ThemesForm
    success_url = reverse_lazy("accounts:my_profile")

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("accounts:my_profile")),
            (_("Mijn thema's"), reverse("accounts:my_themes")),
        ]

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        form.save()

        self.log_change(self.object, _("categories were modified"))
        return HttpResponseRedirect(self.get_success_url())


class MyProfileExportView(LogMixin, LoginRequiredMixin, ExportMixin, DetailView):
    template_name = "export/profile/profile_export.html"
    model = User

    def get_object(self):
        return self.request.user

    def get_filename(self):
        return "profile.pdf"
