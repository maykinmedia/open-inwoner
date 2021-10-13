from django.contrib import admin

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category, fields="__all__")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "created_on", "display_categories")
    list_filter = ("categories",)
    date_hierarchy = "created_on"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("categories")

    def display_categories(self, obj):
        return ", ".join(p.name for p in obj.categories.all())

    display_categories.short_description = "categories"
