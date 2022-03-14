from django.contrib import admin

from open_inwoner.accounts.admin import ActionInlineAdmin
from open_inwoner.utils.mixins import UUIDAdminFirstInOrder

from .models import ActionTemplate, Plan, PlanTemplate


class ActionTempalteInlineAdmin(admin.TabularInline):
    model = ActionTemplate
    extra = 1


@admin.register(PlanTemplate)
class PlanTempalteAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "goal",
    )
    inlines = [ActionTempalteInlineAdmin]


@admin.register(Plan)
class PlanAdmin(UUIDAdminFirstInOrder, admin.ModelAdmin):
    readonly_fields = ("uuid",)
    list_display = (
        "title",
        "end_date",
        "created_by",
    )
    inlines = [ActionInlineAdmin]
