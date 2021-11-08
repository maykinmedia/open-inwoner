from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from import_export.admin import ImportExportMixin
from leaflet.admin import LeafletGeoAdmin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import (
    Category,
    Neighbourhood,
    Organization,
    OrganizationType,
    Product,
    ProductContact,
    ProductLink,
    ProductLocation,
    Tag,
    TagType,
)
from .resources import CategoryResource, ProductResource
from .widgets import CKEditorWidget


@admin.register(Category)
class CategoryAdmin(ImportExportMixin, TreeAdmin):
    change_list_template = "admin/category_admintools.html"
    form = movenodeform_factory(Category, fields="__all__")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("path",)

    # import-export resource
    resource_class = CategoryResource


class ProductLinkInline(admin.TabularInline):
    model = ProductLink
    extra = 1


class ProductLocationInline(admin.TabularInline):
    model = ProductLocation
    exclude = ("geometry",)
    extra = 1


class ProductContactInline(admin.TabularInline):
    model = ProductContact
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
    form = ProductAdminForm
    inlines = (ProductLinkInline, ProductLocationInline, ProductContactInline)

    # import-export resource
    resource_class = ProductResource

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("links", "locations", "product_contacts")

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
    # List
    list_display = ("product", "city", "postcode", "street", "housenumber")
    list_filter = ("city",)

    # Detail
    modifiable = False
    fieldsets = (
        (None, {"fields": ("product",)}),
        (
            _("Address"),
            {"fields": ("street", "housenumber", "postcode", "city", "geometry")},
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        # don't show map when creating new location
        if not obj:
            return readonly_fields + ("geometry",)

        return readonly_fields


@admin.register(ProductLink)
class ProductLinkAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "url")


@admin.register(Neighbourhood)
class NeighbourhoodAmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Organization)
class OrganizationAdmin(LeafletGeoAdmin):
    # List
    list_display = ("name", "type")
    list_filter = ("type__name", "city")
    search_fields = ("name",)
    ordering = ("name",)

    # Detail
    modifiable = False
    fieldsets = (
        (None, {"fields": ("name", "type", "logo", "neighbourhood")}),
        (_("Contact"), {"fields": ("email", "phonenumber")}),
        (
            _("Address"),
            {"fields": ("street", "housenumber", "postcode", "city", "geometry")},
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        # don't show map when creating new location
        if not obj:
            return readonly_fields + ("geometry",)

        return readonly_fields


@admin.register(ProductContact)
class ProductContactAdmin(admin.ModelAdmin):
    list_display = ("product", "organization", "last_name", "first_name")
    list_filter = ("product__name",)
