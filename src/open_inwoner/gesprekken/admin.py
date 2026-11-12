from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .models import (
    GesprekGezien,
    GesprekkenEventStroom,
    MijnGesprekkenConfig,
    VerwerktGesprekEvent,
)


@admin.register(MijnGesprekkenConfig)
class MijnGesprekkenConfigAdmin(SingletonModelAdmin):
    pass


@admin.register(GesprekkenEventStroom)
class GesprekkenEventStroomAdmin(SingletonModelAdmin):
    readonly_fields = ("bijgewerkt_op",)


@admin.register(VerwerktGesprekEvent)
class VerwerktGesprekEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "verwerkt_op")
    search_fields = ("event_id",)


@admin.register(GesprekGezien)
class GesprekGezienAdmin(admin.ModelAdmin):
    list_display = ("user", "gesprek_url", "gezien_op")
    raw_id_fields = ("user",)
