from django.contrib import admin

from .cms_appconfig import ProfileConfig


@admin.register(ProfileConfig)
class ProfileConfigAdmin(admin.ModelAdmin):
    fields = (
        "namespace",
        "my_data",
        "selected_categories",
        "mentors",
        "my_contacts",
        "selfdiagnose",
        "actions",
        "notifications",
        "questions",
        "ssd",
        "newsletters",
        "appointments",
    )
