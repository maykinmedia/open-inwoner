from import_export import fields, resources
from import_export.widgets import CharWidget, ManyToManyWidget

from ..models import Category, Organization, Product, Tag


class CategoryExportResource(resources.ModelResource):
    class Meta:
        model = Category
        import_id_fields = ("slug",)
        fields = (
            "name",
            "slug",
            "description",
            "path",
        )
        export_order = (
            "name",
            "slug",
            "description",
            "path",
        )


class ProductExportResource(resources.ModelResource):
    categories = fields.Field(
        column_name="categories",
        attribute="categories",
        widget=ManyToManyWidget(Category, field="slug"),
    )
    organizations = fields.Field(
        column_name="organizations",
        attribute="organizations",
        widget=ManyToManyWidget(Organization, field="slug"),
    )
    related_products = fields.Field(
        column_name="related_products",
        attribute="related_products",
        widget=ManyToManyWidget(Product, field="slug"),
    )
    tags = fields.Field(
        column_name="tags",
        attribute="tags",
        widget=ManyToManyWidget(Tag, field="slug"),
    )
    costs = fields.Field(
        column_name="costs",
        attribute="costs",
        widget=CharWidget(),
    )

    class Meta:
        model = Product
        fields = (
            "name",
            "slug",
            "summary",
            "link",
            "content",
            "categories",
            "related_products",
            "tags",
            "costs",
            "created_on",
            "updated_on",
            "organizations",
        )
        export_order = (
            "name",
            "slug",
            "summary",
            "link",
            "content",
            "categories",
            "related_products",
            "tags",
            "organizations",
            "costs",
            "created_on",
            "updated_on",
        )
