from django.contrib import messages
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from mail_editor.helpers import find_template
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.mail.service import send_contact_confirmation_mail
from open_inwoner.openklant.clients import build_client
from open_inwoner.openklant.forms import ContactForm
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.wrap import get_fetch_parameters
from open_inwoner.utils.views import CommonPageMixin, LogMixin


class ContactFormView(CommonPageMixin, LogMixin, BaseBreadcrumbMixin, FormView):
    form_class = ContactForm
    template_name = "pages/contactform/form.html"

    @cached_property
    def crumbs(self):
        return [(_("Contact formulier"), self.request.path)]

    def page_title(self):
        return _("Contact formulier")

    def get_success_url(self):
        return self.request.path

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
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

    def form_valid(self, form):
        config = OpenKlantConfig.get_solo()

        # this logic is very gnarly as there are multiple destinations, and sources of user-email

        user = self.request.user
        user_email = None
        api_user_email = None
        email_success = False
        api_success = False
        send_confirmation = False

        if user.is_authenticated and user.email:
            user_email = user.email

        if config.register_email:
            email_success = self.register_by_email(form, config.register_email)
            send_confirmation = email_success

        if config.register_contact_moment:
            api_success, api_user_email = self.register_by_api(form, config)
            if api_success:
                if config.api_sends_email_confirmation:
                    send_confirmation = False
                else:
                    send_confirmation = True
            # else keep the send_confirmation if email set it

        # it is possible we don't have an email, user didn't enter it but we got it from the Klant
        user_email = api_user_email or user_email or form.cleaned_data.get("email")

        if send_confirmation:
            send_contact_confirmation_mail(
                user_email, form.cleaned_data["subject"].subject
            )

        self.set_result_message(email_success or api_success)

        return super().form_valid(form)

    def register_by_email(self, form, recipient_email):
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

    def register_by_api(self, form, config: OpenKlantConfig) -> tuple[bool, str]:
        assert config.has_api_configuration()

        # the form set the email if we didn't ask but have it on the user
        user_email = form.cleaned_data.get("email")

        # fetch/update/create klant
        klant = None
        if klanten_client := build_client("klanten"):
            if self.request.user.is_authenticated and (
                self.request.user.bsn or self.request.user.kvk
            ):
                klant = klanten_client.retrieve_klant(
                    **get_fetch_parameters(self.request)
                )
                if klant:
                    self.log_system_action(
                        "retrieved klant for BSN or KVK user", user=self.request.user
                    )
                    user_email = klant.emailadres or user_email

                    # check if we have some data missing from the Klant
                    update_data = {}
                    if not klant.emailadres and user_email:
                        update_data["emailadres"] = user_email
                    if not klant.telefoonnummer and form.cleaned_data["phonenumber"]:
                        update_data["telefoonnummer"] = form.cleaned_data["phonenumber"]
                    if update_data:
                        klanten_client.partial_update_klant(klant, update_data)
                        self.log_system_action(
                            "patched klant from user with missing fields: {patched}".format(
                                patched=", ".join(sorted(update_data.keys()))
                            ),
                            user=self.request.user,
                        )
                else:
                    self.log_system_action(
                        "could not retrieve klant for BSN or KVK user",
                        user=self.request.user,
                    )

            else:
                data = {
                    "bronorganisatie": config.register_bronorganisatie_rsin,
                    "voornaam": form.cleaned_data["first_name"],
                    "voorvoegselAchternaam": form.cleaned_data["infix"],
                    "achternaam": form.cleaned_data["last_name"],
                    "emailadres": form.cleaned_data["email"],
                    "telefoonnummer": form.cleaned_data["phonenumber"],
                }
                # registering klanten won't work in e-Suite as it always pulls from BRP
                # (but try anyway and fallback to appending details to tekst if fails)
                klant = klanten_client.create_klant(data=data)

                if klant:
                    if self.request.user.is_authenticated:
                        self.log_system_action(
                            "created klant for basic authenticated user",
                            user=self.request.user,
                        )
                    else:
                        self.log_system_action("created klant for anonymous user")

        # create contact moment
        subject = form.cleaned_data["subject"].subject
        subject_code = form.cleaned_data["subject"].subject_code
        question = form.cleaned_data["question"]
        text = question

        if not klant:
            # if we don't have a BSN and can't create a Klant we'll add contact info to the tekst
            parts = [form.cleaned_data[k] for k in ("first_name", "infix", "last_name")]
            full_name = " ".join(p for p in parts if p)

            text = _("{text}\n\nNaam: {full_name}").format(
                text=text, full_name=full_name
            )

            if form.cleaned_data["email"]:
                text = _("{text}\nEmail: {email}").format(
                    text=text, email=form.cleaned_data["email"]
                )

            if form.cleaned_data["phonenumber"]:
                text = _("{text}\nTelefoonnummer: {phone}").format(
                    text=text, phone=form.cleaned_data["phonenumber"]
                )

            self.log_system_action(
                "could not retrieve or create klant for user, appended info to message",
                user=self.request.user,
            )

        data = {
            "bronorganisatie": config.register_bronorganisatie_rsin,
            "tekst": text,
            "type": config.register_type,
            "kanaal": config.register_channel,
            "onderwerp": subject_code or subject,
            "medewerkerIdentificatie": {
                "identificatie": config.register_employee_id,
            },
        }

        contactmoment = None
        if contactmoment_client := build_client("contactmomenten"):
            contactmoment = contactmoment_client.create_contactmoment(data, klant=klant)

        if contactmoment:
            self.log_system_action(
                "registered contactmoment by API", user=self.request.user
            )
            return True, user_email
        else:
            self.log_system_action(
                "error while registering contactmoment by API", user=self.request.user
            )
            return False, user_email
