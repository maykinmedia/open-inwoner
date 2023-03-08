from django.contrib import admin

from .models import ExternalAPILog


@admin.register(ExternalAPILog)
class ExternalAPILogAdmin(admin.ModelAdmin):
    fields = (
        "hostname",
        "path",
        "params",
        "query_params",
        "status_code",
        "method",
        "response_ms",
        "timestamp",
        "user",
    )
    readonly_fields = fields
    list_display = fields
    list_filter = ("method", "status_code", "hostname")
    search_fields = ("path",)
    date_hierarchy = "timestamp"
