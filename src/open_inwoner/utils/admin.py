from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.utils.translation import ugettext_lazy as _

from timeline_logger.admin import TimelineLogAdmin
from timeline_logger.models import TimelineLog


class CustomTimelineLogAdmin(TimelineLogAdmin):
    list_display = ["__str__", "timestamp", "get_action_flag", "user"]
    list_filter = ["timestamp", "content_type"]
    list_select_related = ["content_type"]

    def get_action_flag(self, obj):
        if obj.extra_data:
            if obj.extra_data.get("action_flag") == ADDITION:
                return _("Aangemaakt")
            if obj.extra_data.get("action_flag") == CHANGE:
                return _("Gewijzigd")
            if obj.extra_data.get("action_flag") == DELETION:
                return _("Verwijderd")
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
