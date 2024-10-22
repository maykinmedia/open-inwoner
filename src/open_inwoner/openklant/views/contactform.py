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
from open_inwoner.openklant.clients import (
    KlantenClient,
    build_contactmomenten_client,
    build_klanten_client,
)
from open_inwoner.openklant.forms import ContactForm
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.views.utils import generate_question_answer_pair
from open_inwoner.openklant.wrap import get_fetch_parameters
from open_inwoner.utils.views import CommonPageMixin, LogMixin


class ContactFormView(CommonPageMixin, LogMixin, BaseBreadcrumbMixin, FormView):
    form_class = ContactForm
    template_name = "pages/contactform/form_wrap.html"  # inner ("structure") template rendered by CMS plugin
    klanten_client: KlantenClient | None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.klanten_client = build_klanten_client()

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
        config = OpenKlantConfig.get_solo()
        context["has_form_configuration"] = config.has_form_configuration()
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
        config = OpenKlantConfig.get_solo()

        email_success = False
        api_success = False
        send_confirmation = False
        api_user_email = None

        if config.register_email:
            email_success = self.register_contactmoment_by_email(
                form, config.register_email
            )
            send_confirmation = email_success

        if config.register_contact_moment:
            api_success, api_user_email = self.register_contactmoment_by_api(
                form, config
            )
            if api_success:
                send_confirmation = config.send_email_confirmation
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

    def register_contactmoment_by_email(self, form: ContactForm, recipient_email: str):
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

    def register_contactmoment_by_api(
        self,
        form: ContactForm,
        klanten_config: OpenKlantConfig,
    ) -> tuple[bool, str]:
        assert klanten_config.has_api_configuration()

        klant = self._fetch_klant()
        if klant:
            self._update_klant_with_form_data(klant, form.cleaned_data)

        contactmoment = self._create_contactmoment(
            form.cleaned_data, klanten_config, klant
        )

        if not contactmoment:
            self.log_system_action(
                "error while registering contactmoment by API", user=self.request.user
            )
            return False, getattr(klant, "emailadres", None)
        self.log_system_action(
            "registered contactmoment by API", user=self.request.user
        )
        return True, getattr(klant, "emailadres", None)

    def _fetch_klant(self) -> Klant | None:
        user = self.request.user

        if not user.is_authenticated or (not user.bsn and not user.kvk):
            return

        if not self.klanten_client:
            return

        klant = self.klanten_client.retrieve_klant(**get_fetch_parameters(self.request))

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
        klanten_config: OpenKlantConfig,
        klant: Klant | None = None,
    ):
        if not (contactmoment_client := build_contactmomenten_client()):
            return

        subject = form_data["subject"].subject
        subject_code = form_data["subject"].subject_code
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

        return contactmoment_client.create_contactmoment(data, klant=klant)
