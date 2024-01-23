from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext as _

from import_export.admin import ImportExportMixin
from import_export.formats import base_formats
from ordered_model.admin import OrderedModelAdmin

from open_inwoner.ckeditor5.widgets import CKEditorWidget
from open_inwoner.utils.logentry import system_action
from open_inwoner.utils.mixins import UUIDAdminFirstInOrder

from ..models import (
    Category,
    Product,
    ProductCondition,
    ProductContact,
    ProductFile,
    ProductLink,
    ProductLocation,
)
from ..resources import ProductExportResource, ProductImportResource
from . import QuestionInline
from .mixins import GeoAdminMixin


class ProductFileInline(admin.TabularInline):
    model = ProductFile
    extra = 1


class ProductLinkInline(admin.TabularInline):
    model = ProductLink
    extra = 1
    ordering = ("pk",)


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
        widgets = {"content": CKEditorWidget}

    categories = forms.ModelMultipleChoiceField(
        label=_("Allowed admin categories"),
        queryset=Category.objects.all(),
        required=False,
        widget=FilteredSelectMultiple(verbose_name=_("Category"), is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

        # we only want to add/remove Categories we have access to and keep te rest
        user_categories = self.request.user.get_group_managed_categories()
        if user_categories:
            self.fields["categories"].queryset = user_categories
            if self.instance and self.instance.pk:
                self.fields[
                    "categories"
                ].initial = self.instance.categories.intersection(user_categories)

    def _save_m2m(self):
        # remember this before we run regular _save_m2m()
        current = set(self.instance.categories.all())

        super()._save_m2m()

        # we only want to add/remove Categories we have access to and keep the ones we don't,
        # so do some set operations to figure it out
        managed = set(self.request.user.get_group_managed_categories())
        if managed:
            want_managed = managed & set(self.cleaned_data["categories"])
            keep_not_ours = current - managed
            combined = keep_not_ours | want_managed
            self.instance.categories.set(combined)


@admin.register(Product)
class ProductAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("name", "created_on", "display_categories", "published")
    list_filter = ("published", "categories", "tags")
    list_editable = ("published",)
    date_hierarchy = "created_on"
    autocomplete_fields = (
        # "categories",
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
        QuestionInline,
    )

    # import-export
    resource_class = ProductImportResource
    import_template_name = "admin/product_import.html"
    formats = [base_formats.XLSX, base_formats.CSV]

    def get_form(self, request, obj=None, change=False, **kwargs):
        # workaround to get the request in the Modelform
        Form = super().get_form(request, obj=obj, change=change, **kwargs)

        class RequestForm(Form):
            def __new__(cls, *args, **kwargs):
                kwargs["request"] = request
                return Form(*args, **kwargs)

        return RequestForm

    def get_export_resource_class(self):
        return ProductExportResource

    def export_action(self, request, *args, **kwargs):
        response = super().export_action(request, *args, **kwargs)

        if request.method == "POST":
            user = request.user
            system_action(_("products were exported"), user=user)

        return response

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        categories = request.user.get_group_managed_categories()
        if categories:
            qs = qs.filter(categories__in=categories)
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
class ProductLocationAdmin(GeoAdminMixin, UUIDAdminFirstInOrder, admin.ModelAdmin):
    list_display = ("name", "city", "postcode", "street", "housenumber")
    list_filter = ("city",)
    search_fields = ("name", "city")
    readonly_fields = ("uuid",)


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
