from django import forms
from django.contrib import admin, messages
from django.core.exceptions import BadRequest
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse_lazy
from django.utils.translation import gettext_lazy as _, ngettext

from solo.admin import SingletonModelAdmin

from .catalog import fetch_catalog_case_type_by_identification
from .config import get_configurable_zaaktype_choices, get_configurable_zaaktypes
from .models import CatalogusConfig, OpenZaakConfig, ZaakTypeConfig


@admin.register(OpenZaakConfig)
class OpenZaakConfigAdmin(SingletonModelAdmin):
    pass


@admin.register(CatalogusConfig)
class CatalogusConfigAdmin(admin.ModelAdmin):
    list_display = [
        "domein",
        "rsin",
        "url",
    ]
    fields = [
        "url",
        "domein",
        "rsin",
    ]
    readonly_fields = fields
    search_fields = [
        "domein",
        "rsin",
        "url",
    ]


class ZaakTypeConfigCreateForm(forms.ModelForm):
    catalogus = forms.ModelChoiceField(
        queryset=CatalogusConfig.objects.all(),
        label=_("Cataglous"),
        widget=forms.Select(
            attrs={
                "hx-trigger": "change",
                # TODO build target-id using form.auto_id
                "hx-target": "#id_identificatie",
                "hx-swap": "#innerHTML swap:50ms settle:50ms",
                "hx-get": reverse_lazy(
                    "admin:openzaak_zaaktypeconfig-widget-identificatie"
                ),
                # we'd like hx-sync but it errors
                # "hx-sync": "replace",
            }
        ),
    )
    # use a CharField with a Select widget, so it doesn't force choices validation
    identificatie = forms.CharField(label=_("Identificatie"), widget=forms.Select())

    instance: ZaakTypeConfig

    class Meta:
        model = ZaakTypeConfig
        fields = ["catalogus", "identificatie"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            if self.instance.catalogus_id and not self.instance.identificatie:
                choices = get_configurable_zaaktype_choices(self.instance.catalogus)
                self.fields["identificatie"] = forms.ChoiceField(
                    label=_("Identificatie"),
                    choices=choices,
                )
                # self.fields[
                #     "identificatie"
                # ].widget.choices = get_configurable_zaaktype_choices(
                #     self.instance.catalogus
                # )

    def clean(self):
        cleaned_data = super().clean()
        catalogus = cleaned_data.get("catalogus")
        identificatie = cleaned_data.get("identificatie")
        if (
            catalogus
            and identificatie
            and not self.check_catalogus_has_id(catalogus, identificatie)
        ):
            self.add_error(
                "identificatie",
                _("This is not a valid identification from this catalogus."),
            )

    @staticmethod
    def check_catalogus_has_id(catalogus: CatalogusConfig, identificatie: str) -> bool:
        # re-use the cached list
        case_types = get_configurable_zaaktypes(catalogus)
        for case_type in case_types:
            if case_type.identificatie == identificatie:
                return True
        return False

    def save(self, commit=True):
        super().save(commit=False)
        if not self.instance.omschrijving:
            case_types = fetch_catalog_case_type_by_identification(
                self.instance.catalogus.url, self.instance.identificatie
            )
            if case_types:
                # use the first one to grab info
                case_type = case_types[0]
                # add info for searching/usability/debug here
                self.instance.omschrijving = case_type.omschrijving
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance


class CatalogUsedListFilter(admin.SimpleListFilter):
    title = _("Catalogus")
    parameter_name = "catalogus"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        catalogs = CatalogusConfig.objects.filter(
            id__in=qs.values_list("catalogus_id", flat=True).distinct()
        )
        return [(c.id, str(c)) for c in catalogs]

    def queryset(self, request, queryset):
        v = self.value()
        if v:
            queryset = queryset.filter(catalogus=v)
        return queryset


@admin.register(ZaakTypeConfig)
class ZaakTypeConfigAdmin(admin.ModelAdmin):
    actions = [
        "mark_as_notify_status_changes",
        "mark_as_not_notify_status_changes",
    ]
    fields = [
        "catalogus",
        "identificatie",
        "omschrijving",
        "notify_status_changes",
    ]
    readonly_fields = [
        "omschrijving",
    ]
    list_display = [
        "identificatie",
        "omschrijving",
        "catalogus",
        "notify_status_changes",
    ]
    list_filter = [
        "notify_status_changes",
        CatalogUsedListFilter,
    ]
    search_fields = [
        "identificatie",
        "omschrijving",
        "catalogus__domein",
        "catalogus__rsin__exact",
    ]

    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            kwargs["form"] = ZaakTypeConfigCreateForm
        return super().get_form(request, obj, **kwargs)

    def get_fields(self, request, obj=None):
        if obj:
            return super().get_fields(request, obj=obj)
        else:
            return ["catalogus", "identificatie"]

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj=obj)
        if obj:
            return fields + ["catalogus", "identificatie"]
        return fields

    def get_urls(self):
        urls = super().get_urls()
        urls = [
            path(
                "widget/identificatie/",
                self.admin_site.admin_view(self.view_identificaties, cacheable=True),
                name="openzaak_zaaktypeconfig-widget-identificatie",
            ),
        ] + urls
        return urls

    def view_identificaties(self, request):
        if not request.htmx:
            raise BadRequest("requires htmx")
        catalogus = request.GET.get("catalogus", None)
        config = get_object_or_404(CatalogusConfig, id=catalogus)
        zaak_type_choices = get_configurable_zaaktype_choices(config)
        context = {
            "choices": zaak_type_choices,
        }
        return TemplateResponse(request, "admin/openzaak/widget/options.html", context)

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
