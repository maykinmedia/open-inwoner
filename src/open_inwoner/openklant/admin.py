from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline
from solo.admin import SingletonModelAdmin

from .models import ContactFormSubject, OpenKlantConfig


class ContactFormSubjectInlineAdmin(OrderedTabularInline):
    model = ContactFormSubject
    fields = ("subject", "order", "move_up_down_links")
    readonly_fields = ("order", "move_up_down_links")
    ordering = ("order",)
    extra = 0


class OpenKlantConfigAdminForm(forms.ModelForm):
    class Meta:
        model = OpenKlantConfig
        fields = "__all__"

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)

        if cleaned_data["register_contact_moment"]:
            msg = _(
                "Voor registratie in de Klanten en Contactmomenten API is dit veld vereist."
            )
            for field_name in OpenKlantConfig.register_api_required_fields:
                if not cleaned_data[field_name]:
                    self.add_error(field_name, msg)


@admin.register(OpenKlantConfig)
class OpenKlantConfigAdmin(OrderedInlineModelAdminMixin, SingletonModelAdmin):
    form = OpenKlantConfigAdminForm
    inlines = [
        ContactFormSubjectInlineAdmin,
    ]
    fieldsets = [
        (
            _("Email registratie"),
            {
                "fields": [
                    "register_email",
                ],
            },
        ),
        (
            _("Klanten en Contacten API registratie"),
            {
                "fields": [
                    "register_contact_moment",
                    "register_bronorganisatie_rsin",
                    "register_type",
                    "register_employee_id",
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
