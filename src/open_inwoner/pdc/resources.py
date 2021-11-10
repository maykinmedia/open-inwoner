from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from import_export import fields, resources
from import_export.instance_loaders import CachedInstanceLoader
from import_export.widgets import ManyToManyWidget

from .models import Category, Organization, Product, Tag


class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category
        import_id_fields = ("slug",)


class CategoriesWidget(ManyToManyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        categories = super().clean(value, row=row, *args, **kwargs)
        if not categories and value != "":
            raise ValidationError(_("The category(ies) you entered do(es) not exist."))
        return super().clean(value, row=row, *args, **kwargs)


class OrganizationsWidget(ManyToManyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        organizations = super().clean(value, row=row, *args, **kwargs)
        if not organizations and value != "":
            raise ValidationError(
                _("The organization(s) you entered do(es) not exist.")
            )
        return super().clean(value, row=row, *args, **kwargs)


class RelatedProductsWidget(ManyToManyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        related_products = super().clean(value, row=row, *args, **kwargs)
        if not related_products and value != "":
            raise ValidationError(
                _("The related product(s) you entered do(es) not exist.")
            )
        return super().clean(value, row=row, *args, **kwargs)


class TagsWidget(ManyToManyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        tags = super().clean(value, row=row, *args, **kwargs)
        if not tags and value != "":
            raise ValidationError(_("The tag(s) you entered do(es) not exist."))
        return super().clean(value, row=row, *args, **kwargs)


class ProductResource(resources.ModelResource):
    categories = fields.Field(
        column_name=_("categories"),
        attribute="categories",
        widget=CategoriesWidget(Category, field="slug"),
    )
    organizations = fields.Field(
        column_name=_("organizations"),
        attribute="organizations",
        widget=OrganizationsWidget(Organization, field="name"),
    )
    related_products = fields.Field(
        column_name=_("related products"),
        attribute="related_products",
        widget=RelatedProductsWidget(Product, field="slug"),
    )
    tags = fields.Field(
        column_name=_("tags"),
        attribute="tags",
        widget=TagsWidget(Tag, field="name"),
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
