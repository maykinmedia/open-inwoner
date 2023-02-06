from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.forms.models import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _, ngettext

from solo.admin import SingletonModelAdmin

from .models import (
    CatalogusConfig,
    OpenZaakConfig,
    UserCaseInfoObjectNotification,
    UserCaseStatusNotification,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
)


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
    ordering = ("domein", "rsin")


class CatalogUsedListFilter(admin.SimpleListFilter):
    title = _("Catalogus")
    parameter_name = "catalogus"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        catalogs = CatalogusConfig.objects.filter(
            id__in=qs.values_list("catalogus_id", flat=True).distinct()
        )
        return [("none", "None")] + [(c.id, str(c)) for c in catalogs]

    def queryset(self, request, queryset):
        v = self.value()
        if v:
            if v == "none":
                v = None
            queryset = queryset.filter(catalogus=v)
        return queryset


class ZaakTypeInformatieObjectTypeConfigFormset(BaseInlineFormSet):
    def clean(self):
        instance_doc_upload = self.instance.document_upload_enabled

        for form in self.forms:
            inline_doc_upload = form.cleaned_data["document_upload_enabled"]
            if instance_doc_upload and inline_doc_upload:
                raise ValidationError(
                    _(
                        "Enabling both zaaktype and zaaktypeinformatieobject upload is not allowed. Only one of them should be enabled."
                    )
                )


class ZaakTypeInformatieObjectTypeConfigInline(admin.TabularInline):
    formset = ZaakTypeInformatieObjectTypeConfigFormset
    model = ZaakTypeInformatieObjectTypeConfig
    fields = [
        "omschrijving",
        "document_upload_enabled",
        "informatieobjecttype_url",
        "zaaktype_uuids",
    ]
    readonly_fields = [
        "omschrijving",
        "informatieobjecttype_url",
        "zaaktype_uuids",
    ]
    ordering = ("omschrijving",)

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ZaakTypeConfig)
class ZaakTypeConfigAdmin(admin.ModelAdmin):
    inlines = [
        ZaakTypeInformatieObjectTypeConfigInline,
    ]
    actions = [
        "mark_as_notify_status_changes",
        "mark_as_not_notify_status_changes",
    ]
    fields = [
        "catalogus",
        "identificatie",
        "omschrijving",
        "notify_status_changes",
        "document_upload_enabled",
        "external_document_upload_url",
    ]
    readonly_fields = [
        "catalogus",
        "identificatie",
        "omschrijving",
        "num_infotypes",
    ]
    list_display = [
        "identificatie",
        "omschrijving",
        "catalogus",
        "notify_status_changes",
        "document_upload_enabled",
        "num_infotypes",
    ]
    list_display_links = [
        "identificatie",
        "omschrijving",
    ]
    list_filter = [
        "notify_status_changes",
        CatalogUsedListFilter,
    ]
    search_fields = [
        "identificatie",
        "omschrijving",
        "catalogus__domein",
        "catalogus__rsin",
    ]
    ordering = ("identificatie", "catalogus__domein")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(num_infotypes=Count("zaaktypeinformatieobjecttypeconfig"))
        return qs

    def num_infotypes(self, obj=None):
        if not obj or not obj.pk:
            return "-"
        else:
            return getattr(obj, "num_infotypes", 0)

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


@admin.register(UserCaseStatusNotification)
class UserCaseStatusNotificationAdmin(admin.ModelAdmin):
    raw_id_fields = ["user"]
    search_fields = [
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__id",
        "case_uuid",
        "status_uuid",
    ]
    list_display = [
        "user",
        "case_uuid",
        "status_uuid",
        "created",
    ]

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserCaseInfoObjectNotification)
class UserCaseInfoObjectNotificationAdmin(admin.ModelAdmin):
    raw_id_fields = ["user"]
    search_fields = [
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__id",
        "case_uuid",
        "zaak_info_object_uuid",
    ]
    list_display = [
        "user",
        "case_uuid",
        "zaak_info_object_uuid",
        "created",
    ]

    def has_change_permission(self, request, obj=None):
        return False
