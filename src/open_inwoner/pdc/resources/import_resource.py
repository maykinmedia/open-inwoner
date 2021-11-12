from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from import_export import fields, resources
from import_export.instance_loaders import CachedInstanceLoader
from import_export.widgets import ManyToManyWidget

from ..models import Category, Organization, Product, Tag


class CategoryImportResource(resources.ModelResource):
    class Meta:
        model = Category
        import_id_fields = ("slug",)


class ValidatedManyToManyWidget(ManyToManyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        if self.model.__name__ == "Category" and value == "":
            raise ValidationError("The field categories is required")

        qs = super().clean(value, row=row, *args, **kwargs)
        if not qs and value != "":
            raise ValidationError(
                _(f"The {self.model.__name__.lower()} you entered does not exist")
            )
        return qs


class ProductImportResource(resources.ModelResource):
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

    def get_or_init_instance(self, instance_loader, row):
        # Add slug field when a new row has to be created
        if not row.get("slug") and row.get("name"):
            row["slug"] = slugify(row["name"])
        return super().get_or_init_instance(instance_loader, row)
