from django import forms
from django.contrib import admin
from django.contrib.gis.db.models import PointField
from django.contrib.gis.forms.widgets import BaseGeometryWidget
from django.utils.translation import ugettext_lazy as _

from import_export.admin import ImportExportMixin
from import_export.formats import base_formats
from leaflet.admin import LeafletGeoAdmin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from open_inwoner.ckeditor5.widgets import CKEditorWidget

from .models import (
    Category,
    Neighbourhood,
    Organization,
    OrganizationType,
    Product,
    ProductContact,
    ProductFile,
    ProductLink,
    ProductLocation,
    Tag,
    TagType,
)
from .resources import (
    CategoryExportResource,
    CategoryImportResource,
    ProductExportResource,
    ProductImportResource,
)


class MapWidget(BaseGeometryWidget):
    template_name = "admin/widgets/map.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value and isinstance(value, str):
            value = self.deserialize(value)

        if value:
            context.update({"lat": value.y, "lng": value.x})

        return context


@admin.register(Category)
class CategoryAdmin(ImportExportMixin, TreeAdmin):
    change_list_template = "admin/category_change_list.html"
    form = movenodeform_factory(Category, fields="__all__")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("path",)

    # import-export
    import_template_name = "admin/category_import.html"
    resource_class = CategoryImportResource
    formats = [base_formats.XLSX, base_formats.CSV]

    def get_export_resource_class(self):
        return CategoryExportResource


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


class ProductContactInline(admin.StackedInline):
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


@admin.register(TagType)
class TagTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    list_filter = ("type__name",)
    search_fields = ("name",)
    ordering = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductFile)
class ProductFileAdmin(admin.ModelAdmin):
    list_display = ("product", "file")
    list_filter = ("product",)


@admin.register(ProductLocation)
class ProductLocationAdmin(admin.ModelAdmin):
    # List
    list_display = ("product", "city", "postcode", "street", "housenumber")
    list_filter = ("city",)

    # Detail
    # modifiable = False
    fieldsets = (
        (None, {"fields": ("product",)}),
        (
            _("Address"),
            {"fields": ("street", "housenumber", "postcode", "city", "geometry")},
        ),
    )
    formfield_overrides = {
        PointField: {"widget": MapWidget},
    }

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
    prepopulated_fields = {"slug": ("name",)}

    # Detail
    modifiable = False
    fieldsets = (
        (None, {"fields": ("name", "slug", "type", "logo", "neighbourhood")}),
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
