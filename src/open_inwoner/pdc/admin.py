from django import forms
from django.contrib import admin

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import Category, Product, Tag, TagType
from .widgets import CKEditorWidget


@admin.register(Category)
class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category, fields="__all__")
    prepopulated_fields = {"slug": ("name",)}


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
        widgets = {"content": CKEditorWidget}


@admin.register(TagType)
class TagTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    list_filter = ("type__name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "created_on", "display_categories")
    list_filter = ("categories", "tags")
    date_hierarchy = "created_on"
    form = ProductAdminForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("categories", "tags")

    def display_categories(self, obj):
        return ", ".join(p.name for p in obj.categories.all())

    display_categories.short_description = "categories"
