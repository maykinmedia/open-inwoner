import logging

from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.utils.encoding import iri_to_uri
from django.utils.functional import cached_property
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from mail_editor.helpers import find_template
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.mail.service import send_contact_confirmation_mail
from open_inwoner.openklant.api_models import (
    ContactMomentCreateData,
    Klant,
    MedewerkerIdentificatie,
)
from open_inwoner.openklant.clients import KlantenClient, build_klanten_client
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.forms import ContactForm
from open_inwoner.openklant.models import ESuiteKlantConfig, KlantenSysteemConfig
from open_inwoner.openklant.services import OpenKlant2Service, eSuiteVragenService
from open_inwoner.openklant.views.utils import generate_question_answer_pair
from open_inwoner.utils.views import CommonPageMixin, LogMixin

logger = logging.getLogger(__name__)


class ContactFormView(CommonPageMixin, LogMixin, BaseBreadcrumbMixin, FormView):
    form_class = ContactForm
    template_name = "pages/contactform/form_wrap.html"  # inner ("structure") template rendered by CMS plugin
    klanten_config = KlantenSysteemConfig
    klanten_client: KlantenClient | None
    vragen_service: OpenKlant2Service | eSuiteVragenService | None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.klanten_client = None
        self.vragen_service = None

        self.klanten_config = KlantenSysteemConfig.get_solo()
        match self.klanten_config.primary_backend:
            case KlantenServiceType.ESUITE.value:
                self.klanten_client = build_klanten_client()
                self.vragen_service = eSuiteVragenService()
            case KlantenServiceType.OPENKLANT2.value:
                self.vragen_service = OpenKlant2Service()
            case _:
                logger.info("No klanten/vragen service configured for contactform")

    @cached_property
    def crumbs(self):
        return [(_("Contact formulier"), self.request.path)]

    def page_title(self):
        return _("Contact formulier")

    def get_success_url(self):
        success_url = self.request.path
        if url_has_allowed_host_and_scheme(
            success_url,
            allowed_hosts=[self.request.get_host()],
            require_https=settings.IS_HTTPS,
        ):
            return iri_to_uri(success_url)
        return reverse("contactform")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        captcha_question = self.request.session.get("captcha_question")
        captcha_answer = self.request.session.get("captcha_answer")

        if not (captcha_question and captcha_answer):
            captcha_question, captcha_answer = generate_question_answer_pair()

        self.request.session["captcha_question"] = captcha_question
        self.request.session["captcha_answer"] = captcha_answer

        kwargs["user"] = self.request.user
        kwargs["request_session"] = self.request.session
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            initial.update(
                {
                    "first_name": self.request.user.first_name,
                    "infix": self.request.user.infix,
                    "last_name": self.request.user.last_name,
                    "email": self.request.user.email,
                    "phonenumber": self.request.user.phonenumber,
                }
            )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        has_contactform_configuration = (
            self.klanten_config.has_contactform_configuration
        )
        if not self.request.user.is_authenticated:
            has_contactform_configuration = (
                has_contactform_configuration
                and self.vragen_service.supports_anonymous_questions
            )
        context["has_form_configuration"] = has_contactform_configuration

        return context

    def set_result_message(self, success: bool):
        if success:
            messages.add_message(self.request, messages.SUCCESS, _("Vraag verstuurd!"))
        else:
            messages.add_message(
                self.request,
                messages.ERROR,
                _("Probleem bij versturen van de vraag."),
            )

    def form_valid(self, form: ContactForm):
        email_success = False
        api_success = False
        send_confirmation = False
        api_user_email = None

        if self.klanten_config.register_contact_email:
            email_success = self.register_by_email(
                form, self.klanten_config.register_contact_email
            )
            send_confirmation = email_success

        if self.klanten_config.register_contact_via_api:
            api_success, api_user_email = self.register_by_api(
                form, self.klanten_config
            )
            if api_success:
                send_confirmation = self.klanten_config.send_email_confirmation
            # else keep the send_confirmation if email set it

        user_email = (
            api_user_email  # pulled from klanten api
            or getattr(self.request.user, "email", None)
            or form.cleaned_data["email"]
        )

        if send_confirmation:
            send_contact_confirmation_mail(
                user_email, form.cleaned_data["subject"].subject
            )

        self.set_result_message(email_success or api_success)

        return super().form_valid(form)

    def register_by_email(self, form: ContactForm, recipient_email: str):
        template = find_template("contactform_registration")

        context = {
            k: form.cleaned_data[k]
            for k in (
                "subject",
                "email",
                "phonenumber",
                "question",
            )
        }

        parts = (form.cleaned_data[k] for k in ("first_name", "infix", "last_name"))
        context["name"] = " ".join(p for p in parts if p)

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

    def register_by_api(self, form, config: KlantenSysteemConfig):
        if config.primary_backend == KlantenServiceType.ESUITE.value:
            return self._register_via_esuite(
                form, esuite_config=ESuiteKlantConfig.get_solo()
            )
        return self._register_via_openklant2(form)

    def _register_via_openklant2(self, form: ContactForm):
        user = self.request.user

        partij, _ = self.vragen_service.get_or_create_partij_for_user(user)

        cleaned_data = form.cleaned_data
        question = cleaned_data["question"]
        subject = cleaned_data["subject"].subject

        question = self.vragen_service.create_question(
            partij_uuid=partij["uuid"], question=question, subject=subject
        )

        self.log_system_action(
            "registered question via OpenKlant", user=self.request.user
        )

        # TODO: get email from partij
        return True, getattr(user, "email", None)

    def _register_via_esuite(
        self,
        form: ContactForm,
        esuite_config: ESuiteKlantConfig,
    ) -> tuple[bool, str]:
        assert esuite_config.has_api_configuration

        klant = self._fetch_klant()
        if klant:
            self._update_klant_with_form_data(klant, form.cleaned_data)

        contactmoment = self._create_contactmoment(
            form.cleaned_data, esuite_config, klant
        )

        if not contactmoment:
            self.log_system_action(
                "error while registering contactmoment by API", user=self.request.user
            )
            return False, getattr(klant, "emailadres", None)
        self.log_system_action(
            "registered contactmoment via eSuite", user=self.request.user
        )
        return True, getattr(klant, "emailadres", None)

    def _fetch_klant(self) -> Klant | None:
        user = self.request.user

        if not user.is_authenticated or (not user.bsn and not user.kvk):
            return

        if not self.klanten_client:
            return

        if not self.vragen_service:
            return

        klant = self.klanten_client.retrieve_klant(
            **self.vragen_service.get_fetch_parameters(self.request.user)
        )

        self.log_system_action("retrieved klant for BSN or KVK user", user=user)

        return klant

    def _update_klant_with_form_data(self, klant: Klant, form_data: dict):
        user = self.request.user

        update_data = {}
        user_email = form_data.get("email")
        phonenumber = form_data.get("phonenumber")

        if not klant.emailadres and user_email:
            update_data["emailadres"] = user_email
        if not klant.telefoonnummer and phonenumber:
            update_data["telefoonnummer"] = phonenumber
        if update_data:
            self.klanten_client.partial_update_klant(klant, update_data)
            self.log_system_action(
                "patched klant from user with missing fields: {patched}".format(
                    patched=", ".join(sorted(update_data.keys()))
                ),
                user=user,
            )

    def _create_contactmoment(
        self,
        form_data: dict,
        klanten_config: ESuiteKlantConfig,
        klant: Klant | None = None,
    ):
        subject = form_data["subject"].subject
        subject_code = form_data["subject"].esuite_subject_code
        text = form_data["question"]

        if not klant:
            # if we don't have a BSN and can't create a Klant we'll add contact info to the tekst
            parts = [form_data[k] for k in ("first_name", "infix", "last_name")]
            full_name = " ".join(p for p in parts if p)

            text = _("{text}\n\nNaam: {full_name}").format(
                text=text, full_name=full_name
            )

            self.log_system_action(
                "could not retrieve or create klant for user, appended info to message",
                user=self.request.user,
            )

        data = ContactMomentCreateData(
            bronorganisatie=klanten_config.register_bronorganisatie_rsin,
            tekst=text,
            type=klanten_config.register_type,
            kanaal=klanten_config.register_channel,
            onderwerp=subject_code or subject,
        )

        if not self.request.user.is_authenticated:
            # Ensure we don't send an empty (and thus invalid) email or phonenumber
            contactgegevens = {}
            if form_data["email"]:
                contactgegevens["emailadres"] = form_data["email"]

            if form_data["phonenumber"]:
                contactgegevens["telefoonnummer"] = form_data["phonenumber"]

            if contactgegevens:
                data["contactgegevens"] = contactgegevens

        if employee_id := klanten_config.register_employee_id:
            data["medewerkerIdentificatie"] = MedewerkerIdentificatie(
                identificatie=employee_id
            )

        contactmoment = self.vragen_service.create_contactmoment(data, klant=klant)
        if not contactmoment:
            messages.warning(
                request=self.request,
                message=_("Your question could not be saved. Please try again later."),
            )
        return contactmoment
