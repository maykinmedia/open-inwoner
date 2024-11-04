import logging
from collections.abc import Generator
from datetime import date
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import FormView, TemplateView, UpdateView

from aldryn_apphooks_config.mixins import AppConfigMixin
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.accounts.choices import (
    ContactTypeChoices,
    LoginTypeChoices,
    NotificationChannelChoice,
    StatusChoices,
)
from open_inwoner.cms.utils.page_display import (
    benefits_page_is_published,
    inbox_page_is_published,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.haalcentraal.utils import fetch_brp
from open_inwoner.laposta.forms import NewsletterSubscriptionForm
from open_inwoner.laposta.models import LapostaConfig
from open_inwoner.plans.models import Plan
from open_inwoner.qmatic.client import NoServiceConfigured, QmaticClient
from open_inwoner.questionnaire.models import QuestionnaireStep
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from ..forms import BrpUserForm, CategoriesForm, UserForm, UserNotificationsForm
from ..models import Action, User
from .mixins import KlantenAPIMixin

logger = logging.getLogger(__name__)


class MyProfileView(
    LogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    AppConfigMixin,
    FormView,
):
    template_name = "pages/profile/me.html"
    form_class = NewsletterSubscriptionForm

    def get_success_url(self) -> str:
        return reverse("profile:detail")

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        form.save(self.request)

        # Display errors raised by Laposta API
        if form.errors:
            self.log_user_action(
                self.request.user, _("failed to modify user newsletter subscription")
            )
            return self.form_invalid(form)

        messages.success(self.request, _("Uw wijzigingen zijn opgeslagen"))
        self.log_user_action(
            self.request.user, _("users newsletter subscriptions were modified")
        )
        return HttpResponseRedirect(self.get_success_url())

    @cached_property
    def crumbs(self):
        return [(_("Mijn profiel"), reverse("profile:detail"))]

    @staticmethod
    def stringify(
        items: list, string_func: callable, lump: bool = False
    ) -> Generator | str:
        """
        Create string representation(s) of `items` for display

        :param string_func: the function used to stringify elements in `items`
        :param lump: if `True`, `string_func` is applied to `items` collectively
        :returns: a `Generator` of strings representing elements in `items`, or a
            `str` representing `items` as a whole, depending on whether `lump` is
            `True`
        """
        if lump:
            return string_func(items)
        return (string_func(item) for item in items)

    def get_context_data(self, **kwargs):
        config = SiteConfiguration.get_solo()
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()

        context["anchors"] = [
            ("#personal-info", _("Persoonlijke gegevens")),
            ("#overview", _("Overzicht")),
            ("#profile-remove", _("Profiel verwijderen")),
        ]
        if config.any_notifications_enabled:
            context["anchors"].insert(
                1, ("#notifications", _("Voorkeuren voor meldingen"))
            )

        # Check if Laposta is configured and user has verified email
        if LapostaConfig.get_solo().api_root and user.has_verified_email():
            # Insert #newsletters anchor
            context["anchors"].insert(2, ("#newsletters", _("Nieuwsbrieven")))

        user_files = user.get_all_files()

        # Mentor contacts + names for display
        mentor_contacts = user.user_contacts.filter(
            contact_type=ContactTypeChoices.begeleider
        )
        context["mentor_contacts"] = mentor_contacts
        context["mentor_contact_names"] = self.stringify(
            mentor_contacts,
            string_func=lambda m: m.get_full_name,
        )

        # Regular contacts + names for display
        contacts = user.get_active_contacts()
        context["contact_names"] = self.stringify(
            contacts,
            string_func=lambda c: f"{c.first_name} ({c.get_contact_type_display()})",
        )

        # Actions
        actions = (
            Action.objects.visible()
            .connected(self.request.user)
            .filter(status=StatusChoices.open)
        )
        context["action_text"] = self.stringify(
            actions,
            string_func=lambda actions: f"{actions.count()} acties staan open",
            lump=True,
        )

        context["next_action"] = (
            Action.objects.visible()
            .connected(self.request.user)
            .filter(end_date__gte=today, status=StatusChoices.open)
            .order_by("end_date")
            .first()
        )

        context["files"] = user_files

        context["selected_categories"] = user.get_interests()

        context["questionnaire_exists"] = QuestionnaireStep.objects.filter(
            published=True
        ).exists()
        context["can_change_password"] = user.login_type not in (
            LoginTypeChoices.digid,
            LoginTypeChoices.eherkenning,
        )
        context["inbox_page_is_published"] = inbox_page_is_published()
        context["benefits_page_is_published"] = benefits_page_is_published()

        return context

    def post(self, request, *args, **kwargs):
        if "newsletter-submit" in request.POST:
            return super().post(request, *args, **kwargs)

        if request.user.is_authenticated and not request.user.is_staff:
            instance = User.objects.get(id=request.user.id)

            # check if there are still plans created by or associated witht the user
            if Plan.objects.connected(instance):
                messages.warning(
                    request,
                    _(
                        "Your profile could not be deleted because you still "
                        "have plans associated with it."
                    ),
                )
                return redirect("profile:detail")

            # continue with delete
            self.log_user_action(instance, _("user was deleted via frontend"))
            instance.delete()
            request.session.flush()

            return redirect(reverse("logout"))
        else:
            messages.warning(request, _("Uw account kon niet worden verwijderd"))
            return redirect("profile:detail")


class EditProfileView(
    LogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    KlantenAPIMixin,
    BaseBreadcrumbMixin,
    UpdateView,
):
    template_name = "pages/profile/edit.html"
    model = User
    form_class = UserForm
    success_url = reverse_lazy("profile:detail")

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("profile:detail")),
            (_("Bewerk profiel"), reverse("profile:edit", kwargs=self.kwargs)),
        ]

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        form.save()

        self.update_klant({k: form.cleaned_data[k] for k in form.changed_data})

        messages.success(self.request, _("Uw wijzigingen zijn opgeslagen"))
        self.log_change(self.get_object(), _("profile was modified"))
        return HttpResponseRedirect(self.get_success_url())

    def update_klant(self, user_form_data: dict):
        field_mapping = {
            "emailadres": "email",
            "telefoonnummer": "phonenumber",
        }
        update_data = {
            api_name: user_form_data[local_name]
            for api_name, local_name in field_mapping.items()
            if user_form_data.get(local_name)
        }
        self.patch_klant(update_data)

    def get_form_class(self):
        user = self.request.user
        if user.is_digid_user_with_brp:
            return BrpUserForm
        return super().get_form_class()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MyCategoriesView(
    LogMixin, LoginRequiredMixin, CommonPageMixin, BaseBreadcrumbMixin, UpdateView
):
    template_name = "pages/profile/categories.html"
    model = User
    form_class = CategoriesForm
    success_url = reverse_lazy("profile:detail")

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("profile:detail")),
            (_("Mijn interessegebieden"), reverse("profile:categories")),
        ]

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Uw wijzigingen zijn opgeslagen"))
        self.log_change(self.object, _("categories were modified"))
        return HttpResponseRedirect(self.get_success_url())


