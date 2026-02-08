from django.contrib import admin

from open_inwoner.accounts.admin import ActionInlineAdmin
from open_inwoner.utils.mixins import UUIDAdminFirstInOrder

from .models import ActionTemplate, Plan, PlanContact, PlanTemplate


class ActionTemplateInlineAdmin(admin.TabularInline):
    model = ActionTemplate
    extra = 1


class PlanContactInlineAdmin(admin.TabularInline):
    model = PlanContact
    extra = 1


@admin.register(PlanTemplate)
class PlanTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "goal",
    )
    inlines = [ActionTemplateInlineAdmin]
    filter_horizontal = ("related_categories",)


@admin.register(Plan)
class PlanAdmin(UUIDAdminFirstInOrder, admin.ModelAdmin):
    readonly_fields = ("uuid",)
    list_display = (
        "title",
        "end_date",
        "created_by",
    )
    inlines = [PlanContactInlineAdmin, ActionInlineAdmin]
    # Note: filter_horizontal cannot be used with plan_contacts because it uses a through model
    # The PlanContactInlineAdmin handles editing contacts instead
