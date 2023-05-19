from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import ContactFormSubject, OpenKlantConfig


class ContactFormSubjectInlineAdmin(admin.TabularInline):
    model = ContactFormSubject
    fields = [
        "subject",
    ]
    extra = 0


class OpenKlantConfigAdminForm(forms.ModelForm):
    class Meta:
        model = OpenKlantConfig
        fields = "__all__"

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)

        register_contact_moment = cleaned_data["register_contact_moment"]
        klanten_service = cleaned_data["klanten_service"]
        contactmomenten_service = cleaned_data["contactmomenten_service"]
        register_bronorganisatie_rsin = cleaned_data["register_bronorganisatie_rsin"]

        if register_contact_moment:
            if not klanten_service or not contactmomenten_service:
                msg = _(
                    "Voor registratie in de Klanten en Contactmomenten API zijn services vereist."
                )
                self.add_error("register_contact_moment", msg)
                if not klanten_service:
                    self.add_error("klanten_service", msg)
                if not contactmomenten_service:
                    self.add_error("contactmomenten_service", msg)

            if not register_bronorganisatie_rsin:
                msg = _(
                    "Voor registratie in de Klanten en Contactmomenten API is een bronorganisatie RSIN vereist."
                )
                self.add_error("register_bronorganisatie_rsin", msg)


@admin.register(OpenKlantConfig)
class OpenKlantConfigAdmin(SingletonModelAdmin):
    form = OpenKlantConfigAdminForm
    inlines = [
        ContactFormSubjectInlineAdmin,
    ]
    fieldsets = [
        (
            _("Registratie"),
            {
                "fields": [
                    "register_email",
                    "register_contact_moment",
                    "register_bronorganisatie_rsin",
                ],
            },
        ),
        (
            _("Services"),
            {
                "fields": [
                    "klanten_service",
                    "contactmomenten_service",
                ],
            },
        ),
    ]
