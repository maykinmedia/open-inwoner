from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import SSDConfig


@admin.register(SSDConfig)
class SSDConfigAdmin(SingletonModelAdmin):
    fields = [
        "service",
        "bedrijfs_naam",
        "applicatie_naam",
        "gemeentecode",
    ]

    class Meta:
        verbose_name = _("SSD configuration")
