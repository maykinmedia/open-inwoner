import re
from typing import Tuple

from django.contrib import messages
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from mail_editor.helpers import find_template
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.openklant.forms import ContactForm
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.wrap import (
    create_contactmoment,
    create_klant,
    fetch_klant_for_bsn,
)
from open_inwoner.utils.views import CommonPageMixin


class ContactFormView(CommonPageMixin, BaseBreadcrumbMixin, FormView):
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
        else:
            messages.add_message(self.request, messages.ERROR, self.message_failure)

    def register_by_api(self, form, config: OpenKlantConfig):
        assert config.has_form_configuration()

        # fetch/update/create klant
        if self.request.user.is_authenticated and self.request.user.bsn:
            klant = fetch_klant_for_bsn(self.request.user.bsn)

            # TODO update klant phone/email? (other ticket)
        else:
            # TODO according to taiga #1437 we should disable Klanten/Contacten API if Digid is not enabled
            # TODO registering klanten won't work in e-Suite as it always pulls from BRP
            data = {
                "bronorganisatie": config.register_bronorganisatie_rsin,
                "voornaam": form.cleaned_data["first_name"],
                "voorvoegselAchternaam": form.cleaned_data["infix"],
                "achternaam": form.cleaned_data["last_name"],
                "emailadres": form.cleaned_data["email"],
                "telefoonnummer": form.cleaned_data["phonenumber"],
            }
            klant = create_klant(data)

        # create contact moment
        subject = form.cleaned_data["subject"].subject
        body = form.cleaned_data["question"]

        data = {
            "bronorganisatie": config.register_bronorganisatie_rsin,
            "tekst": f"{subject}\n\n{body}",
            "type": config.register_type,
            "kanaal": "Internet",
            "medewerkerIdentificatie": {
                "identificatie": config.register_employee_id,
            },
        }
        contactmoment = create_contactmoment(data, klant=klant)

        if contactmoment:
            messages.add_message(self.request, messages.SUCCESS, self.message_success)
        else:
            messages.add_message(self.request, messages.ERROR, self.message_failure)