class MyDataView(
    LogMixin, LoginRequiredMixin, CommonPageMixin, BaseBreadcrumbMixin, TemplateView
):
    template_name = "pages/profile/mydata.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("profile:detail")),
            (_("Mijn gegevens"), reverse("profile:data")),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["my_data"] = self.get_brp_data()
        return context

    def get_brp_data(self):
        self.log_user_action(self.request.user, _("user requests for brp data"))
        data = fetch_brp(self.request.user.bsn)
        return data


class MyNotificationsView(
    LogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    KlantenAPIMixin,
    BaseBreadcrumbMixin,
    UpdateView,
):
    template_name = "pages/profile/notifications.html"
    model = User
    form_class = UserNotificationsForm
    success_url = reverse_lazy("profile:detail")

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("profile:detail")),
            (_("Ontvang berichten over"), reverse("profile:notifications")),
        ]

    def get(self, *args, **kwargs):
        config = SiteConfiguration.get_solo()
        if not config.any_notifications_enabled:
            return HttpResponseRedirect(reverse("profile:detail"))
        return super().get(*args, **kwargs)

    def get_object(self):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        config = SiteConfiguration.get_solo()
        context_data["notifications_cases_enabled"] = config.notifications_cases_enabled
        return context_data

    def form_valid(self, form):
        form.save()

        self.update_klant(
            user_form_data={k: form.cleaned_data[k] for k in form.changed_data}
        )

        messages.success(self.request, _("Uw wijzigingen zijn opgeslagen"))
        self.log_change(self.object, _("users notifications were modified"))
        return HttpResponseRedirect(self.get_success_url())

    def update_klant(self, user_form_data: dict):
        config = SiteConfiguration.get_solo()
        if not config.enable_notification_channel_choice:
            return

        if notification_channel := user_form_data.get("case_notification_channel"):
            self.patch_klant(
                update_data={
                    "toestemmingZaakNotificatiesAlleenDigitaal": notification_channel
                    == NotificationChannelChoice.digital_only
                }
            )


class UserAppointmentsView(
    LogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    TemplateView,
):
    template_name = "pages/profile/appointments.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user: User = self.request.user
        if not user.has_verified_email():
            context["appointments"] = []
        else:
            try:
                client = QmaticClient()
            except NoServiceConfigured:
                logger.exception("Error occurred while creating Qmatic client")
                context["appointments"] = []
            else:
                context["appointments"] = client.list_appointments_for_customer(
                    user.verified_email
                )
        return context

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("profile:detail")),
            (_("Mijn afspraken"), reverse("profile:appointments")),
        ]
