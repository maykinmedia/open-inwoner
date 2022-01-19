from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import OpenZaakConfig


@admin.register(OpenZaakConfig)
class OpenZaakConfigAdmin(SingletonModelAdmin):
    pass
