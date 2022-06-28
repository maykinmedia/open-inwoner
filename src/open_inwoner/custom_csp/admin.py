from django.contrib import admin

from .models import CSPSetting


@admin.register(CSPSetting)
class CSPSettingAdmin(admin.ModelAdmin):
    fields = [
        "directive",
        "value",
    ]
    list_display = [
        "directive",
        "value",
    ]
    list_filter = [
        "directive",
    ]
    search_fields = [
        "directive",
        "value",
    ]
