from django.contrib import admin

from .cms_appconfig import MijnAfvalApphookConfig


@admin.register(MijnAfvalApphookConfig)
class MijnAfvalConfigAdmin(admin.ModelAdmin):
    fields = ("namespace", "page_heading", "page_description")

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial["namespace"] = "mijn_afval"
        return initial
