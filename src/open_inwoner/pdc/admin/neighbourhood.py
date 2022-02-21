from django.contrib import admin

from ..models import Neighbourhood


@admin.register(Neighbourhood)
class NeighbourhoodAmin(admin.ModelAdmin):
    list_display = ("name",)
