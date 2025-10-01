from django.contrib import admin

from open_inwoner.pdc.models import Neighbourhood


@admin.register(Neighbourhood)
class NeighbourhoodAmin(admin.ModelAdmin):
    list_display = ("name",)
