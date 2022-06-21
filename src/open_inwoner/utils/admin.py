from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.urls import NoReverseMatch, reverse
from django.utils.html import escape, format_html
from django.utils.translation import gettext as _

from import_export.admin import ExportMixin
from import_export.formats import base_formats
from timeline_logger.admin import TimelineLogAdmin
from timeline_logger.models import TimelineLog
from timeline_logger.resources import TimelineLogResource


class CustomTimelineLogAdmin(ExportMixin, TimelineLogAdmin):
    show_full_result_count = False
    fields = ["content_type", "timestamp", "extra_data", "user"]
    list_display = [
        "timestamp",
        "user",
        "content_type",
        "object_link",
        "object_id",
        "get_action_flag",
        "message",
    ]
    list_filter = ["timestamp", "content_type"]
    list_select_related = ["content_type"]
    search_fields = [
        "user__email",
        "extra_data",
    ]
    date_hierarchy = "timestamp"

    # export
    resource_class = TimelineLogResource
    formats = [
        base_formats.CSV,
        base_formats.XLSX,
    ]

    def get_object_title(self, obj):
        if obj.content_type:
            return f"{obj.content_type.name} - {obj.object_id}"
        return _("System - anonymous user")

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
            if obj.extra_data.get("action_flag")[0] == 5:
                return _("System action")
        return ""

    def message(self, obj):
        return obj.extra_data.get("message") if obj.extra_data else ""

    def object_link(self, obj):
        if not obj.extra_data:
            return ""

        if obj.extra_data.get("action_flag") == DELETION:
            link = escape(obj.extra_data.get("content_object_repr")) or ""
        else:
            ct = obj.content_type
            try:
                url = reverse(
                    ("admin:{app_label}_{model}_change").format(
                        app_label=ct.app_label, model=ct.model
                    ),
                    args=[obj.object_id],
                )
                link = format_html(
                    '<a href="{}">{}</a>',
                    url,
                    escape(obj.extra_data.get("content_object_repr")),
                )
            except NoReverseMatch:
                link = escape(obj.extra_data.get("content_object_repr"))
            except Exception:
                link = ""

        return link

    get_action_flag.short_description = _("Actie")
    message.short_description = _("Bericht")
    object_link.short_description = _("Object")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(TimelineLog)
admin.site.register(TimelineLog, CustomTimelineLogAdmin)
