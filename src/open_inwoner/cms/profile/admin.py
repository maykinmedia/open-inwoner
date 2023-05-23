from django.contrib import admin

from aldryn_apphooks_config.admin import BaseAppHookConfig

from .cms_appconfig import ProfileConfig


@admin.register(ProfileConfig)
class ProfileConfigAdmin(BaseAppHookConfig, admin.ModelAdmin):
    def get_config_fields(self):
        return (
            "my_data",
            "selected_categories",
            "mentors",
            "my_contacts",
            "selfdiagnose",
            "actions",
            "notifications",
            "questions",
        )
