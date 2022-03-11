from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from import_export import fields, resources
from import_export.exceptions import ImportExportError
from import_export.instance_loaders import CachedInstanceLoader
from import_export.widgets import CharWidget

from ..models import Category, Organization, Product, Tag
from .widgets import ValidatedManyToManyWidget


class ImportResource(resources.ModelResource):
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        # Validate that file contains all the headers
        missing_headers = set(self.get_diff_headers()) - set(dataset.headers)
        if missing_headers:
            missing_headers = ",\n".join(missing_headers)
            raise ImportExportError(_(f"Missing required headers: {missing_headers}"))

        return super().before_import(dataset, using_transactions, dry_run, **kwargs)

    def get_or_init_instance(self, instance_loader, row):
        # Add slug field when a new row has to be created
        if not row.get("slug") and row.get("name"):
            row["slug"] = slugify(row["name"])

        # Replace newlines from excel
        for key, value in row.items():
            if isinstance(value, str):
                row[key] = value.replace("_x000D_", "\n")

        return super().get_or_init_instance(instance_loader, row)


class CategoryImportResource(ImportResource):
    name = fields.Field(column_name="name", attribute="name")
    slug = fields.Field(column_name="slug", attribute="slug")
    description = fields.Field(
        column_name="description", attribute="description", default=""
    )

    class Meta:
        model = Category
        instance_loader_class = CachedInstanceLoader
        clean_model_instances = True
        import_id_fields = ("slug",)
        fields = ("name", "slug", "description")

    def validate_instance(
        self, instance, import_validation_errors=None, validate_unique=True
    ):
        last_root = Category.get_last_root_node()
        if last_root:
            # Add the new root node as the last one
            newpath = last_root._inc_path()
        else:
            # Add the first root node
            newpath = Category._get_path(None, 1, 1)
        instance.depth = 1
        instance.path = newpath
        return super().validate_instance(
            instance,
            import_validation_errors=import_validation_errors,
            validate_unique=validate_unique,
        )


class ProductImportResource(ImportResource):
    name = fields.Field(column_name="name", attribute="name")
    slug = fields.Field(column_name="slug", attribute="slug")
    summary = fields.Field(column_name="summary", attribute="summary", default="")
    link = fields.Field(column_name="link", attribute="link", default="")
    content = fields.Field(column_name="content", attribute="content")
    categories = fields.Field(
        column_name="categories",
        attribute="categories",
        widget=ValidatedManyToManyWidget(Category, field="slug"),
    )
    organizations = fields.Field(
        column_name="organizations",
        attribute="organizations",
        widget=ValidatedManyToManyWidget(Organization, field="name"),
    )
    related_products = fields.Field(
        column_name="related_products",
        attribute="related_products",
        widget=ValidatedManyToManyWidget(Product, field="slug"),
    )
    tags = fields.Field(
        column_name="tags",
        attribute="tags",
        widget=ValidatedManyToManyWidget(Tag, field="name"),
    )
    costs = fields.Field(
        column_name="costs",
        attribute="costs",
        default=0,
        widget=CharWidget(),
    )

    class Meta:
        model = Product
        instance_loader_class = CachedInstanceLoader
        clean_model_instances = True
        import_id_fields = ("slug",)
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
            "organizations",
        )
