from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import DetailView, FormView, TemplateView, UpdateView

from glom import PathAccessError, glom
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.accounts.choices import (
    ContactTypeChoices,
    LoginTypeChoices,
    StatusChoices,
)
from open_inwoner.haalcentraal.utils import fetch_brb_data
from open_inwoner.questionnaire.models import QuestionnaireStep
from open_inwoner.utils.mixins import ExportMixin
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from ..forms import ThemesForm, UserForm
from ..models import Action, User


class MyProfileView(
    LogMixin, LoginRequiredMixin, CommonPageMixin, BaseBreadcrumbMixin, FormView
):
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
            c.get_full_name()
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
        contacts = user.get_active_contacts()
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

        context["questionnaire_exists"] = QuestionnaireStep.objects.filter(
            published=True
        ).exists()
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


class EditProfileView(
    LogMixin, LoginRequiredMixin, CommonPageMixin, BaseBreadcrumbMixin, UpdateView
):
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


class MyCategoriesView(
    LogMixin, LoginRequiredMixin, CommonPageMixin, BaseBreadcrumbMixin, UpdateView
):
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


class MyDataView(
    LoginRequiredMixin, CommonPageMixin, BaseBreadcrumbMixin, TemplateView
):
    template_name = "pages/profile/mydata.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("accounts:my_profile")),
            (_("Mijn gegevens"), reverse("accounts:my_data")),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["my_data"] = self.parse_brp_data()
        return context

    def parse_brp_data(self):
        brp_version = settings.BRP_VERSION
        user = self.request.user
        my_data = {
            "first_name": "naam.voornamen",
            "initials": "naam.voorletters",
            "last_name": "naam.geslachtsnaam",
            "prefix": "naam.voorvoegsel",
            "birthday": "geboorte.datum.datum",
            "birthday_place": "geboorte.plaats.omschrijving",
            "birthday_country": "geboorte.land.omschrijving",
            "gender": "geslachtsaanduiding.omschrijving"
            if brp_version == "2.0"
            else "geslachtsaanduiding",
            "street": "verblijfplaats.straat",
            "house_number": "verblijfplaats.huisnummer",
            "postcode": "verblijfplaats.postcode",
            "place": "verblijfplaats.woonplaats",
            "land": "verblijfplaats.land.omschrijving",
        }

        fetched_data = fetch_brb_data(user, brp_version)

        # we have a different response depending on brp version
        if brp_version == "2.0" and fetched_data.get("personen"):
            fetched_data = glom(fetched_data, "personen")[0]

        if not fetched_data:
            return {}

        for field in my_data:
            try:
                my_data[field] = glom(fetched_data, my_data[field])
            except PathAccessError:
                my_data[field] = None

        return my_data


class MyProfileExportView(LogMixin, LoginRequiredMixin, ExportMixin, DetailView):
    template_name = "export/profile/profile_export.html"
    model = User

    def get_object(self):
        return self.request.user

    def get_filename(self):
        return "profile.pdf"
