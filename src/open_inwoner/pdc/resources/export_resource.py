from import_export import fields, resources
from import_export.widgets import ManyToManyWidget

from ..models import Category, Organization, Product, Tag


class CategoryExportResource(resources.ModelResource):
    name = fields.Field(column_name="Name of category", attribute="name")
    slug = fields.Field(column_name="Slug", attribute="slug")
    description = fields.Field(column_name="Description", attribute="description")
    created_on = fields.Field(
        column_name="Date of category creation", attribute="created_on"
    )
    updated_on = fields.Field(
        column_name="Date of category update", attribute="updated_on"
    )

    class Meta:
        model = Category
        import_id_fields = ("slug",)
        fields = (
            "name",
            "slug",
            "description",
            "created_on",
            "updated_on",
        )
        export_order = (
            "name",
            "slug",
            "description",
            "created_on",
            "updated_on",
        )


class ProductExportResource(resources.ModelResource):
    name = fields.Field(column_name="Name of product", attribute="name")
    slug = fields.Field(column_name="Slug", attribute="slug")
    summary = fields.Field(column_name="Summary", attribute="summary")
    link = fields.Field(column_name="Action link", attribute="link")
    content = fields.Field(column_name="Content", attribute="content")
    costs = fields.Field(column_name="Costs", attribute="costs")
    created_on = fields.Field(
        column_name="Date of product creation", attribute="created_on"
    )
    updated_on = fields.Field(
        column_name="Date of product update", attribute="updated_on"
    )
    categories = fields.Field(
        column_name="Categories",
        attribute="categories",
        widget=ManyToManyWidget(Category, field="slug"),
    )
    organizations = fields.Field(
        column_name="Organizations",
        attribute="organizations",
        widget=ManyToManyWidget(Organization, field="name"),
    )
    related_products = fields.Field(
        column_name="Related products",
        attribute="related_products",
        widget=ManyToManyWidget(Product, field="slug"),
    )
    tags = fields.Field(
        column_name="Tags",
        attribute="tags",
        widget=ManyToManyWidget(Tag, field="name"),
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
