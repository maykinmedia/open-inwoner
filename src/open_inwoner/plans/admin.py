from django.contrib import admin

from open_inwoner.accounts.admin import ActionInlineAdmin
from open_inwoner.utils.mixins import UUIDAdminFirstInOrder

from .models import Plan


@admin.register(Plan)
class PlanAdmin(UUIDAdminFirstInOrder, admin.ModelAdmin):
    readonly_fields = ("uuid",)
    list_display = ("title", "end_date", "created_by")
    inlines = [ActionInlineAdmin]
