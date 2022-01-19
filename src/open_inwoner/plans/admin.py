from django.contrib import admin

from .models import Plan, PlanFile


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("title", "end_date", "created_by")


# @admin.register(Goal)
# class GoalAdmin(admin.ModelAdmin):
#     pass


@admin.register(PlanFile)
class PlanFileAdmin(admin.ModelAdmin):
    pass
