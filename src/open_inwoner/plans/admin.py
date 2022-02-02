from django.contrib import admin

from open_inwoner.accounts.admin import ActionInlineAdmin

from .models import Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("title", "end_date", "created_by")
    inlines = [ActionInlineAdmin]
