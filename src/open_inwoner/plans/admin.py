from django.contrib import admin

from .models import Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("title", "end_date", "created_by")
