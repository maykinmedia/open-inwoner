from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import OpenKlantConfig


@admin.register(OpenKlantConfig)
class OpenKlantConfigAdmin(SingletonModelAdmin):
    fields = [
        "klanten_service",
        "contactmomenten_service",
    ]
