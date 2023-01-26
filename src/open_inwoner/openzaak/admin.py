from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _, ngettext

from solo.admin import SingletonModelAdmin

from .models import (
    CatalogusConfig,
    OpenZaakConfig,
    UserCaseStatusNotification,
    ZaakTypeConfig,
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
        "catalogus",
        "identificatie",
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
        "catalogus__rsin",
    ]
    ordering = ("identificatie", "catalogus__domein")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

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
