from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline
from solo.admin import SingletonModelAdmin

from .models import (
    ContactFormSubject,
    KlantContactMomentAnswer,
    KlantenInteractiesConfig,
    OpenKlant2Config2,
    OpenKlantConfig,
)


class ContactFormSubjectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject_code"].widget.attrs["placeholder"] = _(
            "Must be configured if E-suite is used"
        )

    class Meta:
        model = ContactFormSubject
        fields = (
            "subject",
            "subject_code",
        )


class ContactFormSubjectInlineAdmin(OrderedTabularInline):
    model = ContactFormSubject
    form = ContactFormSubjectForm
    fields = ("subject", "subject_code", "order", "move_up_down_links")
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


class OpenKlantConfigAdmin(admin.StackedInline):
    model = OpenKlantConfig
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
                    "register_channel",
                    "register_employee_id",
                    "use_rsin_for_innNnpId_query_parameter",
                    "send_email_confirmation",
                ],
            },
        ),
        (
            _("Filter Contactmomenten"),
            {
                "fields": [
                    "exclude_contactmoment_kanalen",
                ]
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


@admin.register(KlantContactMomentAnswer)
class KlantContactMomentAnswerAdmin(admin.ModelAdmin):
    search_fields = [
        "user__first_name",
        "user__last_name",
        "user__email",
        "contactmoment_url",
    ]
    list_filter = ["is_seen"]
    list_display = ["user", "contactmoment_url", "is_seen"]


#
# OpenKlant2
#


class OpenKlant2ConfigAdminForm(forms.ModelForm):
    class Meta:
        model = OpenKlantConfig
        fields = "__all__"


class OpenKlant2Config2Admin(admin.StackedInline):
    model = OpenKlant2Config2
    form = OpenKlant2ConfigAdminForm
    fieldsets = [
        (
            _("API configuration"),
            {
                "fields": [
                    "api_root",
                    "api_token",
                ]
            },
        ),
        (
            _("Vragen"),
            {
                "fields": [
                    "mijn_vragen_kanaal",
                    "mijn_vragen_organisatie_naam",
                    "mijn_vragen_actor",
                    "interne_taak_gevraagde_handeling",
                    "interne_taak_toelichting",
                ]
            },
        ),
    ]

    class Media:
        css = {"all": ("css/custom_admin.css",)}


@admin.register(KlantenInteractiesConfig)
class KlantenInteractiesConfigAdmin(OrderedInlineModelAdminMixin, SingletonModelAdmin):
    inlines = [
        OpenKlant2Config2Admin,
        OpenKlantConfigAdmin,
        ContactFormSubjectInlineAdmin,
    ]
