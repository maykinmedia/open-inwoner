from django import forms
from django.contrib import admin

from leaflet.admin import LeafletGeoAdmin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import Category, Product, ProductLink, ProductLocation, Tag, TagType
from .widgets import CKEditorWidget


@admin.register(Category)
class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category, fields="__all__")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("name",)


class ProductLinkInline(admin.TabularInline):
    model = ProductLink
    extra = 1


class ProductLocationInline(admin.TabularInline):
    model = ProductLocation
    exclude = ("geometry",)
    extra = 1


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
        widgets = {"content": CKEditorWidget}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "created_on", "display_categories")
    list_filter = ("categories", "tags")
    date_hierarchy = "created_on"
    autocomplete_fields = ("categories", "related_products", "tags")
    search_fields = ("name",)
    ordering = ("name",)
    form = ProductAdminForm
    inlines = (ProductLinkInline, ProductLocationInline)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("categories", "tags")

    def display_categories(self, obj):
        return ", ".join(p.name for p in obj.categories.all())

    display_categories.short_description = "categories"


@admin.register(TagType)
class TagTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    list_filter = ("type__name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(ProductLocation)
class ProductLocationAdmin(LeafletGeoAdmin):
    list_display = ("product", "city", "postcode", "street", "housenumber")
    list_filter = ("city",)
    modifiable = False

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)

        # don't show map when creating new location
        if not obj:
            return readonly_fields + ("geometry",)

        return readonly_fields


@admin.register(ProductLink)
class ProductLinkAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "url")
