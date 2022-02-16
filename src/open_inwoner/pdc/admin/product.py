from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from import_export.admin import ImportExportMixin
from import_export.formats import base_formats

from open_inwoner.ckeditor5.widgets import CKEditorWidget

from ..models import Product, ProductContact, ProductFile, ProductLink, ProductLocation
from ..resources import ProductExportResource, ProductImportResource
from .mixins import GeoAdminMixin


class ProductContactInline(admin.StackedInline):
    model = ProductContact
    extra = 1


class ProductFileInline(admin.TabularInline):
    model = ProductFile
    extra = 1


class ProductLinkInline(admin.TabularInline):
    model = ProductLink
    extra = 1


class ProductLocationInline(admin.StackedInline):
    model = ProductLocation
    exclude = ("geometry",)
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
    autocomplete_fields = ("categories", "related_products", "tags", "organizations")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    save_on_top = True
    form = ProductAdminForm
    inlines = (
        ProductFileInline,
        ProductLinkInline,
        ProductLocationInline,
        ProductContactInline,
    )

    # import-export
    resource_class = ProductImportResource
    import_template_name = "admin/product_import.html"
    formats = [base_formats.XLSX, base_formats.CSV]

    def get_export_resource_class(self):
        return ProductExportResource

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("links", "locations", "product_contacts")

    def display_categories(self, obj):
        return ", ".join(p.name for p in obj.categories.all())

    display_categories.short_description = "categories"


@admin.register(ProductContact)
class ProductContactAdmin(admin.ModelAdmin):
    list_display = ("product", "organization", "last_name", "first_name")
    list_filter = ("product__name",)


@admin.register(ProductFile)
class ProductFileAdmin(admin.ModelAdmin):
    list_display = ("product", "file")
    list_filter = ("product",)


@admin.register(ProductLink)
class ProductLinkAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "url")


@admin.register(ProductLocation)
class ProductLocationAdmin(GeoAdminMixin, admin.ModelAdmin):
    # List
    list_display = ("product", "name", "city", "postcode", "street", "housenumber")
    list_filter = ("city",)

    # Detail
    fieldsets = (
        (None, {"fields": ("product", "name")}),
        (
            _("Address"),
            {"fields": ("street", "housenumber", "postcode", "city", "geometry")},
        ),
    )
