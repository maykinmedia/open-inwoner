from django.contrib import admin

from solo.admin import SingletonModelAdmin

from open_inwoner.ssd.models import SSDConfig


@admin.register(SSDConfig)
class SSDConfigAdmin(SingletonModelAdmin):
    fields = [
        "service",
        "gemeentecode",
        "bedrijfs_naam",
        "applicatie_naam",
    ]
