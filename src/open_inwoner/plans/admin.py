from django.contrib import admin

from open_inwoner.accounts.admin import ActionInlineAdmin

from .models import Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    fields = (
        "uuid",
        "title",
        "goal",
        "end_date",
        "contacts",
        "created_by",
    )
    readonly_fields = ("uuid",)
    list_display = ("title", "end_date", "created_by")
    inlines = [ActionInlineAdmin]
