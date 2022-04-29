from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.utils.translation import ugettext_lazy as _

from import_export.admin import ExportMixin
from import_export.formats import base_formats
from timeline_logger.admin import TimelineLogAdmin
from timeline_logger.models import TimelineLog
from timeline_logger.resources import TimelineLogResource


class CustomTimelineLogAdmin(ExportMixin, TimelineLogAdmin):
    list_display = ["get_object_title", "timestamp", "get_action_flag", "user"]
    list_filter = ["timestamp", "content_type"]
    list_select_related = ["content_type"]

    # export
    resource_class = TimelineLogResource
    formats = [
        base_formats.JSON,
        base_formats.CSV,
        base_formats.YAML,
        base_formats.TSV,
        base_formats.ODS,
        base_formats.HTML,
        base_formats.XLSX,
    ]

    def get_object_title(self, obj):
        return f"{obj.content_type.name} - {obj.object_id}"

    get_object_title.short_description = _("Logboekvermelding")

    def get_action_flag(self, obj):
        if obj.extra_data:
            if obj.extra_data.get("action_flag")[0] == ADDITION:
                return _("Aangemaakt")
            if obj.extra_data.get("action_flag")[0] == CHANGE:
                return _("Gewijzigd")
            if obj.extra_data.get("action_flag")[0] == DELETION:
                return _("Verwijderd")
            if obj.extra_data.get("action_flag")[0] == 4:
                return _("User action")
        return ""

    get_action_flag.short_description = _("Actie")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        """
        Show the audit log both to superusers and the users with 'change'
        permissions.
        """
        return (
            request.user.is_superuser or request.user.has_perm("admin.change_logentry")
        ) and request.method != "POST"

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(TimelineLog)
admin.site.register(TimelineLog, CustomTimelineLogAdmin)
