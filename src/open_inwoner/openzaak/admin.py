from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import BooleanField, Count, ExpressionWrapper, Q
from django.forms.models import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _, ngettext

from import_export.admin import ImportExportMixin
from import_export.formats import base_formats
from solo.admin import SingletonModelAdmin

from .models import (
    CatalogusConfig,
    OpenZaakConfig,
    StatusTranslation,
    UserCaseInfoObjectNotification,
    UserCaseStatusNotification,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
)
from .resources.import_resource import StatusTranslationImportResource


@admin.register(OpenZaakConfig)
class OpenZaakConfigAdmin(SingletonModelAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "zaak_service",
                    "catalogi_service",
                    "document_service",
                    "form_service",
                ]
            },
        ),
        (
            "Advanced options",
            {
                "classes": ("collapse",),
                "fields": [
                    "zaak_max_confidentiality",
                    "document_max_confidentiality",
                    "max_upload_size",
                    "allowed_file_extensions",
                ],
            },
        ),
        (
            _("API behaviour override options"),
            {
                "fields": [
                    "skip_notification_statustype_informeren",
                    "reformat_esuite_zaak_identificatie",
                ],
            },
        ),
    )


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


class HasDocNotifyListFilter(admin.SimpleListFilter):
    title = _("notify document attachment")
    parameter_name = "doc_notify"

    def lookups(self, request, model_admin):
        return [
            ("yes", _("Yes")),
            ("no", _("No")),
        ]

    def queryset(self, request, queryset):
        v = self.value()
        if v == "yes":
            queryset = queryset.filter(has_doc_notify=True)
        elif v == "no":
            queryset = queryset.filter(has_doc_notify=False)
        return queryset


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
        "document_notification_enabled",
        "informatieobjecttype_uuid",
        "zaaktype_uuids",
    ]
    readonly_fields = [
        "omschrijving",
        "informatieobjecttype_url",
        "informatieobjecttype_uuid",
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
        "contact_form_enabled",
        "notify_status_changes",
        "document_upload_enabled",
        "external_document_upload_url",
        "description",
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
        "has_doc_notify",
        "document_upload_enabled",
        "num_infotypes",
    ]
    list_display_links = [
        "identificatie",
        "omschrijving",
    ]
    list_filter = [
        "notify_status_changes",
        HasDocNotifyListFilter,
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
        qs = qs.annotate(
            num_doc_notify=Count(
                "zaaktypeinformatieobjecttypeconfig",
                filter=Q(
                    zaaktypeinformatieobjecttypeconfig__document_notification_enabled=True
                ),
            )
        )
        qs = qs.annotate(
            has_doc_notify=ExpressionWrapper(
                Q(num_doc_notify__gt=0), output_field=BooleanField()
            )
        )
        return qs

    def num_infotypes(self, obj=None):
        if not obj or not obj.pk:
            return "-"
        else:
            return getattr(obj, "num_infotypes", 0)

    num_infotypes.admin_order_field = "num_infotypes"

    def has_doc_notify(self, obj=None):
        if not obj or not obj.pk:
            return False
        else:
            return getattr(obj, "has_doc_notify", False)

    has_doc_notify.boolean = True
    has_doc_notify.admin_order_field = "has_doc_notify"

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
        "created_on",
        "is_sent",
    ]
    list_filter = [
        "is_sent",
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
        "created_on",
        "is_sent",
    ]
    list_filter = [
        "is_sent",
    ]

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StatusTranslation)
class StatusTranslationAdmin(ImportExportMixin, admin.ModelAdmin):
    fields = [
        "status",
        "translation",
    ]
    search_fields = [
        "status",
        "translation",
    ]
    list_display = [
        "id",
        "status",
        "translation",
    ]
    list_editable = [
        "status",
        "translation",
    ]
    ordering = ("status",)

    # import-export
    resource_class = StatusTranslationImportResource
    formats = [base_formats.XLSX, base_formats.CSV]
