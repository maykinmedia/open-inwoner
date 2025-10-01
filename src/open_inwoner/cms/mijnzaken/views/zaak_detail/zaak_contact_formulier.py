import logging
from typing import cast

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from django_htmx.http import HttpResponseClientRedirect
from mail_editor.helpers import find_template

from open_inwoner.accounts.models import User
from open_inwoner.mail.service import send_contact_confirmation_mail
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.models import (
    ESuiteKlantConfig,
    KlantenSysteemConfig,
    OpenKlant2Config,
)
from open_inwoner.openklant.services import (
    OpenKlant2Service,
    eSuiteKlantenService,
    eSuiteVragenService,
)
from open_inwoner.openzaak.models import ZaakTypeConfig, ZGWApiGroupConfig
from open_inwoner.utils.views import LogMixin

from ...forms import CaseContactForm
from ..mixins import CaseAccessMixin

logger = logging.getLogger(__name__)


class CaseContactFormView(CaseAccessMixin, LogMixin, FormView):
    template_name = "pages/cases/contact_form.html"
    form_class = CaseContactForm

    def post(self, request, *args, **kwargs):
        try:
            api_group = ZGWApiGroupConfig.objects.get(pk=self.kwargs["api_group_id"])
        except ZGWApiGroupConfig.DoesNotExist as exc:
            logger.exception("Non-existent ZGWApiGroupConfig passed")
            raise Http404 from exc

        form = self.get_form()

        if form.is_valid():
            klant_config = KlantenSysteemConfig.get_solo()

            email_success = False
            api_success = False
            send_confirmation = False

            if klant_config.register_contact_email:
                form.cleaned_data["question"] += (
                    f"\n\nCase number: {self.case.identificatie}"
                )
                email_success = self.register_by_email(
                    form, klant_config.register_contact_email
                )
                send_confirmation = email_success

            if klant_config.register_contact_via_api:
                api_success = self.register_by_api(form, api_group)
                if api_success:
                    send_confirmation = klant_config.send_email_confirmation
                # else keep the send_confirmation if email set it

            if send_confirmation:
                subject = _("Case: {case_identification}").format(
                    case_identification=self.case.identificatie
                )
                send_contact_confirmation_mail(self.request.user.email, subject)

            self.set_result_message(email_success or api_success)

            return HttpResponseClientRedirect(
                reverse(
                    "cases:case_detail",
                    kwargs={
                        "object_id": str(self.case.uuid),
                        "api_group_id": self.kwargs["api_group_id"],
                    },
                )
            )
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse(
            "cases:case_detail_contact_form", kwargs={"object_id": str(self.case.uuid)}
        )

    def set_result_message(self, success: bool):
        if success:
            messages.add_message(self.request, messages.SUCCESS, _("Vraag verstuurd!"))
        else:
            messages.add_message(
                self.request,
                messages.ERROR,
                _("Probleem bij versturen van de vraag."),
            )

    def register_by_email(self, form, recipient_email):
        template = find_template("contactform_registration")

        context = {
            "subject": _("Case: {case_identification}").format(
                case_identification=self.case.identificatie
            ),
            "email": self.request.user.email,
            "phonenumber": self.request.user.phonenumber,
            "question": form.cleaned_data["question"],
            "name": self.request.user.get_full_name(),
        }

        success = template.send_email([recipient_email], context)

        if success:
            self.log_system_action(
                "registered contactmoment by email", user=self.request.user
            )
            return True
        else:
            self.log_system_action(
                "error while registering contactmoment by email",
                user=self.request.user,
            )
            return False

    def register_by_api(self, form, api_group: ZGWApiGroupConfig):
        if not api_group.klant_backend:
            return

        match api_group.klant_backend:
            case KlantenServiceType.ESUITE.value:
                return self._register_via_esuite(
                    form, config=ESuiteKlantConfig.get_solo()
                )
            case KlantenServiceType.OPENKLANT2.value:
                return self._register_via_openklant(
                    form, config=OpenKlant2Config.get_solo()
                )
            case _:
                logger.error(
                    "Got non-existent klanten backend %s", api_group.klant_backend
                )

    def _register_via_openklant(self, form, config: OpenKlant2Config) -> bool:
        user = cast(User, self.request.user)
        service = OpenKlant2Service(config=config)

        partij, _ = service.get_or_create_partij_for_user(user)

        if not partij:
            return False

        cleaned_data = form.cleaned_data
        question = cleaned_data["question"]

        question = service.create_question_for_zaak(
            partij_uuid=partij["uuid"],
            question=question,
            subject=self.case.omschrijving,
            zaak=self.case,
        )

        return bool(question)

    def _register_via_esuite(self, form, config: ESuiteKlantConfig):
        if not config.has_api_configuration:
            raise ImproperlyConfigured("Missing eSuite API configuration")

        try:
            ztc = ZaakTypeConfig.objects.filter_case_type(self.case.zaaktype).get()
        except ObjectDoesNotExist:
            ztc = None

        klant = None
        user = cast(User, self.request.user)
        try:
            service = eSuiteKlantenService(config=config)
        except (ImproperlyConfigured, RuntimeError):
            self.log_system_action("could not build client for klanten API")
        else:
            fetch_params = service.get_fetch_parameters(user)
            klant, created = service.get_or_create_klant(
                fetch_params=fetch_params, user=user
            )
            if not klant:
                self.log_system_action(
                    "could not create klant for user", user=self.request.user
                )
            else:
                if created:
                    self.log_system_action(
                        (
                            "created klant for basic authenticated user"
                            if created
                            else "retrieved klant for user"
                        ),
                        user=self.request.user,
                    )

        # create contact moment
        question = form.cleaned_data["question"]
        data = {
            "bronorganisatie": config.register_bronorganisatie_rsin,
            "tekst": question,
            "type": config.register_type,
            "kanaal": config.register_channel,
        }
        if employee_id := config.register_employee_id:
            data["medewerkerIdentificatie"] = {"identificatie": employee_id}
        if ztc and ztc.contact_subject_code:
            data["onderwerp"] = ztc.contact_subject_code

        try:
            service = eSuiteVragenService(config=config)
        except ImproperlyConfigured:
            logger.error("Failed to build eSuiteVragenService")
            return

        contactmoment = service.create_contactmoment(data, klant=klant)

        if not contactmoment:
            self.log_system_action(
                "error while registering contactmoment by API", user=self.request.user
            )
            messages.error(
                request=self.request,
                message=_("Your question could not be saved. Please try again later."),
            )
            return False

        self.log_system_action(
            "registered contactmoment by API", user=self.request.user
        )
        objectcontactmoment = service.create_objectcontactmoment(
            contactmoment, self.case
        )
        if objectcontactmoment:
            self.log_system_action(
                "registered objectcontactmoment by API", user=self.request.user
            )
        else:
            self.log_system_action(
                "error while registering objectcontactmoment by API",
                user=self.request.user,
            )

        # We'll mark this call as successful if the cotactmoment is created, independent of
        # whether we've successfully associated the contactmoment with the case, because we
        # still want the notification email to be sent.
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_form"] = self.get_form()
        context["hxpost_contact_action"] = reverse(
            "cases:case_detail_contact_form", kwargs=self.kwargs
        )
        return context
