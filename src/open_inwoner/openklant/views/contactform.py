from django.contrib import messages
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from mail_editor.helpers import find_template
from view_breadcrumbs import BaseBreadcrumbMixin
from zds_client import ClientError

from open_inwoner.openklant.forms import ContactForm
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.wrap import (
    create_contactmoment,
    create_klant,
    fetch_klant_for_bsn,
    patch_klant,
)
from open_inwoner.utils.views import CommonPageMixin, LogMixin


class ContactFormView(CommonPageMixin, LogMixin, BaseBreadcrumbMixin, FormView):
    form_class = ContactForm
    template_name = "pages/contactform/form.html"

    message_success = _("Vraag verstuurd!")
    message_failure = _("Probleem bij versturen van de vraag.")

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
        context["has_configuration"] = config.has_form_configuration()
        return context

    def form_valid(self, form):
        config = OpenKlantConfig.get_solo()
        if config.register_email:
            self.register_by_email(form, config.register_email)
        if config.register_contact_moment:
            self.register_by_api(form, config)
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

        parts = [form.cleaned_data[k] for k in ("first_name", "infix", "last_name")]
        context["name"] = " ".join(p for p in parts if p)

        success = template.send_email([recipient_email], context)

        if success:
            messages.add_message(self.request, messages.SUCCESS, self.message_success)
            self.log_system_action(
                "registered contactmoment by email", user=self.request.user
            )
        else:
            messages.add_message(self.request, messages.ERROR, self.message_failure)
            self.log_system_action(
                "error while registering contactmoment by email",
                user=self.request.user,
            )

    def register_by_api(self, form, config: OpenKlantConfig):
        assert config.has_api_configuration()

        # fetch/update/create klant
        if self.request.user.is_authenticated and self.request.user.bsn:
            klant = fetch_klant_for_bsn(self.request.user.bsn)
            if klant:
                self.log_system_action(
                    "retrieved klant for BSN-user", user=self.request.user
                )

                # check if we have some data missing from the Klant
                update_data = {}
                if not klant.emailadres and form.cleaned_data["email"]:
                    update_data["emailadres"] = form.cleaned_data["email"]
                if not klant.telefoonnummer and form.cleaned_data["phonenumber"]:
                    update_data["telefoonnummer"] = form.cleaned_data["phonenumber"]
                if update_data:
                    patch_klant(klant, update_data)
                    self.log_system_action(
                        f"patched klant from user with missing fields: {', '.join(sorted(update_data.keys()))}",
                        user=self.request.user,
                    )
            else:
                self.log_system_action(
                    "could not retrieve klant for BSN-user", user=self.request.user
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
            # registering klanten won't work in e-Suite as it always pulls from BRP (but try anyway and fallback to appending details to tekst if fails)
            klant = create_klant(data)
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
        question = form.cleaned_data["question"]
        text = f"{subject}\n\n{question}"

        if not klant:
            # if we don't have a BSN and can't create a Klant we'll add contact info to the tekst
            parts = [form.cleaned_data[k] for k in ("first_name", "infix", "last_name")]
            full_name = " ".join(p for p in parts if p)
            text = f"{text}\n\nNaam: {full_name}"

            if form.cleaned_data["email"]:
                text = f"{text}\nEmail: {form.cleaned_data['email']}"

            if form.cleaned_data["phonenumber"]:
                text = f"{text}\nTelefoonnummer: {form.cleaned_data['phonenumber']}"

            self.log_system_action(
                "could not retrieve or create klant for user, appended info to message",
                user=self.request.user,
            )

        data = {
            "bronorganisatie": config.register_bronorganisatie_rsin,
            "tekst": text,
            "type": config.register_type,
            "kanaal": "Internet",
            "medewerkerIdentificatie": {
                "identificatie": config.register_employee_id,
            },
        }
        contactmoment = create_contactmoment(data, klant=klant)

        if contactmoment:
            messages.add_message(self.request, messages.SUCCESS, self.message_success)
            self.log_system_action(
                "registered contactmoment by API", user=self.request.user
            )
        else:
            messages.add_message(self.request, messages.ERROR, self.message_failure)
            self.log_system_action(
                "error while registering contactmoment by API", user=self.request.user
            )
