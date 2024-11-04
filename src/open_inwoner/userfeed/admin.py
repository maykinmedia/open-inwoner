from django.conf import settings
from django.contrib import admin

from .models import FeedItemData


@admin.register(FeedItemData)
class FeedItemDataAdmin(admin.ModelAdmin):
    raw_id_fields = [
        "user",
    ]
    list_display = [
        "user",
        "type",
        "display_at",
        "completed_at",
    ]
    list_filter = [
        "type",
    ]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
    ]
    ordering = [
        "display_at",
    ]

    def has_change_permission(self, request, obj=None):
        if settings.DEBUG:
            return super().has_change_permission(request, obj=obj)
        return False

    def has_add_permission(self, request):
        if settings.DEBUG:
            return super().has_add_permission(request)
