from django.contrib import admin

from ..models import Tag, TagType


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    list_filter = ("type__name",)
    search_fields = ("name",)
    ordering = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(TagType)
class TagTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
