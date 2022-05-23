from django import forms
from django.contrib import admin
from django.utils.translation import gettext as _

from import_export.admin import ImportExportMixin
from import_export.formats import base_formats
from ordered_model.admin import OrderedModelAdmin

from open_inwoner.ckeditor5.widgets import CKEditorWidget
from open_inwoner.utils.logentry import system_action

from ..models import (
    Product,
    ProductCondition,
    ProductContact,
    ProductFile,
    ProductLink,
    ProductLocation,
)
from ..resources import ProductExportResource, ProductImportResource
from .mixins import GeoAdminMixin


class ProductFileInline(admin.TabularInline):
    model = ProductFile
    extra = 1


class ProductLinkInline(admin.TabularInline):
    model = ProductLink
    extra = 1


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
        widgets = {"content": CKEditorWidget}


@admin.register(Product)
class ProductAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("name", "created_on", "display_categories")
    list_filter = ("categories", "tags")
    date_hierarchy = "created_on"
    autocomplete_fields = (
        "categories",
        "related_products",
        "tags",
        "organizations",
        "contacts",
        "locations",
        "conditions",
    )
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    save_on_top = True
    form = ProductAdminForm
    inlines = (
        ProductFileInline,
        ProductLinkInline,
    )

    # import-export
    resource_class = ProductImportResource
    import_template_name = "admin/product_import.html"
    formats = [base_formats.XLSX, base_formats.CSV]

    def get_export_resource_class(self):
        return ProductExportResource

    def export_action(self, request, *args, **kwargs):
        response = super().export_action(request, *args, **kwargs)

        if request.method == "POST":
            user = request.user
            system_action(_("products were exported"), user)

        return response

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("links", "locations", "contacts")

    def display_categories(self, obj):
        return ", ".join(p.name for p in obj.categories.all())

    display_categories.short_description = "categories"


@admin.register(ProductContact)
class ProductContactAdmin(admin.ModelAdmin):
    list_display = ("organization", "last_name", "first_name")
    list_filter = ("organization",)
    search_fields = ("first_name", "last_name")


@admin.register(ProductFile)
class ProductFileAdmin(admin.ModelAdmin):
    list_display = ("product", "file")
    list_filter = ("product",)


@admin.register(ProductLink)
class ProductLinkAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "url")


@admin.register(ProductLocation)
class ProductLocationAdmin(GeoAdminMixin, admin.ModelAdmin):
    list_display = ("name", "city", "postcode", "street", "housenumber")
    list_filter = ("city",)
    search_fields = ("name", "city")


@admin.register(ProductCondition)
class ProductConditionAdmin(OrderedModelAdmin):
    list_display = (
        "name",
        "question",
        "display_products",
        "order",
        "move_up_down_links",
    )
    list_filter = ("products__name",)
    search_fields = ("name",)

    def display_products(self, obj):
        return ", ".join(p.name for p in obj.products.all())

    display_products.short_description = "products"
