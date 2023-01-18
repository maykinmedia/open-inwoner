from django import forms
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _, ngettext

from solo.admin import SingletonModelAdmin

from open_inwoner.openzaak.zaaktypeconfig import get_configurable_zaaktype_choices

from .catalog import fetch_single_case_type_uuid
from .models import OpenZaakConfig, ZaakTypeConfig


@admin.register(OpenZaakConfig)
class OpenZaakConfigAdmin(SingletonModelAdmin):
    pass


class ZaakTypeConfigCreateForm(forms.ModelForm):
    uuid = forms.ChoiceField(label=_("Zaaktype"), choices=[])
    instance: ZaakTypeConfig

    class Meta:
        model = ZaakTypeConfig
        fields = [
            "uuid",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["uuid"].choices = get_configurable_zaaktype_choices()

    def save(self, commit=True):
        super().save(commit=False)
        if not self.instance.identificatie:
            case_type = fetch_single_case_type_uuid(self.instance.uuid)
            if case_type:
                self.instance.identificatie = case_type.identificatie
                self.instance.omschrijving = case_type.omschrijving
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance


@admin.register(ZaakTypeConfig)
class ZaakTypeConfigAdmin(admin.ModelAdmin):
    actions = [
        "mark_as_notify_status_changes",
        "mark_as_not_notify_status_changes",
    ]
    fields = [
        "uuid",
        "identificatie",
        "omschrijving",
        "notify_status_changes",
    ]
    readonly_fields = [
        "identificatie",
        "omschrijving",
    ]
    list_display = [
        "identificatie",
        "omschrijving",
        "notify_status_changes",
    ]
    list_filter = [
        "notify_status_changes",
    ]
    search_fields = [
        "uuid",
        "identificatie",
        "omschrijving",
    ]

    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            kwargs["form"] = ZaakTypeConfigCreateForm
        return super().get_form(request, obj, **kwargs)

    def get_fields(self, request, obj=None):
        if obj:
            return super().get_fields(request, obj=obj)
        else:
            return ["uuid"]

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj=obj)
        if obj:
            return fields + ["uuid"]
        return fields

    @admin.action(description="Set selected Zaaktypes to notify on status changes")
    def mark_as_notify_status_changes(self, request, qs):
        count = qs.update(notify_status_changes=True)
        self.message_user(
            request,
            ngettext(
                "%d zaaktype was successfully set to notify on status changes.",
                "%d zaaktypes were successfully set to notify on status changes.",
                count,
            )
            % count,
            level=messages.SUCCESS,
        )

    @admin.action(description="Set selected Zaaktypes to not notify on status changes")
    def mark_as_not_notify_status_changes(self, request, qs):
        count = qs.update(notify_status_changes=False)
        self.message_user(
            request,
            ngettext(
                "%d zaaktype was successfully set to not notify on status changes.",
                "%d zaaktypes were successfully set to not notify on status changes.",
                count,
            )
            % count,
            level=messages.SUCCESS,
        )
