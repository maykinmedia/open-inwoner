from django.contrib import admin

from aldryn_apphooks_config.admin import BaseAppHookConfig

from .cms_appconfig import MijnAfvalApphookConfig


@admin.register(MijnAfvalApphookConfig)
class MijnAfvalConfigAdmin(BaseAppHookConfig, admin.ModelAdmin):
    def get_config_fields(self):
        return (
            "page_heading",
            "page_description",
        )

    def get_changeform_initial_data(self, request):
        """
        Pre-populate the CMS instance namespace field with the correct value.
        """
        initial = super().get_changeform_initial_data(request)
        initial["namespace"] = "mijn_afval"
        return initial
