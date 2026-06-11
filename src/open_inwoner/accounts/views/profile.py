from collections.abc import Generator
from datetime import date
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import FormView, TemplateView, UpdateView

import requests
import structlog
from aldryn_apphooks_config.mixins import AppConfigMixin
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.accounts.brp import BRPData
from open_inwoner.accounts.choices import (
    ContactTypeChoices,
    LoginTypeChoices,
    StatusChoices,
)
from open_inwoner.accounts.forms import (
    BrpUserForm,
    CategoriesForm,
    UserForm,
    UserNotificationsForm,
)
from open_inwoner.accounts.models import Action, User
from open_inwoner.cms.utils.page_display import (
    benefits_page_is_published,
    case_page_is_published,
    inbox_page_is_published,
    products_page_is_published,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.haalcentraal.clients import BRPClient
from open_inwoner.laposta.forms import NewsletterSubscriptionForm
from open_inwoner.laposta.models import LapostaConfig
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.exceptions import KlantAPIError
from open_inwoner.openklant.models import KlantenSysteemConfig
from open_inwoner.openklant.services import OpenKlant2Service, eSuiteKlantenService
from open_inwoner.plans.models import Plan
from open_inwoner.qmatic.client import NoServiceConfigured, qmatic_client_factory
from open_inwoner.questionnaire.models import QuestionnaireStep
from open_inwoner.utils.views import CommonPageMixin

from .mixins import ProfileLogMixin

logger = structlog.stdlib.get_logger(__name__)


class MyProfileView(
    ProfileLogMixin,
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
            self.log_newsletter_subscription_modified(success=False)
            return self.form_invalid(form)

        messages.success(self.request, _("Uw wijzigingen zijn opgeslagen"))
        self.log_newsletter_subscription_modified(success=True)
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

        if user.is_eherkenning_user:
            overview_anchor = ("#business-overview", _("Bedrijfsgegevens"))
        else:
            overview_anchor = ("#personal-info", _("Persoonlijke gegevens"))

        context["anchors"] = [
            overview_anchor,
            ("#profile-remove", _("Profiel verwijderen")),
        ]
        if self.config and self.config.selected_categories:
            context["anchors"].insert(1, ("#overview", _("Overzicht")))
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
            LoginTypeChoices.eidas_person_bsn,
            LoginTypeChoices.eidas_person_pseudo_id,
            LoginTypeChoices.eidas_company,
        )
        context["inbox_page_is_published"] = inbox_page_is_published()
        context["benefits_page_is_published"] = benefits_page_is_published()
        context["case_page_is_published"] = case_page_is_published()
        context["products_page_is_published"] = products_page_is_published()

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
            self.log_user_deleted(instance)
            instance.delete()
            request.session.flush()

            return redirect(reverse("login"))
        else:
            messages.warning(request, _("Uw account kon niet worden verwijderd"))
            return redirect("profile:detail")


class EditProfileView(
    ProfileLogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
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
        user: User = self.get_object()

        # Save locally first so that user.digital_addresses reflects the new
        # values before we sync outward (eventual-consistency model).
        form.save()

        if any(key in form.changed_data for key in ("email", "phonenumber")):
            klanten_config = KlantenSysteemConfig.get_solo()
            failed_services = []
            if klanten_config.has_api_service_configured(KlantenServiceType.ESUITE):
                try:
                    self.update_klant_via_esuite(
                        {k: form.cleaned_data[k] for k in form.changed_data}, user
                    )
                except Exception:
                    logger.exception("eSuite failed during profile update", user=user)
                    failed_services.append("eSuite")
            if klanten_config.has_api_service_configured(KlantenServiceType.OPENKLANT2):
                try:
                    self.update_klant_via_openklant(
                        {k: form.cleaned_data[k] for k in form.changed_data}, user
                    )
                except Exception:
                    logger.exception(
                        "OpenKlant failed during profile update", user=user
                    )
                    failed_services.append("OpenKlant")
            if failed_services:
                messages.error(
                    request=self.request,
                    message=_(
                        "Your changes could not be saved due to technical problems. "
                        "Please try again later"
                    ),
                )
                self.log_profile_update_failed(user, failed_services, form.changed_data)
                return HttpResponseRedirect(self.get_success_url())

        messages.success(self.request, _("Uw wijzigingen zijn opgeslagen"))
        self.log_profile_modified(user)
        return HttpResponseRedirect(self.get_success_url())

    def update_klant_via_openklant(self, user_form_data: dict, user: User) -> bool:
        """
        Update the user `partij` in OpenKlant from `user_form_data`

        If applicable, clean up old contact information in OpenKlant before the update

        Note: we only delete old contact info that is present in both OpenKlant and OIP;
              the possibility that other contact info has been added by external sources
              cannot be excluded
        """
        try:
            service = OpenKlant2Service()
        except Exception:
            logger.warning("OpenKlant2Service failed to build")
            return False

        partij, created = service.get_or_create_partij_for_user(user)

        if partij:
            return service.update_partij_from_user_data(
                partij_uuid=partij["uuid"],
                user=user,
            )

        return False

    def update_klant_via_esuite(self, user_form_data: dict, user: User) -> bool:
        field_mapping = {
            "emailadres": "email",
            "telefoonnummer": "phonenumber",
        }
        update_data = {
            api_name: user_form_data[local_name]
            for api_name, local_name in field_mapping.items()
            if user_form_data.get(local_name)
        }

        try:
            service = eSuiteKlantenService()
        except Exception:
            logger.warning("eSuiteKlantenService failed to build")
            return False

        if fetch_params := service.get_fetch_parameters(user):
            try:
                klant, created = service.get_or_create_klant(
                    fetch_params=fetch_params, user=user
                )
                if klant and not created:
                    return bool(
                        service.update_klant_from_user(
                            klant, user, update_fields=list(update_data.keys())
                        )
                    )
            except (KlantAPIError, requests.RequestException):
                logger.error("Error updating klant via eSuite")
                return False

        return bool(klant)

    def get_form_class(self):
        user = self.request.user
        if user.is_bsn_user_with_brp:
            return BrpUserForm
        return super().get_form_class()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MyCategoriesView(
    ProfileLogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    UpdateView,
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
        self.log_categories_modified(self.get_object())
        return HttpResponseRedirect(self.get_success_url())


class MyDataView(
    ProfileLogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    TemplateView,
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
        self.log_brp_data_requested()
        bsn = self.request.user.bsn
        if not bsn:
            return None
        try:
            client = BRPClient.from_config()
        except ImproperlyConfigured:
            logger.warning("no service configured for Haal Centraal")
            return None

        try:
            persoon = client.fetch_brp_data_for_bsn(bsn)
        except Exception:
            logger.exception("Failed to fetch BRP data for user")
            return None

        if persoon is None:
            return None
        return BRPData.from_persoon(persoon)


class MyNotificationsView(
    ProfileLogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
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
        user: User = self.get_object()

        if "case_notification_channel" in form.changed_data:
            self.update_klant_via_esuite(user)

        messages.success(self.request, _("Uw wijzigingen zijn opgeslagen"))
        self.log_change(user, _("users notifications were modified"))
        return HttpResponseRedirect(self.get_success_url())

    def update_klant_via_esuite(self, user: User):
        try:
            service = eSuiteKlantenService()
        except Exception:
            logger.warning("eSuiteKlantenService failed to build")
            return

        if fetch_params := service.get_fetch_parameters(user):
            try:
                klant, created = service.get_or_create_klant(
                    fetch_params=fetch_params, user=user
                )
                if klant and not created:
                    service.update_klant_from_user(
                        klant,
                        user,
                        update_fields=["toestemmingZaakNotificatiesAlleenDigitaal"],
                    )
            except (KlantAPIError, requests.RequestException):
                logger.error("Error updating klant via eSuite")


class UserAppointmentsView(
    ProfileLogMixin,
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
                client = qmatic_client_factory()
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
