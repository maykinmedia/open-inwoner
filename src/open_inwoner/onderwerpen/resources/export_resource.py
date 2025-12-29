from import_export import fields, resources
from import_export.widgets import CharWidget, ManyToManyWidget

from open_inwoner.onderwerpen.models import Category, Organization, Product, Tag
from open_inwoner.onderwerpen.resources.widgets import ProsemirrorWidget


class CategoryExportResource(resources.ModelResource):
    description = fields.Field(
        column_name="description",
        attribute="description",
        widget=ProsemirrorWidget(),
    )

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
    content = fields.Field(
        column_name="content",
        attribute="content",
        widget=ProsemirrorWidget(),
    )
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
